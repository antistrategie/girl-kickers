"""GFL2 weapons that build_weapon.py turns into mod/models/signatures/<name>.khm and .dds.

Each row is keyed by the khm name the weapon XML points at.

gfl2      the client's weapon name: the mesh is cw_<gfl2>_WL_lod0, the diffuse cw_<gfl2>_WL_d.
kind      "gun" (Prop_R rifle frame, IKHandL on the handguard) or "blade" (Hare's frame,
          the same as the vanilla sword: handle at the origin with about 0.1 m of pommel
          behind it, blade along +X lying flat in XY, no helpers).
origin    where the right hand grips, in the GFL2 weapon's own (Unity) coordinates. Defaults
          to the GFL2 origin, which is the pistol grip on most guns.
ik_x      how far ahead of the grip the left hand holds a gun, in metres. The game's rifle aim
          clip puts the left wrist about 0.26 ahead of Prop_R, and the roster's guns sit
          between 0.10 and 0.29.
roll      blades only: degrees about the blade axis that lay it flat like the vanilla sword.

These are the starting points. Once a weapon's .blend exists it is the source of truth: nudge
the mesh and helpers there and rerun the script, which exports from the .blend instead of
rebuilding it (pass --rebuild to start over from this table).
"""

WEAPONS = {
    "kp31": {"gfl2": "SuomiSR01", "kind": "gun", "ik_x": 0.2},
    "m1super90": {"gfl2": "LottaSR01", "kind": "gun", "ik_x": 0.27},
    # Littara's and Balthilde's GFL2 origin sits by the magazine. Their Grip_Node marks the
    # pistol grip.
    "galilarm": {
        "gfl2": "LittaraSR01",
        "kind": "gun",
        "origin": (-0.282, -0.07),
        "ik_x": 0.27,
    },
    "ls26": {
        "gfl2": "BalthildeSR01",
        "kind": "gun",
        "origin": (-0.282, -0.07),
        "ik_x": 0.27,
    },
    # Blades: GFL2 puts the origin mid-blade. These sit 0.1 m ahead of the pommel, as on Hare.
    "pluedge": {
        "gfl2": "UllridSR01",
        "kind": "blade",
        "origin": (-0.38, 0.03),
        "roll": -90,
    },
    "graythorn": {
        "gfl2": "PhaetusaSR01",
        "kind": "blade",
        "origin": (-0.37, 0.03),
        "roll": -90,
    },
}
