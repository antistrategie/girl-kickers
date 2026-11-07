"""Build signature weapons from the GFL2 CN client: mod/models/signatures/<name>.khm and .dds.

Run:
    uv run --no-project --with UnityPy==1.25.0 --with lz4 --with numpy --with pillow \\
        python tools/weapons/build_weapon.py [name ...] [--rebuild]

Rows live in weapons.py. With no names, every row is built.

Two stages in one file, like tools/animations/ullrid_bow/build_ullrid_bow.py. Outside Blender
it reads the weapon mesh, its socket nodes and its diffuse map out of the client (paths from
GFL2_BUNDLES and GFL2_ASSET_MAP, in the environment or the repo's .env), writes the DDS and
src/<name>/mesh.json, then reruns itself in Blender.

In Blender, the first run builds tools/weapons/<name>.blend:

- the weapon mesh at the world origin, in the frame the game hangs it from. A gun sits in
  Prop_R's frame (origin at the right hand's grip, +X towards the target, Z up). A blade sits
  in Hare's frame (handle at the origin, blade along +X, lying flat).
- a gun's helpers, as children of the mesh: muzzle, silencer_socket and optics_socket from
  the GFL2 sockets (lgp_muzzle, Silencer01_Node, Sight_Node), underbarrel from Stool_Node,
  and IKHandL on the underside of the handguard ik_x ahead of the grip.
- for a gun, the doll who carries it (mod/models/dolls/<name>.khm), posed in the game's
  rifle aim clip and moved so her Prop_R sits on the world origin. She is only there to show
  where the hands land and is never exported.

Nudge in that .blend: move IKHandL onto the handguard where her left hand should close, or
move the weapon mesh itself to change where it sits in the right hand (its helpers follow,
so move them back if they should stay put). Save, then rerun the script. While a .blend
exists the script exports from it, so nudges are kept. --rebuild starts over from weapons.py.

Every run also renders tools/weapons/preview/<name>.png (gitignored) for a quick look.
--renders <dir> also writes <dir>/<name>.png: the weapon alone, side on with the muzzle to the
right, orthographic on a transparent background, as a base to draw the <name>_ui.dds icon over.
"""

import json
import os
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(ROOT, "..", ".."))
SRC = os.path.join(ROOT, "src")
PREVIEW = os.path.join(ROOT, "preview")
SIGNATURES = os.path.join(REPO, "mod", "models", "signatures")
DOLLS = os.path.join(REPO, "mod", "models", "dolls")
RIFLE_AIM = os.path.join(
    REPO, "tools", "animations", "ullrid_bow", "rifle_clips", "idle_aim.khm"
)
sys.path.insert(0, ROOT)
from weapons import WEAPONS

TEXTURE_SIZE = 1024
# IKHandL sits this far below the handguard's underside, as on the roster's guns.
IK_BELOW = 0.005
# Half widths of the slice through the handguard that finds its underside.
IK_SLICE = (0.015, 0.04)
# Gaps in that slice wider than this separate the handguard from a magazine below it.
IK_GAP = 0.01
# Side renders for drawing icons over: about four times the roster icons' 540 px per metre.
RENDER_PX_PER_M = 2160

try:
    import bpy
except ImportError:
    bpy = None


# ------------------------------------------------------------ stage 1: extract (plain python)
def extract(names):
    import ntpath

    import numpy as np
    from PIL import Image

    sys.path.insert(0, os.path.join(REPO, "scripts", "sprites"))
    from extract_art import decrypt, load_dotenv

    load_dotenv()
    bundles, asset_map = (
        os.environ.get("GFL2_BUNDLES"),
        os.environ.get("GFL2_ASSET_MAP"),
    )
    if not bundles or not asset_map:
        raise SystemExit(
            "set GFL2_BUNDLES and GFL2_ASSET_MAP (see scripts/sprites/extract_art.py)"
        )
    import UnityPy
    from UnityPy.helpers.MeshHelper import MeshHandler

    with open(asset_map) as fh:
        entries = json.load(fh)
    source = {
        e["Name"]: ntpath.basename(e["Source"])
        for e in entries
        if e.get("Type") == "Texture2D"
    }

    def quat(q):
        x, y, z, w = q.x, q.y, q.z, q.w
        return np.array(
            [
                [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
            ]
        )

    for name in names:
        g = WEAPONS[name]["gfl2"]
        tex_name = f"cw_{g}_WL_d"
        if tex_name not in source:
            raise SystemExit(f"{name}: {tex_name} is not in the asset map")
        # The weapon's mesh, prefab and diffuse all sit in the bundle that holds the diffuse.
        env = UnityPy.Environment()
        with open(os.path.join(bundles, source[tex_name]), "rb") as f:
            env.load_file(decrypt(f.read()), name=source[tex_name])

        transforms = {
            o.path_id: o.read() for o in env.objects if o.type.name == "Transform"
        }

        def world(t, transforms=transforms):
            m = np.eye(4)
            while True:
                local = np.eye(4)
                s = t.m_LocalScale
                local[:3, :3] = quat(t.m_LocalRotation) * [s.x, s.y, s.z]
                p = t.m_LocalPosition
                local[:3, 3] = [p.x, p.y, p.z]
                m = local @ m
                if t.m_Father.path_id not in transforms:
                    return m
                t = transforms[t.m_Father.path_id]

        # Only the sockets under this weapon's own skin root, not its parts' prefabs.
        nodes = {}
        for t in transforms.values():
            root = t
            while root.m_Father.path_id in transforms:
                root = transforms[root.m_Father.path_id]
            if root.m_GameObject.read().m_Name == f"cw_{g}_WL_skin":
                nodes[t.m_GameObject.read().m_Name] = world(t)[:3, 3].tolist()

        mesh, image = None, None
        for o in env.objects:
            kind = o.type.name
            if kind == "Texture2D":
                t = o.read()
                if t.m_Name == tex_name:
                    image = t.image.convert("RGBA")
            elif kind in ("SkinnedMeshRenderer", "MeshFilter"):
                r = o.read()
                if not r.m_Mesh.path_id:
                    continue
                m = r.m_Mesh.read()
                if m.m_Name != f"cw_{g}_WL_lod0":
                    continue
                h = MeshHandler(m)
                h.process()
                step = 2 if h.m_Use16BitIndices else 4
                tris = []
                for sm in m.m_SubMeshes:
                    idx = h.m_IndexBuffer[
                        sm.firstByte // step : sm.firstByte // step + sm.indexCount
                    ]
                    tris += [list(idx[i : i + 3]) for i in range(0, len(idx), 3)]
                mesh = {
                    "v": [list(v) for v in h.m_Vertices],
                    "uv": [list(u)[:2] for u in h.m_UV0],
                    "tris": tris,
                }
        if mesh is None or image is None:
            raise SystemExit(
                f"{name}: cw_{g}_WL_lod0 or its diffuse missing from {source[tex_name]}"
            )

        out = os.path.join(SRC, name)
        os.makedirs(out, exist_ok=True)
        mesh["nodes"] = nodes
        with open(os.path.join(out, "mesh.json"), "w") as fh:
            json.dump(mesh, fh)
        if image.size != (TEXTURE_SIZE, TEXTURE_SIZE):
            image = image.resize((TEXTURE_SIZE, TEXTURE_SIZE), Image.LANCZOS)
        image.save(os.path.join(out, "diffuse.png"))
        # Uncompressed 32-bit BGRA, one mip, the layout of the other signature weapons.
        w, h = image.size
        with open(os.path.join(SIGNATURES, name + ".dds"), "wb") as f:
            f.write(
                struct.pack(
                    "<4s7I44x8I5I",
                    b"DDS ",
                    124,
                    0x100F,
                    h,
                    w,
                    w * 4,
                    0,
                    1,
                    32,
                    0x41,
                    0,
                    32,
                    0xFF0000,
                    0xFF00,
                    0xFF,
                    0xFF000000,
                    0x1000,
                    0,
                    0,
                    0,
                    0,
                )
            )
            f.write(image.tobytes("raw", "BGRA"))
        print(f"== {name}: {len(mesh['v'])} verts, sockets {sorted(nodes)}")
        print(
            f"== wrote {os.path.relpath(os.path.join(SIGNATURES, name + '.dds'), REPO)}"
        )


# ------------------------------------------------------------ stage 2: build and export (blender)
def blender_main(names, rebuild, renders):
    import addon_utils

    if "khm" not in dir(bpy.ops.export_scene):
        addon_utils.enable("khm_tools")
    os.makedirs(PREVIEW, exist_ok=True)
    for name in names:
        blend = os.path.join(ROOT, name + ".blend")
        if rebuild or not os.path.exists(blend):
            build(name)
            bpy.ops.wm.save_as_mainfile(filepath=blend)
            print(f"== built {os.path.relpath(blend, REPO)}")
        else:
            bpy.ops.wm.open_mainfile(filepath=blend)
            print(
                f"== exporting from {os.path.relpath(blend, REPO)} (pass --rebuild to start over)"
            )
        export(name)
        preview(name)
        if renders:
            side_render(name, renders)


def to_frame(row):
    """Unity weapon coordinates to the game's: Unity is left handed (x forward, y up, z left
    of the barrel here), the game right handed with Z up, so y and z swap and windings flip."""
    from mathutils import Matrix, Vector

    ox, oy = row.get("origin", (0.0, 0.0))
    roll = Matrix.Rotation(__import__("math").radians(row.get("roll", 0)), 3, "X")

    def f(p):
        x, y, z = p
        return roll @ Vector((x - ox, z, y - oy))

    return f


def build(name):
    import math

    row = WEAPONS[name]
    with open(os.path.join(SRC, name, "mesh.json")) as fh:
        src = json.load(fh)
    f = to_frame(row)

    bpy.ops.wm.read_homefile(use_empty=True)
    verts = [f(v) for v in src["v"]]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [(a, c, b) for a, b, c in src["tris"]])
    me.validate()
    uvl = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        uvl.data[loop.index].uv = src["uv"][loop.vertex_index]
    gun = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(gun)

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(SRC, name, "diffuse.png"))
    mat.node_tree.links.new(
        tex.outputs["Color"],
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"],
    )
    me.materials.append(mat)

    def helper(hname, pos, euler):
        e = bpy.data.objects.new("HELPER_" + hname, None)
        bpy.context.collection.objects.link(e)
        e.parent = gun
        e.location = pos
        e.rotation_euler = [math.radians(a) for a in euler]
        e.empty_display_type = "ARROWS"
        e.empty_display_size = 0.05

    xs = [v.x for v in verts]
    if row["kind"] == "gun":
        nodes = src["nodes"]
        muzzle = f(nodes["lgp_muzzle"])
        for hname, node in (
            ("muzzle", "lgp_muzzle"),
            ("silencer_socket", "Silencer01_Node"),
            ("optics_socket", "Sight_Node"),
            ("underbarrel", "Stool_Node"),
        ):
            if node in nodes:
                p = f(nodes[node])
                helper(hname, (p.x, 0, p.z), (0, 0, -90))
        ik_x = row.get("ik_x", 0.27)
        helper(
            "IKHandL",
            (ik_x, 0, handguard_underside(verts, ik_x, muzzle.z) - IK_BELOW),
            (90, 0, 0),
        )
    # One collision volume, as on Hare and the roster's guns.
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=1, location=((min(xs) + max(xs)) / 2, 0, 0)
    )
    col = bpy.context.active_object
    col.name = "COL_SPHERE"
    col.parent = gun
    col.scale = (0.06, 0.06, 0.06)

    if row["kind"] == "gun":
        add_reference_doll(name)
    bpy.context.view_layer.update()


def handguard_underside(verts, x, bore_z):
    """Lowest point of the solid band around the bore in a thin slice at x. Walking down from
    the bore, a gap wider than IK_GAP is where the handguard ends and a magazine begins."""
    dx, dy = IK_SLICE
    zs = sorted(
        (v.z for v in verts if abs(v.x - x) < dx and abs(v.y) < dy), reverse=True
    )
    if not zs:
        raise SystemExit(
            f"no geometry {x:.2f} m ahead of the grip for IKHandL, set ik_x in weapons.py"
        )
    below = [z for z in zs if z <= bore_z] or zs
    lowest = below[0]
    for z in below[1:]:
        if lowest - z > IK_GAP:
            break
        lowest = z
    return lowest


def add_reference_doll(name):
    """The doll in the game's rifle aim pose, moved so her Prop_R is the world origin."""
    from khm_tools import import_khm

    path = os.path.join(DOLLS, name + ".khm")
    if not os.path.exists(path):
        print(
            f"== {name}: no doll model at {os.path.relpath(path, REPO)}, skipping the reference doll"
        )
        return
    before = set(bpy.data.objects)
    import_khm.load(None, bpy.context, path)
    doll = [o for o in set(bpy.data.objects) - before]
    arm = next(o for o in doll if o.type == "ARMATURE")
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    deselect_all()
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    import_khm.load(None, bpy.context, RIFLE_AIM)
    bpy.context.scene.frame_set(bpy.context.scene.frame_start)
    bpy.context.view_layer.update()
    prop_r = arm.matrix_world @ arm.pose.bones["HELPER_Prop_R"].matrix
    arm.matrix_world = prop_r.inverted() @ arm.matrix_world

    coll = bpy.data.collections.new("reference_doll (not exported)")
    bpy.context.scene.collection.children.link(coll)
    for o in doll:
        for c in o.users_collection:
            c.objects.unlink(o)
        coll.objects.link(o)
        o.hide_select = o.type != "ARMATURE"
    deselect_all()


def deselect_all():
    for o in bpy.context.view_layer.objects:
        o.select_set(False)


def export(name):
    from mathutils import Matrix

    gun = bpy.data.objects[name]
    # A nudged mesh object is baked into its vertices, children kept where they are.
    if gun.matrix_world != Matrix.Identity(4):
        kept = {c: c.matrix_world.copy() for c in gun.children}
        gun.data.transform(gun.matrix_world)
        gun.matrix_world = Matrix.Identity(4)
        bpy.context.view_layer.update()
        for c, m in kept.items():
            c.matrix_world = m
        bpy.context.view_layer.update()
    deselect_all()
    gun.hide_set(False)
    gun.select_set(True)
    bpy.context.view_layer.objects.active = gun
    out = os.path.join(SIGNATURES, name + ".khm")
    bpy.ops.export_scene.khm(
        filepath=out,
        export_mesh=True,
        export_animation=False,
        export_animation_mask=False,
    )
    from khm_tools import import_khm

    bm = import_khm.LoadModel(out)
    helpers = [
        (h.szName, [round(c, 3) for c in h.matGlobal.to_translation()])
        for h in (bm.lHelpers or [])
    ]
    print(
        f"== wrote {os.path.relpath(out, REPO)} | verts {bm.pMesh.numVertices} | helpers {helpers}"
    )


def preview(name):
    """Side, top and three-quarter views, textured, with the reference doll when there is one."""
    from mathutils import Vector

    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "TEXTURE"
    sc.render.resolution_x, sc.render.resolution_y = 640, 480
    sc.render.film_transparent = False
    for o in bpy.data.objects:
        if o.name.startswith("COL_"):
            o.hide_render = True
    cam = bpy.data.objects.new("preview_cam", bpy.data.cameras.new("preview_cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    doll = any(c.name.startswith("reference_doll") for c in bpy.data.collections)
    shots = (
        ("side", (0.15, -1.1, 0.05), (0.15, 0, 0.0)),
        ("top", (0.15, 0, 1.1), (0.15, 0, 0)),
        ("quarter", (1.0, -0.9, 0.5), (0.0, 0.15, 0.0)),
    )
    files = []
    for view, pos, target in shots:
        if not doll and view == "quarter":
            continue
        cam.location = pos
        cam.rotation_euler = (
            (Vector(target) - Vector(pos))
            .to_track_quat("-Z", "Y" if view != "top" else "X")
            .to_euler()
        )
        cam.data.lens = 35
        path = os.path.join(PREVIEW, f"{name}_{view}.png")
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        files.append(path)
    out = os.path.join(PREVIEW, f"{name}.png")
    subprocess.run(["magick", *files, "+append", out], check=True)
    for p in files:
        os.remove(p)
    bpy.data.objects.remove(cam)
    print(f"== preview {os.path.relpath(out, REPO)}")


def side_render(name, outdir):
    """The weapon alone, side on, muzzle right, orthographic, transparent background."""
    sc = bpy.context.scene
    gun = bpy.data.objects[name]
    shown = {o: o.hide_render for o in bpy.data.objects}
    for o in bpy.data.objects:
        o.hide_render = o != gun
    # A blade lies flat in XY, so it is drawn from above. A gun is drawn from its right side.
    blade = WEAPONS[name]["kind"] == "blade"
    xs = [v.co.x for v in gun.data.vertices]
    us = [v.co.y if blade else v.co.z for v in gun.data.vertices]
    margin = 0.02
    w, h = max(xs) - min(xs) + 2 * margin, max(us) - min(us) + 2 * margin
    cam = bpy.data.objects.new("side_cam", bpy.data.cameras.new("side_cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(w, h)
    mid_x, mid_u = (min(xs) + max(xs)) / 2, (min(us) + max(us)) / 2
    if blade:
        cam.location = (mid_x, mid_u, 2.0)
        cam.rotation_euler = (0, 0, 0)
    else:
        cam.location = (mid_x, -2.0, mid_u)
        cam.rotation_euler = (__import__("math").radians(90), 0, 0)
    sc.render.resolution_x, sc.render.resolution_y = (
        round(w * RENDER_PX_PER_M),
        round(h * RENDER_PX_PER_M),
    )
    sc.render.film_transparent = True
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "TEXTURE"
    os.makedirs(outdir, exist_ok=True)
    sc.render.filepath = os.path.join(outdir, name + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
    for o, hidden in shown.items():
        o.hide_render = hidden
    print(f"== render {sc.render.filepath}")


def parse(argv):
    rebuild = "--rebuild" in argv
    renders = None
    if "--renders" in argv:
        i = argv.index("--renders")
        renders = os.path.abspath(os.path.expanduser(argv[i + 1]))
        argv = argv[:i] + argv[i + 2 :]
    names = [a for a in argv if not a.startswith("--")] or list(WEAPONS)
    unknown = [n for n in names if n not in WEAPONS]
    if unknown:
        raise SystemExit(f"not in weapons.py: {', '.join(unknown)}")
    return names, rebuild, renders


if bpy is None:
    names, rebuild, renders = parse(sys.argv[1:])
    extract(names)
    subprocess.run(
        [
            "blender",
            "--background",
            "--python-exit-code",
            "1",
            "--python",
            os.path.abspath(__file__),
            "--",
            *names,
            *(["--rebuild"] if rebuild else []),
            *(["--renders", renders] if renders else []),
        ],
        check=True,
    )
else:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    blender_main(*parse(argv))
