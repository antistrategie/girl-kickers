"""
Add DK2 Armature and Weights to Prepared Model

This script:
1. Opens a prepared .blend file from prepare_mmd.py
2. Imports armature and mesh from a reference KHM file
3. Transfers weights using Blender's Data Transfer modifier
4. Saves the result

Note: For better results, open the .blend file in Blender and use
Voxel Heat Diffuse Skinning addon manually.
"""

import sys
from pathlib import Path

import addon_utils
import bpy

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"


def get_args():
    """Parse command line arguments."""
    blend_path = None
    reference_khm = None

    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]

    for i, arg in enumerate(argv):
        if arg == "--blend" and i + 1 < len(argv):
            blend_path = argv[i + 1]
        elif arg == "--reference" and i + 1 < len(argv):
            reference_khm = argv[i + 1]

    if not blend_path:
        raise ValueError("No blend file specified. Use --blend /path/to/model.blend")
    if not reference_khm:
        raise ValueError(
            "No reference KHM specified. Use --reference /path/to/reference.khm"
        )

    return blend_path, reference_khm


def cleanup_existing_armatures_and_collisions():
    """Remove any existing armatures and collision meshes from the scene."""
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    collisions = [
        obj for obj in bpy.data.objects if obj.type == "MESH" and "COL_" in obj.name
    ]

    for arm in armatures:
        bpy.data.objects.remove(arm, do_unlink=True)
    for col in collisions:
        bpy.data.objects.remove(col, do_unlink=True)

    # Clean up orphan data
    for arm_data in bpy.data.armatures:
        if arm_data.users == 0:
            bpy.data.armatures.remove(arm_data)
    for mesh_data in bpy.data.meshes:
        if mesh_data.users == 0:
            bpy.data.meshes.remove(mesh_data)

    if armatures:
        print(f"Removed {len(armatures)} existing armature(s)")
    if collisions:
        print(f"Removed {len(collisions)} existing collision mesh(es)")


def import_khm_armature_and_mesh(khm_path, target_mesh_name):
    """Import a KHM file and return armature, source mesh, and collision mesh."""
    # Clean up any existing armatures and collisions first
    cleanup_existing_armatures_and_collisions()

    # Enable khm_tools addon
    addon_utils.enable("khm_tools")

    # Import the KHM
    import_op = getattr(bpy.ops.khm, "import")
    import_op(filepath=khm_path)

    # Find the imported armature and mesh
    armature = None
    source_mesh = None
    collision_mesh = None
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            armature = obj
        elif obj.type == "MESH" and obj.name != target_mesh_name:
            if "COL_" in obj.name:
                collision_mesh = obj
            else:
                source_mesh = obj

    if not armature:
        raise ValueError("No armature found in KHM file")

    # Rename armature to clean name
    armature.name = "Armature"
    armature.data.name = "Armature"

    print(f"Imported armature with {len(armature.data.bones)} bones")
    if source_mesh:
        print(f"Source mesh for weight transfer: {source_mesh.name}")
    if collision_mesh:
        print(f"Collision mesh: {collision_mesh.name}")

    return armature, source_mesh, collision_mesh


def transfer_weights_data_transfer(target_mesh, source_mesh, armature):
    """Transfer weights using Blender's Data Transfer modifier."""
    # First, parent target to armature with empty vertex groups
    bpy.ops.object.select_all(action="DESELECT")
    target_mesh.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type="ARMATURE_NAME")

    # Select target mesh
    bpy.ops.object.select_all(action="DESELECT")
    target_mesh.select_set(True)
    bpy.context.view_layer.objects.active = target_mesh

    # Add Data Transfer modifier
    mod = target_mesh.modifiers.new(name="DataTransfer", type="DATA_TRANSFER")
    mod.object = source_mesh
    mod.use_vert_data = True
    mod.data_types_verts = {"VGROUP_WEIGHTS"}
    mod.vert_mapping = "POLYINTERP_NEAREST"

    # Apply the modifier
    bpy.ops.object.modifier_apply(modifier=mod.name)

    print("Data Transfer weight transfer completed")
    return True


def clean_vertex_groups(mesh, armature):
    """Remove vertex groups that don't correspond to bones."""
    bone_names = set(bone.name for bone in armature.data.bones)

    groups_to_remove = []
    for vg in mesh.vertex_groups:
        if vg.name not in bone_names and not vg.name.startswith("HELPER_"):
            groups_to_remove.append(vg.name)

    for name in groups_to_remove:
        vg = mesh.vertex_groups.get(name)
        if vg:
            mesh.vertex_groups.remove(vg)

    if groups_to_remove:
        print(f"Removed {len(groups_to_remove)} unused vertex groups")


def main():
    blend_path, reference_khm = get_args()

    print(f"\n{'=' * 60}")
    print("Add DK2 Armature and Weights")
    print(f"{'=' * 60}")
    print(f"Blend:     {blend_path}")
    print(f"Reference: {reference_khm}")
    print(f"{'=' * 60}\n")

    # Open the blend file
    bpy.ops.wm.open_mainfile(filepath=blend_path)

    # Find the target mesh (skip collision meshes)
    mesh = None
    for obj in bpy.data.objects:
        if obj.type == "MESH" and "COL_" not in obj.name:
            mesh = obj
            break

    if not mesh:
        raise ValueError("No mesh found in blend file")

    print(f"Target mesh: {mesh.name}")

    # Import armature and source mesh from reference KHM
    print(f"\nImporting armature from {reference_khm}...")
    armature, source_mesh, collision_mesh = import_khm_armature_and_mesh(
        reference_khm, mesh.name
    )

    if source_mesh:
        print("\nTransferring weights from reference mesh...")
        success = transfer_weights_data_transfer(mesh, source_mesh, armature)

        # Delete source mesh after transfer
        bpy.data.objects.remove(source_mesh, do_unlink=True)
        print("Deleted reference mesh")

        if not success:
            print("Weight transfer failed")
    else:
        print("\nNo reference mesh available for weight transfer")

    # Parent collision mesh to target mesh (not armature)
    if collision_mesh:
        collision_mesh.parent = mesh
        print(f"Parented {collision_mesh.name} to {mesh.name}")

    # Clean up vertex groups
    clean_vertex_groups(mesh, armature)

    # Save the file
    bpy.ops.wm.save_mainfile()
    print(f"\nSaved to {blend_path}")

    print(f"\n{'=' * 60}")
    print("DONE!")
    print(f"{'=' * 60}")
    print(f"Mesh: {mesh.name}")
    print(f"Armature: {armature.name}")
    print(f"Vertex groups: {len(mesh.vertex_groups)}")
    if collision_mesh:
        print(f"Collision: {collision_mesh.name} (parented to {mesh.name})")
    print("\nNext steps:")
    print(f"1. Open {blend_path} and check weights")
    print(f"2. Export to KHM: mod/models/dolls/{mesh.name}.khm")
    print(f"3. Convert {mesh.name}.png to DDS")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
