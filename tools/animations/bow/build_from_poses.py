"""Turn the four hand-made poses in bow_poses.blend into the bow clips.

Run headless:  blender --background --python tools/animations/bow/build_from_poses.py

Upper body (Spine1 and everything under it) is blended between the poses; legs, spine
and breathing come from the game's rifle clips so the character stands like the others.
"""
import bpy, os, math
from mathutils import Vector, Matrix, Quaternion

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))
DK = os.path.expanduser("~/.local/share/Steam/steamapps/common/DoorKickers2/data")
CLIPS_IN = os.path.join(ROOT, "rifle_clips")
OUT_ANIMS = os.path.join(REPO, "mod", "animations", "khm", "bow")
os.makedirs(OUT_ANIMS, exist_ok=True)
import addon_utils
if "khm" not in dir(bpy.ops.export_scene): addon_utils.enable("khm_tools")
from khm_tools import import_khm
imp = getattr(bpy.ops.khm, "import")


def log(*a): print("==", *a)
def objmode():
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
def select_only(o):
    objmode(); bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
def smooth(u): return u * u * (3 - 2 * u)


# ------------------------------------------------ read the four poses
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "bow_poses.blend"))
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]; PB = arm.pose.bones
def subtree(name):
    out = [name]
    for c in PB[name].children: out += subtree(c.name)
    return out
UPPER = [n for n in subtree("Bip001 Spine1") if not n.startswith("HELPER_")]
POSES = {}
for name in ("pose_aim", "pose_release", "pose_nock", "pose_low"):
    act = bpy.data.actions[name]; arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    bpy.context.scene.frame_set(0); bpy.context.view_layer.update()
    POSES[name] = {n: (PB[n].rotation_quaternion.copy(), PB[n].location.copy()) for n in UPPER}
log("poses read:", list(POSES), "| upper body bones", len(UPPER))


def mix(a, b, t):
    return {n: (a[n][0].slerp(b[n][0], t), a[n][1].lerp(b[n][1], t)) for n in a}


def apply(pose, frame):
    for n, (q, l) in pose.items():
        PB[n].rotation_quaternion = q; PB[n].location = l
        PB[n].keyframe_insert("rotation_quaternion", frame=frame); PB[n].keyframe_insert("location", frame=frame)


def load_base(clip):
    arm.animation_data_clear()
    for pb in PB: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    select_only(arm); imp(filepath=f"{CLIPS_IN}/{clip}.khm")
    return bpy.context.scene.frame_end + 1


def build(name, base, nframes, pose_at):
    n_base = load_base(base); N = nframes or n_base
    sc = bpy.context.scene; sc.frame_start = 0; sc.frame_end = N - 1; sc.render.fps = 30
    for f in range(N):
        sc.frame_set(min(f, n_base - 1))
        for pb in PB:   # legs and spine from the game's clip, keyed so the clip is self-contained
            if pb.name not in UPPER and not pb.name.startswith("HELPER_"):
                pb.keyframe_insert("rotation_quaternion", frame=f); pb.keyframe_insert("location", frame=f)
        apply(pose_at(f / max(N - 1, 1)), f)
    select_only(arm)
    path = f"{OUT_ANIMS}/{name}.khm"
    bpy.ops.export_scene.khm(filepath=path, export_mesh=False, export_animation=True, export_animation_mask=False)
    a = import_khm.LoadModel(path).pAnimation
    log("clip", name, "frames", a.numNodeFrames, "nodes", a.numNodes, round(a.endTimeS, 2), "s")
    return N

P = POSES
build("bow_idle_aim", "idle_aim", None, lambda u: P["pose_aim"])
build("bow_idle_low", "idle_low", None, lambda u: P["pose_low"])
build("bow_fire", "fire_aim", 12, lambda u: mix(P["pose_aim"], P["pose_release"], math.sin(math.pi * min(u * 1.5, 1)) if u < 2 / 3 else 0.0))
def reload_pose(u):
    if u < 0.3: return mix(P["pose_release"], P["pose_nock"], smooth(u / 0.3))
    if u < 0.5: return P["pose_nock"]
    if u < 0.9: return mix(P["pose_nock"], P["pose_aim"], smooth((u - 0.5) / 0.4))
    return P["pose_aim"]
reload_frames = build("bow_reload", "reload_aim", 40, reload_pose)
build("bow_lower", "lower_weapon", None, lambda u: mix(P["pose_aim"], P["pose_low"], smooth(u)))
log("reload ms", round(reload_frames / 30 * 1000))
