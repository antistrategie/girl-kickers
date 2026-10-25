"""Ulrid's bow from the GFL2 CN client as gfl_ullrid_bow.khm, laid out like the placeholder it replaces.

Run:  uv run --with UnityPy==1.25.0 --with lz4 python tools/animations/ullrid_bow/build_ullrid_bow.py

Two stages in one file. Outside Blender it reads the bow and arrow out of the CN bundles, packs
both diffuse maps into one 1024x2048 sheet (bow on top, arrow below), writes the DDS, then reruns
itself in Blender, which builds the mesh in the Prop_R frame (origin at the drawn nock, +X towards
the target, Z up, grip D metres ahead) and exports the khm.

The string is drawn by moving the bowstring joint back, the way the game's skin would, so the limb
tips flex with it. The string itself is rebuilt as two thin rods: the original is a flat ribbon
that disappears when seen from above.
"""
import os, sys, json, struct, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))
SRC = os.path.join(ROOT, "ullrid_src")   # mesh.json + atlas.png, regenerated each run
OUT = os.path.join(REPO, "mod", "models", "signatures", "gfl_ullrid_bow")
D = 0.426        # string hand to bow grip along the aim axis, metres (the hand-made poses are built on it)
GRIP_Z = -0.03   # centre of the red grip pad along the bow's depth axis, measured off a side render

try:
    import bpy
except ImportError:
    bpy = None


# ------------------------------------------------------------ stage 1: extract (plain python)
def extract():
    sys.path.insert(0, os.path.expanduser("~/gfl2-extract/tools"))
    from gf2 import AB, load_bundle
    from UnityPy.helpers.MeshHelper import MeshHandler
    from PIL import Image

    def skinned(env, name):
        for o in env.objects:
            if o.type.name != "SkinnedMeshRenderer": continue
            r = o.read()
            if not r.m_Mesh.path_id: continue
            m = r.m_Mesh.read()
            if m.m_Name != name: continue
            h = MeshHandler(m); h.process()
            bones = [b.read().m_GameObject.read().m_Name for b in r.m_Bones]
            step = 2 if h.m_Use16BitIndices else 4
            tris = []
            for sm in m.m_SubMeshes:
                idx = h.m_IndexBuffer[sm.firstByte // step:sm.firstByte // step + sm.indexCount]
                tris += [list(idx[i:i + 3]) for i in range(0, len(idx), 3)]
            w_string = [sum(w for i, w in zip(bi, bw) if bones[i].startswith("bowstring"))
                        for bi, bw in zip(h.m_BoneIndices, h.m_BoneWeights)]
            return {"v": [list(v) for v in h.m_Vertices], "uv": [list(u)[:2] for u in h.m_UV0], "tris": tris, "w_string": w_string}
        raise SystemExit(f"{name} not found")

    def texture(bundle, name):
        for o in load_bundle(f"{AB}/{bundle}.bundle").objects:
            if o.type.name == "Texture2D":
                t = o.read()
                if t.m_Name == name: return t.image.convert("RGBA")
        raise SystemExit(f"{name} not found")

    env = load_bundle(f"{AB}/deee59297d7e33c33b485f9cac165fcd.bundle")
    bow, arrow = skinned(env, "c_UllridSSR01_slg_weapon"), skinned(env, "c_UllridSSR01_slg_Bolt")

    # the string is the one piece of the bow with vertices driven by the bowstring joints alone
    parent = list(range(len(bow["v"])))
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for t in bow["tris"]:
        for k in t[1:]: parent[find(k)] = find(t[0])
    string_roots = {find(i) for i, w in enumerate(bow["w_string"]) if w > 0.99}
    bow["string"] = [find(i) in string_roots for i in range(len(bow["v"]))]

    os.makedirs(SRC, exist_ok=True)
    json.dump({"bow": bow, "arrow": arrow}, open(os.path.join(SRC, "mesh.json"), "w"))

    atlas = Image.new("RGBA", (1024, 2048))
    atlas.paste(texture("d89cce20fb0f389487ea9a66438bf90e", "c_UllridSSR01_slg_weapon_d").resize((1024, 1024), Image.LANCZOS), (0, 0))
    atlas.paste(texture("4794882690dcd6886986803f9424eb06", "c_UllridSSR01_slg_Bolt_d").resize((1024, 1024), Image.LANCZOS), (0, 1024))
    atlas.save(os.path.join(SRC, "atlas.png"))
    # uncompressed 32-bit BGRA, one mip, same header layout as the other signature weapons
    w, h = atlas.size
    with open(OUT + ".dds", "wb") as f:
        f.write(struct.pack("<4s7I44x8I5I", b"DDS ", 124, 0x100F, h, w, w * 4, 0, 1,
                            32, 0x41, 0, 32, 0xFF0000, 0xFF00, 0xFF, 0xFF000000, 0x1000, 0, 0, 0, 0))
        f.write(atlas.tobytes("raw", "BGRA"))
    print("== wrote", OUT + ".dds", "| string verts", sum(bow["string"]))
    subprocess.run(["blender", "--background", "--python-exit-code", "1", "--python", os.path.abspath(__file__)], check=True)


# ------------------------------------------------------------ stage 2: build and export (blender)
def build():
    import math, addon_utils
    from mathutils import Vector
    if "khm" not in dir(bpy.ops.export_scene): addon_utils.enable("khm_tools")
    from khm_tools import import_khm

    data = json.load(open(os.path.join(SRC, "mesh.json")))
    bow, arrow = data["bow"], data["arrow"]
    AV, BV = arrow["v"], bow["v"]
    ARROW_X = sum(v[0] for v in AV) / len(AV); ARROW_Y = sum(v[1] for v in AV) / len(AV)
    NOCK_Z = GRIP_Z - D   # where the string hand holds the nock, in the bow's own coordinates
    rest = [BV[i][2] for i, w in enumerate(bow["w_string"]) if w > 0.99]
    PULL = sum(rest) / len(rest) - NOCK_Z
    ARROW_BACK = min(v[2] for v in AV) - NOCK_Z

    def local(x, y, z):
        # Unity is left handed (x right, y up, z forward); Prop_R is X forward, Y left, Z up
        return (z - NOCK_Z, -(x - ARROW_X), y - ARROW_Y)

    keep = [i for i in range(len(BV)) if not bow["string"][i]]
    remap = {i: n for n, i in enumerate(keep)}
    verts = [local(BV[i][0], BV[i][1], BV[i][2] - PULL * bow["w_string"][i]) for i in keep]
    uvs = [(bow["uv"][i][0], 0.5 + 0.5 * bow["uv"][i][1]) for i in keep]
    faces = [(remap[t[0]], remap[t[2]], remap[t[1]]) for t in bow["tris"] if t[0] in remap]   # mirrored, so flip the winding
    off = len(verts)
    verts += [local(x, y, z - ARROW_BACK) for x, y, z in AV]
    uvs += [(u, 0.5 * v) for u, v in arrow["uv"]]
    faces += [(off + t[0], off + t[2], off + t[1]) for t in arrow["tris"]]

    bpy.ops.wm.read_homefile(use_empty=True)
    me = bpy.data.meshes.new("gfl_ullrid_bow"); me.from_pydata(verts, [], faces); me.validate()
    uvl = me.uv_layers.new(name="UVMap")
    for loop in me.loops: uvl.data[loop.index].uv = uvs[loop.vertex_index]
    bow_obj = bpy.data.objects.new("gfl_ullrid_bow", me); bpy.context.collection.objects.link(bow_obj)

    # drawn string: two rods from the (flexed) limb tips to the nock
    s = [i for i in range(len(BV)) if bow["string"][i]]
    string_uv = (sum(bow["uv"][i][0] for i in s) / len(s), 0.5 + 0.5 * sum(bow["uv"][i][1] for i in s) / len(s))
    parts = [bow_obj]
    for i in (min(s, key=lambda i: BV[i][1]), max(s, key=lambda i: BV[i][1])):
        tip = Vector(local(BV[i][0], BV[i][1], BV[i][2] - PULL * bow["w_string"][i])); v = -tip
        bpy.ops.mesh.primitive_cylinder_add(radius=0.002, depth=v.length, vertices=6, location=tip + v / 2)
        rod = bpy.context.active_object; rod.rotation_euler = v.to_track_quat("Z", "Y").to_euler()
        for d in rod.data.uv_layers.active.data: d.uv = string_uv
        parts.append(rod)
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = bow_obj; bpy.ops.object.join()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    tip_x = max(v[0] for v in verts[off:])
    for name, pos, euler in (("muzzle", (tip_x, 0, 0), (0, 0, -90)), ("silencer_socket", (tip_x, 0, 0), (0, 0, -90)),
                             ("optics_socket", (D - 0.05, 0, 0.12), (0, 0, -90)), ("IKHandL", (D - 0.02, 0, 0), (-180, 0, 0))):
        e = bpy.data.objects.new("HELPER_" + name, None); bpy.context.collection.objects.link(e); e.parent = bow_obj
        e.location = pos; e.rotation_euler = [math.radians(a) for a in euler]
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(D / 2, 0, 0)); col = bpy.context.active_object
    col.name = "COL_SPHERE"; col.parent = bow_obj; col.scale = (0.06, 0.06, 0.06)
    bpy.context.view_layer.update()

    bpy.ops.object.select_all(action="DESELECT"); bow_obj.select_set(True); bpy.context.view_layer.objects.active = bow_obj
    bpy.ops.export_scene.khm(filepath=OUT + ".khm", export_mesh=True, export_animation=False, export_animation_mask=False)
    bm = import_khm.LoadModel(OUT + ".khm")
    print("== wrote", OUT + ".khm", "| pull", round(PULL, 3), "| arrow tip", round(tip_x, 3), "| verts", bm.pMesh.numVertices,
          "| helpers", [(h.szName, [round(c, 2) for c in h.matGlobal.to_translation()]) for h in bm.lHelpers])


if bpy is None: extract()
else: build()
