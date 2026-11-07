"""Which GFL2 art each generated sprite comes from.

DOLLS is keyed by the portrait id: `gfl_<id>.dds` and `gfl_<id>_large.dds` under
mod/textures/portraits/. `gfl2` is the client's art suffix (Avatar_Whole_<gfl2>,
Avatar_Head_<gfl2>). `head_box` (x, y, size in Avatar_Whole pixels, top of the hair to just
below the chin) overrides the automatic head match when it lands wrong.

UNITS is keyed by the unit slug (GFL-UNIT-<SLUG>, lowercased), which names
mod/textures/gfl_<slug>_bg.dds and gui/deploy/gfl_class_icon_<slug>.dds. `logo` is the
Img_CampLogo_<logo> faction logo. The flag colour is read from the unit XML.

Only dolls and units without hand-made art are listed. Add a row and run `mise run sprites`.
"""

DOLLS = {
    "kp31": {"gfl2": "SuomiSSR"},
    "pluedge": {"gfl2": "UllridSSR"},
    "m1super90": {"gfl2": "LottaSR"},
    "galilarm": {"gfl2": "LittaraSR"},
    "ls26": {"gfl2": "BalthildeSSR"},
    "graythorn": {"gfl2": "PhaetusaSSR"},
}

UNITS = {
    "dollcom": {"logo": "DollCom"},
}
