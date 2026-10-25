"""Derive pose_release, pose_nock and pose_low from the hand-made pose_aim in bow_poses.blend.

Only the arms are moved, by rotating upper arm and forearm; each hand keeps the rotation
relative to its forearm that was set by hand, so nothing twists. The left hand follows the
bow grip, which sits D metres along the string hand's aim axis.

This only seeded the three poses: they were hand-tuned in bow_poses.blend afterwards, so running
it again throws that work away. Needs rifle_clips/, so run build_from_poses.py once first.
"""
import bpy, os, math
from mathutils import Vector, Matrix, Quaternion
ROOT = os.path.dirname(os.path.abspath(__file__))
DK = os.path.expanduser("~/.local/share/Steam/steamapps/common/DoorKickers2/data")
from khm_tools import import_khm
D = 0.426   # string hand to bow grip along the aim axis, metres (build_ullrid_bow.py puts the grip here)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "bow_poses.blend"))
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]; PB = arm.pose.bones
PROP_R_LOCAL = [h for h in import_khm.LoadModel(f"{DK}/models/humans/ranger_assaulter.khm").lHelpers if h.szName == "Prop_R"][0].matLocal
R_ARM = ("Bip001 R UpperArm", "Bip001 R Forearm", "Bip001 R Hand"); L_ARM = ("Bip001 L UpperArm", "Bip001 L Forearm", "Bip001 L Hand")
def subtree(name):
    out = [name]
    for c in PB[name].children: out += subtree(c.name)
    return out
UPPER = [n for n in subtree("Bip001 Spine1") if not n.startswith("HELPER_")]
def log(*a): print("==", *a)
def upd(): bpy.context.view_layer.update()
def head(n): return PB[n].matrix.to_translation()
def bow_dir(): return (PB["Bip001 R Hand"].matrix @ PROP_R_LOCAL).to_3x3() @ Vector((1, 0, 0))
def prop_r(): return (PB["Bip001 R Hand"].matrix @ PROP_R_LOCAL).to_translation()

def rotate_about_head(name, R3):
    pb = PB[name]; h = pb.matrix.to_translation()
    pb.matrix = Matrix.Translation(h) @ R3.to_4x4() @ Matrix.Translation(-h) @ pb.matrix; upd()

def aim_bone(name, tip, target, fraction=1.0):
    h = head(name); a = head(tip) - h; b = target - h
    if a.length < 1e-6 or b.length < 1e-6: return
    q = a.rotation_difference(b)
    if fraction != 1.0: q = Quaternion((1, 0, 0, 0)).slerp(q, fraction)
    rotate_about_head(name, q.to_matrix())

def reach(chain, wrist_target, iters=16):
    """move the wrist with upper arm and forearm only; the hand keeps its local rotation"""
    upper, fore, hand = chain
    for _ in range(iters):
        aim_bone(fore, hand, wrist_target); aim_bone(upper, hand, wrist_target, 0.6)

def left_to_grip():
    reach(L_ARM, prop_r() + bow_dir().normalized() * (D - 0.08))

def assign(name):
    act = bpy.data.actions[name]; arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    bpy.context.scene.frame_set(0); upd()

def snapshot(): return {n: (PB[n].rotation_quaternion.copy(), PB[n].location.copy()) for n in UPPER}
def restore(p):
    for n, (q, l) in p.items(): PB[n].rotation_quaternion = q; PB[n].location = l
    upd()
def write(name, pose):
    assign(name)   # the action's old keys get evaluated here, so set each value right before keying it
    for n, (q, l) in pose.items():
        PB[n].rotation_quaternion = q; PB[n].keyframe_insert("rotation_quaternion", frame=0)
        PB[n].location = l; PB[n].keyframe_insert("location", frame=0)

def detach():
    arm.animation_data.action = None; upd()

assign("pose_aim"); AIM = snapshot()
# how far the torso is turned side-on compared to the game's rifle idle it sits on
base = import_khm.LoadModel(os.path.join(ROOT, "rifle_clips", "idle_aim.khm")).pAnimation
model = import_khm.LoadModel(f"{DK}/models/humans/ranger_assaulter.khm")
names = [n.szNodeName for n in base.pNodeAnimations]; F = base.numNodeFrames; W = {}
for b in model.lBones:
    t = base.pNodeTransforms[names.index(b.szName) * F]; L = Matrix.LocRotScale(t.vTrans, t.qRot, t.vScale)
    W[b.uiId] = (W[b.uiParentId] @ L) if b.uiParentId != -1 else L
base_spine1 = W[[b.uiId for b in model.lBones if b.szName == "Bip001 Spine1"][0]]
bx = base_spine1.to_3x3() @ Vector((0, 1, 0)); hx = PB["Bip001 Spine1"].matrix.to_3x3() @ Vector((0, 1, 0))
bx.z = hx.z = 0
TORSO_YAW = bx.angle(hx) * (1 if bx.cross(hx).z > 0 else -1)
log("torso turned", round(math.degrees(TORSO_YAW), 1), "deg from the rifle idle")
w0 = head("Bip001 R Hand"); d0 = bow_dir().normalized()
log("your aim: right wrist", [round(v, 3) for v in w0], "bow direction", [round(v, 2) for v in d0], "left wrist", [round(v, 3) for v in head("Bip001 L Hand")])

# release: string hand snaps 5 cm back along the arrow line and 2 cm up
detach(); restore(AIM)
reach(R_ARM, w0 - d0 * 0.05 + Vector((0, 0, 0.02))); left_to_grip(); REL = snapshot()
log("release: right wrist", [round(v, 3) for v in head("Bip001 R Hand")])

# nock: string hand drops to chest height and forward, bow still pointing the same way
detach(); restore(AIM)
reach(R_ARM, w0 + Vector((0, -0.19, -0.27)))
# level the bow back to about 15 degrees down and look at the arrow
d = bow_dir().normalized(); pitch = math.asin(-d.z)
rotate_about_head("Bip001 R Hand", Matrix.Rotation(-(pitch - math.radians(15)), 3, "X"))
rotate_about_head("Bip001 Head", Matrix.Rotation(math.radians(20), 3, "X"))
left_to_grip(); NOCK = snapshot()
log("nock: right wrist", [round(v, 3) for v in head("Bip001 R Hand")], "bow direction", [round(v, 2) for v in bow_dir().normalized()])

# low: swing the whole right arm so the bow points down and forward, then bring the left hand along
detach(); restore(AIM)
low_dir = Vector((0, -0.6, -0.8)).normalized()
# turn the torso most of the way back to face forward, head with it, before dropping the arms
rotate_about_head("Bip001 Spine1", Matrix.Rotation(-TORSO_YAW * 0.8, 3, "Z"))
rotate_about_head("Bip001 Head", Matrix.Rotation(TORSO_YAW * 0.8, 3, "Z"))
d0l = bow_dir().normalized()
rotate_about_head("Bip001 R UpperArm", d0l.rotation_difference(low_dir).to_matrix())
reach(R_ARM, Vector((-0.16, -0.24, 1.08))); left_to_grip(); LOW = snapshot()
log("low: right wrist", [round(v, 3) for v in head("Bip001 R Hand")], "bow direction", [round(v, 2) for v in bow_dir().normalized()])

write("pose_release", REL); write("pose_nock", NOCK); write("pose_low", LOW)
assign("pose_aim")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "bow_poses.blend"))
log("saved")
