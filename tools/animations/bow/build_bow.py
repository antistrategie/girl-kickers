"""Bow animations for the DK2 human rig, plus a placeholder bow weapon model.

Run headless:  blender --background --python tools/animations/bow/build_bow.py

Builds on the game's own rifle clips (legs, spine, breathing) and re-poses the upper body
around a drawn bow with a small CCD solver. The bow model is authored relative to the
string hand (Prop_R): origin at the drawn string, +X towards the target, grip D metres ahead.
"""
import bpy, os, math
from mathutils import Vector, Matrix, Quaternion

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))
DK = os.path.expanduser("~/.local/share/Steam/steamapps/common/DoorKickers2/data")
CLIPS_IN = os.path.join(ROOT, "rifle_clips")   # extracted from data_store.zip by the runner
OUT_ANIMS = os.path.join(REPO, "mod", "animations", "khm", "bow")
OUT_MODELS = os.path.join(REPO, "mod", "models", "signatures")
os.makedirs(OUT_ANIMS, exist_ok=True); os.makedirs(OUT_MODELS, exist_ok=True)

import zipfile
if not os.path.isdir(CLIPS_IN):
    with zipfile.ZipFile(f"{DK}/animations/khm/data_store.zip") as z:
        for n in ("idle_aim", "idle_low", "fire_aim", "reload_aim", "lower_weapon"):
            z.extract(f"rifle/{n}.khm", ROOT)
    os.rename(os.path.join(ROOT, "rifle"), CLIPS_IN)

import addon_utils
if "khm" not in dir(bpy.ops.export_scene): addon_utils.enable("khm_tools")
from khm_tools import import_khm
imp = getattr(bpy.ops.khm, "import")

FWD, UP = Vector((0, -1, 0)), Vector((0, 0, 1))
R_ARM = ("Bip001 R UpperArm", "Bip001 R Forearm", "Bip001 R Hand")
L_ARM = ("Bip001 L UpperArm", "Bip001 L Forearm", "Bip001 L Hand")
UPPER = ["Bip001 Spine1", "Bip001 Neck", "Bip001 Head", "Bip001 L Clavicle", "Bip001 R Clavicle", *R_ARM, *L_ARM]
PROP_R_LOCAL = None   # filled from the model


def log(*a): print("==", *a)
def objmode():
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
def select_only(o):
    objmode(); bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
def upd(): bpy.context.view_layer.update()
def smooth(u): return u * u * (3 - 2 * u)


# ------------------------------------------------------------------ rig
bpy.ops.wm.read_homefile(use_empty=True)
imp(filepath=f"{DK}/models/humans/ranger_assaulter.khm")
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
md = import_khm.LoadModel(f"{DK}/models/humans/ranger_assaulter.khm")
PROP_R_LOCAL = [h for h in md.lHelpers if h.szName == "Prop_R"][0].matLocal
PB = arm.pose.bones
for pb in PB: pb.rotation_mode = "QUATERNION"


def head(name): return PB[name].matrix.to_translation()
def prop_r_world(): return PB["Bip001 R Hand"].matrix @ PROP_R_LOCAL


def rotate_about_head(name, R3):
    """apply an armature-space rotation to a bone about its own head, children follow"""
    pb = PB[name]; h = pb.matrix.to_translation()
    pb.matrix = Matrix.Translation(h) @ R3.to_4x4() @ Matrix.Translation(-h) @ pb.matrix
    upd()


def aim_bone(name, tip_name, target, fraction=1.0):
    h = head(name); a = head(tip_name) - h; b = target - h
    if a.length < 1e-6 or b.length < 1e-6: return
    q = a.rotation_difference(b)
    if fraction != 1.0: q = Quaternion((1, 0, 0, 0)).slerp(q, fraction)
    rotate_about_head(name, q.to_matrix())


def solve_arm(chain, wrist_target, elbow_dir, hand_x, hand_z=UP, iters=14):
    upper, fore, hand = chain
    for i in range(iters):
        aim_bone(fore, hand, wrist_target)
        aim_bone(upper, hand, wrist_target, 0.6)
    # swivel the elbow about the shoulder-wrist line towards elbow_dir, wrist stays put
    s, w, e = head(upper), head(hand), head(fore); axis = (w - s).normalized()
    cur = (e - s) - (e - s).dot(axis) * axis; want = elbow_dir - elbow_dir.dot(axis) * axis
    if cur.length > 1e-4 and want.length > 1e-4:
        ang = cur.angle(want); sign = 1 if cur.cross(want).dot(axis) > 0 else -1
        rotate_about_head(upper, Matrix.Rotation(sign * ang, 3, axis))
    # hand orientation: X along hand_x, Z as close to hand_z as possible
    x = hand_x.normalized(); z = (hand_z - hand_z.dot(x) * x).normalized(); y = z.cross(x)
    R = Matrix((x, y, z)).transposed()
    pb = PB[hand]; pb.matrix = Matrix.LocRotScale(pb.matrix.to_translation(), R.to_quaternion(), None); upd()


def key_upper(frame):
    for n in UPPER:
        PB[n].keyframe_insert("rotation_quaternion", frame=frame); PB[n].keyframe_insert("location", frame=frame)


def load_base(clip):
    """the game's rifle clip supplies legs, spine and breathing; returns its frame count"""
    arm.animation_data_clear()
    for pb in PB: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    select_only(arm); imp(filepath=f"{CLIPS_IN}/{clip}.khm")
    return bpy.context.scene.frame_end + 1


# -------------------------------------------------------------- poses
# the string hand sits at the anchor (jaw), the bow grip is D metres ahead of Prop_R
ANCHOR = Vector((-0.06, -0.15, 1.57))
LOW_WRIST = Vector((-0.12, -0.26, 1.08)); LOW_DIR = Vector((0, -0.6, -0.8)).normalized()
NOCK = Vector((-0.06, -0.34, 1.30))
TORSO_YAW = math.radians(-50)
D = None   # draw length, chosen from the rig's reach below


def pose_upper(frame, wrist_r, dir_r, yaw, torso_from_base=True):
    """re-pose the upper body around the bow at this frame (base clip already evaluated)"""
    if yaw:
        rotate_about_head("Bip001 Spine1", Matrix.Rotation(yaw, 3, "Z"))
        rotate_about_head("Bip001 Head", Matrix.Rotation(-yaw, 3, "Z"))
    solve_arm(R_ARM, wrist_r, Vector((-0.6, 0.4, 0.7)), dir_r)
    grip = prop_r_world().to_translation() + dir_r * D
    solve_arm(L_ARM, grip - dir_r * 0.08, Vector((0.35, -0.1, -0.9)), dir_r)
    key_upper(frame)


def choose_draw_length():
    global D
    bpy.context.scene.frame_set(0)
    rotate_about_head("Bip001 Spine1", Matrix.Rotation(TORSO_YAW, 3, "Z"))
    solve_arm(R_ARM, ANCHOR, Vector((-0.6, 0.4, 0.7)), FWD)
    pr = prop_r_world().to_translation(); s = head("Bip001 L UpperArm")
    reach = (head("Bip001 L Forearm") - s).length + (head("Bip001 L Hand") - head("Bip001 L Forearm")).length
    # grip must be within 92% of reach from the left shoulder, measured to the wrist (8 cm short of the grip)
    lo, hi = 0.30, 0.80
    for _ in range(30):
        mid = (lo + hi) / 2; wrist = pr + FWD * mid - FWD * 0.08
        if (wrist - s).length < 0.92 * reach: lo = mid
        else: hi = mid
    D = round(min(lo, 0.60), 3)
    log("left arm reach", round(reach, 3), "m | draw length D", D, "m | Prop_R at anchor", [round(v, 3) for v in pr])


def build(name, base, nframes, pose_fn):
    n_base = load_base(base)
    N = nframes or n_base
    sc = bpy.context.scene; sc.frame_start = 0; sc.frame_end = N - 1; sc.render.fps = 30
    for f in range(N):
        sc.frame_set(min(f, n_base - 1)); upd()
        pose_fn(f, f / max(N - 1, 1))
    for f in range(N):   # legs and spine from the base clip on every frame, so the clip is self-contained
        sc.frame_set(min(f, n_base - 1))
        for pb in PB:
            if pb.name not in UPPER and not pb.name.startswith("HELPER_"):
                pb.keyframe_insert("rotation_quaternion", frame=f); pb.keyframe_insert("location", frame=f)
    sc.frame_end = N - 1
    select_only(arm)
    path = f"{OUT_ANIMS}/{name}.khm"
    bpy.ops.export_scene.khm(filepath=path, export_mesh=False, export_animation=True, export_animation_mask=False)
    a = import_khm.LoadModel(path).pAnimation
    log("clip", name, "base", base, "frames", a.numNodeFrames, "nodes", a.numNodes, round(a.endTimeS, 2), "s")
    return N


choose_draw_length()

def aim(f, u):
    pose_upper(f, ANCHOR, FWD, TORSO_YAW)
def low(f, u):
    pose_upper(f, LOW_WRIST, LOW_DIR, 0.0)
def fire(f, u):
    k = math.sin(math.pi * min(u * 3, 1)) if u < 1 / 3 else 0.0   # snap back and settle in the first third
    pose_upper(f, ANCHOR + Vector((0, 0.05, 0.02)) * k, FWD, TORSO_YAW)
def reload(f, u):
    if u < 0.3: t = smooth(u / 0.3); w = ANCHOR.lerp(NOCK, t)
    elif u < 0.5: w = NOCK
    elif u < 0.9: t = smooth((u - 0.5) / 0.4); w = NOCK.lerp(ANCHOR, t)
    else: w = ANCHOR
    pose_upper(f, w, FWD, TORSO_YAW)
def lower(f, u):
    t = smooth(u)
    pose_upper(f, ANCHOR.lerp(LOW_WRIST, t), FWD.lerp(LOW_DIR, t).normalized(), TORSO_YAW * (1 - t))

FRAMES = {}
FRAMES["bow_idle_aim"] = build("bow_idle_aim", "idle_aim", None, aim)
FRAMES["bow_idle_low"] = build("bow_idle_low", "idle_low", None, low)
FRAMES["bow_fire"] = build("bow_fire", "fire_aim", 12, fire)
FRAMES["bow_reload"] = build("bow_reload", "reload_aim", 40, reload)
FRAMES["bow_lower"] = build("bow_lower", "lower_weapon", None, lower)
log("reload ms", round(FRAMES["bow_reload"] / 30 * 1000))

# ------------------------------------------- placeholder bow: authored relative to the string hand
def build_bow_mesh():
    parts = []
    cu = bpy.data.curves.new("stave", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.012; cu.bevel_resolution = 3
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(2)
    for pt, co in zip(sp.bezier_points, ((D - 0.10, 0, -0.55), (D + 0.03, 0, 0), (D - 0.10, 0, 0.55))):
        pt.co = co; pt.handle_left_type = pt.handle_right_type = "AUTO"
    stave = bpy.data.objects.new("stave", cu); bpy.context.collection.objects.link(stave); select_only(stave)
    bpy.ops.object.convert(target="MESH"); parts.append(stave)
    def rod(a, b, r):
        a, b = Vector(a), Vector(b); v = b - a
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=v.length, vertices=8, location=(a + b) / 2)
        o = bpy.context.active_object; o.rotation_euler = v.to_track_quat("Z", "Y").to_euler(); parts.append(o)
    rod((D - 0.10, 0, -0.55), (0, 0, 0), 0.002); rod((D - 0.10, 0, 0.55), (0, 0, 0), 0.002)   # string
    rod((-0.03, 0, 0), (0.78, 0, 0), 0.005)                                                     # arrow
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join()
    bow = bpy.context.active_object; bow.name = bow.data.name = "gfl_bow"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if not bow.data.uv_layers: bow.data.uv_layers.new(name="UVMap")
    for name, pos, euler in (("muzzle", (0.78, 0, 0), (0, 0, -90)), ("silencer_socket", (0.78, 0, 0), (0, 0, -90)),
                             ("optics_socket", (D - 0.05, 0, 0.12), (0, 0, -90)), ("IKHandL", (D - 0.02, 0, 0), (-180, 0, 0))):
        e = bpy.data.objects.new("HELPER_" + name, None); bpy.context.collection.objects.link(e); e.parent = bow
        e.location = pos; e.rotation_euler = [math.radians(v) for v in euler]
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(D / 2, 0, 0)); col = bpy.context.active_object
    col.name = "COL_SPHERE"; col.parent = bow; col.scale = (0.06, 0.06, 0.06); upd()
    return bow

bpy.ops.wm.read_homefile(use_empty=True)
bow = build_bow_mesh(); select_only(bow)
bpy.ops.export_scene.khm(filepath=f"{OUT_MODELS}/gfl_bow.khm", export_mesh=True, export_animation=False, export_animation_mask=False)
bm = import_khm.LoadModel(f"{OUT_MODELS}/gfl_bow.khm")
open(os.path.join(ROOT, "draw_length.txt"), "w").write(str(D))
log("bow model verts", bm.pMesh.numVertices, "helpers", [(h.szName, [round(v, 2) for v in h.matGlobal.to_translation()]) for h in bm.lHelpers])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "gfl_bow.blend"))

# ------------------------------------------- pose file for hand editing: four single-frame actions
POSES = {"pose_aim": lambda: pose_upper(0, ANCHOR, FWD, TORSO_YAW),
         "pose_release": lambda: pose_upper(0, ANCHOR + Vector((0, 0.05, 0.02)), FWD, TORSO_YAW),
         "pose_nock": lambda: pose_upper(0, NOCK, FWD, TORSO_YAW),
         "pose_low": lambda: pose_upper(0, LOW_WRIST, LOW_DIR, 0.0)}
bpy.ops.wm.read_homefile(use_empty=True)
imp(filepath=f"{DK}/models/humans/ranger_assaulter.khm"); arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]; PB = arm.pose.bones
for pb in PB: pb.rotation_mode = "QUATERNION"
before = set(bpy.data.objects); imp(filepath=f"{OUT_MODELS}/gfl_bow.khm"); bowobj = [o for o in bpy.data.objects if o not in before and o.type == "MESH" and not o.name.startswith("COL_")][0]
for o in [o for o in bpy.data.objects if o not in before and o is not bowobj]: bpy.data.objects.remove(o, do_unlink=True)
bowobj.parent = arm; bowobj.parent_type = "BONE"; bowobj.parent_bone = "HELPER_Prop_R"
b = arm.data.bones["HELPER_Prop_R"]; bowobj.matrix_parent_inverse = (b.matrix_local @ Matrix.Translation((0, b.length, 0))).inverted() @ b.matrix_local
for name, fn in POSES.items():
    load_base("idle_aim"); bpy.context.scene.frame_set(0); upd(); fn(); upd()
    act = bpy.data.actions.new(name); arm.animation_data.action = None
    arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots.new(id_type="OBJECT", name="OBArmature")
    except Exception: pass
    for pb in PB:
        if not pb.name.startswith("HELPER_"):
            pb.keyframe_insert("rotation_quaternion", frame=0); pb.keyframe_insert("location", frame=0)
    act.use_fake_user = True
arm.animation_data.action = bpy.data.actions["pose_aim"]
try: arm.animation_data.action_slot = bpy.data.actions["pose_aim"].slots[0]
except Exception: pass
bpy.context.scene.frame_start = 0; bpy.context.scene.frame_end = 0; bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "bow_poses.blend"))
log("saved bow_poses.blend with", list(POSES))

# ------------------------------------------- previews: rig in the bow poses with the bow on Prop_R
bpy.ops.wm.read_homefile(use_empty=True)
imp(filepath=f"{DK}/models/humans/ranger_assaulter.khm"); arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]; PB = arm.pose.bones
for pb in PB: pb.rotation_mode = "QUATERNION"
before = set(bpy.data.objects); imp(filepath=f"{OUT_MODELS}/gfl_bow.khm"); bowobj = [o for o in bpy.data.objects if o not in before and o.type == "MESH" and not o.name.startswith("COL_")][0]
for o in [o for o in bpy.data.objects if o not in before and o is not bowobj]: bpy.data.objects.remove(o, do_unlink=True)
bowobj.parent = arm; bowobj.parent_type = "BONE"; bowobj.parent_bone = "HELPER_Prop_R"
b = arm.data.bones["HELPER_Prop_R"]; bowobj.matrix_parent_inverse = (b.matrix_local @ Matrix.Translation((0, b.length, 0))).inverted() @ b.matrix_local
bowobj.color = (0.9, 0.3, 0.2, 1)
sc = bpy.context.scene
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); bpy.context.collection.objects.link(cam); sc.camera = cam
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); bpy.context.collection.objects.link(sun); sun.rotation_euler = (math.radians(50), 0, math.radians(30))
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = 1000; sc.render.resolution_y = 700; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "OBJECT"
def shot(name, pos, target):
    cam.location = pos; cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(ROOT, f"preview_{name}.png"); bpy.ops.render.render(write_still=True)
for clip, frame in (("bow_idle_aim", 0), ("bow_idle_low", 0), ("bow_reload", 14), ("bow_fire", 2)):
    arm.animation_data_clear(); select_only(arm); imp(filepath=f"{OUT_ANIMS}/{clip}.khm"); sc.frame_set(frame); upd()
    shot(clip + "_side", (-3.2, -1.2, 1.7), (0, -0.3, 1.2)); shot(clip + "_top", (0, -0.3, 5.5), (0, -0.31, 0))
log("previews written")
