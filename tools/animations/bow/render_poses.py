"""Render the four poses in bow_poses.blend into contact_poses.png (side and front of each).

blender --background --python tools/animations/bow/render_poses.py
"""
import bpy, math, os, subprocess
from mathutils import Vector
ROOT = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "bow_poses.blend"))
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
for o in bpy.data.objects:
    if o.name.startswith("COL_"): o.hide_render = True
    if o.name == "gfl_bow": o.color = (0.9, 0.3, 0.2, 1)
    if o.name == "ranger_assaulter": o.hide_render = False
sc = bpy.context.scene
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); bpy.context.collection.objects.link(cam); sc.camera = cam
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); bpy.context.collection.objects.link(sun); sun.rotation_euler = (math.radians(50), 0, math.radians(30))
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = 700; sc.render.resolution_y = 700
sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "OBJECT"
def shot(name, pos, target):
    cam.location = pos; cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(ROOT, f"preview_{name}.png"); bpy.ops.render.render(write_still=True)
files = []
for name in ("pose_aim", "pose_release", "pose_nock", "pose_low"):
    act = bpy.data.actions[name]; arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    sc.frame_set(0); bpy.context.view_layer.update()
    shot(name + "_side", (-3.0, -1.0, 1.6), (0, -0.35, 1.25)); shot(name + "_front", (0.6, -3.4, 1.7), (0, -0.4, 1.25))
    files += [os.path.join(ROOT, f"preview_{name}_side.png"), os.path.join(ROOT, f"preview_{name}_front.png")]
subprocess.run(["magick", "montage", *files, "-tile", "4x2", "-geometry", "+2+2", "-background", "#333", os.path.join(ROOT, "contact_poses.png")], check=True)
print("== wrote", os.path.join(ROOT, "contact_poses.png"))
