#!/usr/bin/env python3
"""
Script to generate deploy screen GUI from unit definitions.

This script reads unit definitions from gfl_unit.xml and generates:
1. Base unit deploy screens (gfl_deploy.xml)
2. GIRL tabbed deploy screen (gfl_deploy_girl.xml)

Layout rules:
- Units with ≤4 dolls: Single column (380px wide)
- Units with >4 dolls: Two columns (178px each)

Usage:
    python generate_deploy_screens.py
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path


def extract_unit_data(unit_xml_path):
    """Extract unit information including class count and colors."""
    with open(unit_xml_path, "r", encoding="utf-8") as f:
        content = f.read()

    units = []

    unit_pattern = r'<Unit\s+name="(GFL-UNIT-[^"]+)"[^>]*flagColor="([^"]+)"[^>]*>.*?<Classes>(.*?)</Classes>'
    matches = re.findall(unit_pattern, content, re.DOTALL)

    for unit_name, flag_color, classes_block in matches:
        class_pattern = r'<Class\s+name="(GFL-DOLL-[^"]+)"'
        classes = re.findall(class_pattern, classes_block)

        units.append(
            {
                "name": unit_name,
                "flag_color": flag_color,
                "classes": classes,
                "count": len(classes),
            }
        )

    return units


def generate_class_item(
    class_name,
    x_origin,
    y_origin,
    slot_num,
    width,
    flag_color,
    indent=" ",
):
    """Generate a single class item for the deploy screen."""

    template = f'''{indent}<StaticImage name="{class_name}" origin="{x_origin} {y_origin}">
{indent}    <RenderObject2D
{indent}            texture="data/textures/gui/square.tga"
{indent}            sizeX="{width}"
{indent}            sizeY="148"
{indent}            color="211e1dcc"
{indent}        />
{indent}    <StaticImage name="#ClassHeader" origin="0 0" align="t">
{indent}        <RenderObject2D
{indent}                texture="data/textures/gui/square.tga"
{indent}                sizeX="{width}"
{indent}                sizeY="46"
{indent}                color="4B4B4B"
{indent}            />
{indent}    </StaticImage>
{indent}    <StaticImage origin="0 0" align="lt">
{indent}        <RenderObject2D
{indent}                texture="data/textures/gui/deploy/deploy_class_diagonalbars.dds"
{indent}                color="0c0b0b33"
{indent}            />
{indent}    </StaticImage>
{indent}    <StaticImage origin="-16 0" align="lt">
{indent}        <RenderObject2D
{indent}                texture="data/textures/gui/square.tga"
{indent}                sizeX="8"
{indent}                sizeY="148"
{indent}                color="{flag_color}"
{indent}            />
{indent}    </StaticImage>
{indent}    <StaticText
{indent}            name="#ClassName"
{indent}            origin="-6 50"
{indent}            text=""
{indent}            align="r"
{indent}            font="header_4"
{indent}            textColor="211e1d"
{indent}        />
{indent}    <StaticImage name="#ClassIcon" origin="8 50" align="l">
{indent}        <RenderObject2D
{indent}                texture="data/textures/gui/deploy/class_name_icon_assaulter.dds"
{indent}            />
{indent}    </StaticImage>
{indent}    <Item origin="-2 -25">
{indent}        <StaticImage name="#slot{slot_num}" origin="0 0">
{indent}            <RenderObject2D
{indent}                    texture="data/textures/gui/deploy/deploy_trooperbackground_01.tga"
{indent}                />
{indent}        </StaticImage>
{indent}    </Item>
{indent}</StaticImage>
'''
    return template


def generate_class_item_girl(
    class_name,
    x_origin,
    y_origin,
    slot_num,
    width,
    flag_color,
    indent=" ",
):
    """Generate class item for GIRL deploy screen (with align="t" and name on left bar)."""

    template = f'''{indent}<StaticImage name="{class_name}" origin="{x_origin} {y_origin}" align="t">
{indent}    <RenderObject2D
{indent}            texture="data/textures/gui/square.tga"
{indent}            sizeX="{width}"
{indent}            sizeY="148"
{indent}            color="211e1dcc"
{indent}        />
{indent}    <StaticImage name="#ClassHeader" origin="0 0" align="t">
{indent}        <RenderObject2D
{indent}                texture="data/textures/gui/square.tga"
{indent}                sizeX="{width}"
{indent}                sizeY="46"
{indent}                color="4B4B4B"
{indent}            />
{indent}    </StaticImage>
{indent}    <StaticImage origin="0 0" align="lt">
{indent}        <RenderObject2D
{indent}                texture="data/textures/gui/deploy/deploy_class_diagonalbars.dds"
{indent}                color="0c0b0b33"
{indent}            />
{indent}    </StaticImage>
{indent}    <StaticImage name="#ClassBackgroundLeftBar" origin="-16 0" align="lt">
{indent}        <RenderObject2D
{indent}                texture="data/textures/gui/square.tga"
{indent}                sizeX="8"
{indent}                sizeY="148"
{indent}                color="{flag_color}"
{indent}            />
{indent}    </StaticImage>
{indent}    <StaticText
{indent}            name="#ClassName"
{indent}            origin="-6 50"
{indent}            text=""
{indent}            align="r"
{indent}            font="header_4"
{indent}            textColor="211e1d"
{indent}        />
{indent}    <StaticImage name="#ClassIcon" origin="8 50" align="l">
{indent}        <RenderObject2D
{indent}                texture="data/textures/gui/deploy/class_name_icon_assaulter.dds"
{indent}            />
{indent}    </StaticImage>
{indent}    <Item origin="-2 -25">
{indent}        <StaticImage name="#slot{slot_num}" origin="0 0">
{indent}            <RenderObject2D
{indent}                    texture="data/textures/gui/deploy/deploy_trooperbackground_01.tga"
{indent}                />
{indent}        </StaticImage>
{indent}    </Item>
{indent}</StaticImage>
'''
    return template


def generate_unit_item(unit, indent=""):
    """Generate a complete unit item for base deploy screen."""

    unit_name = unit["name"]
    flag_color = unit["flag_color"]
    classes = unit["classes"]
    count = unit["count"]

    # Determine layout
    use_two_columns = count > 4
    width = 178 if use_two_columns else 380

    # Start unit item
    output = f'''
{indent}<EventActionBatch name="GAME_GUI_LOADTIME_ACTIONS">
{indent}    <Action type="Show" target="{unit_name}" />
{indent}</EventActionBatch>

{indent}<Item name="{unit_name}" origin="0 -172" hidden="true" align="rt" sizeX="380">
{indent}    <OnOpen>
{indent}        <Action type="AddMeToParent" target="#unit_header" />
{indent}    </OnOpen>

'''

    slot_num = 0
    for i, class_name in enumerate(classes):
        if use_two_columns:
            row = i // 2
            col = i % 2
            x_origin = -101 if col == 0 else 100
            y_origin = -214 + (row * -160)
        else:
            x_origin = 0
            y_origin = -214 + (i * -160)

        output += generate_class_item(
            class_name,
            x_origin,
            y_origin,
            slot_num,
            width,
            flag_color,
            indent=indent + " ",
        )
        output += "\n"
        slot_num += 1

    output += f"{indent}</Item>\n"

    return output


def generate_base_deploy(units, output_path):
    """Generate gfl_deploy.xml for base units."""
    output = "<GUIItems>"

    for unit in units:
        output += generate_unit_item(unit)

    output += "</GUIItems>"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)


def generate_tab_button(tab_num, unit, total_tabs, container_num):
    """Generate a tab button for GIRL deploy screen."""
    unit_name = unit["name"]

    # Extract squad name from unit (e.g., GFL-UNIT-DEFY -> defy)
    squad = unit_name.replace("GFL-UNIT-", "").lower()

    # Position calculation: 5 tabs per row, each 72px apart horizontally
    # Within each container, tabs are positioned at Y=0 (all in same row)
    tabs_per_row = 5
    col = tab_num % tabs_per_row
    x_pos = -304 + (col * 72)
    y_pos = 0

    default_state = "CheckedState" if tab_num == 0 else "UncheckedState"

    # Build list of other tabs to uncheck (dynamic based on total tabs)
    other_tabs = [f"tab{i}_cbox" for i in range(total_tabs) if i != tab_num]
    uncheck_actions = "\n                    ".join(
        [f'<Action type="Uncheck" target="{t}" />' for t in other_tabs]
    )

    template = f'''        <!-- Tab {tab_num}: {unit_name} -->
        <Checkbox
                name="tab{tab_num}_cbox"
                origin="{x_pos} {y_pos}"
                align="r"
                stealFocus="true"
                defaultState="{default_state}"
            >
            <UncheckedState>
                <RenderObject2D
                        texture="data/textures/gui/square.tga"
                        sizeX="64"
                        sizeY="64"
                        color="080808cc"
                    />
                <OnOpen>
                    <Action type="Hide" target="unit_tab{tab_num}" />
                    <Action type="Hide" target="icon_{squad}_active" />
                    <Action type="Show" target="icon_{squad}" />
                </OnOpen>
                <OnClick>
                    <RenderObject2D
                            texture="data/textures/gui/square.tga"
                            sizeX="60"
                            sizeY="60"
                            color="E3F6FD"
                        />
                    {uncheck_actions}
                </OnClick>
                <OnHover>
                    <RenderObject2D
                            texture="data/textures/gui/square.tga"
                            sizeX="64"
                            sizeY="64"
                            color="E3F6FD"
                        />
                    <Action type="Hide" target="icon_{squad}" />
                    <Action type="Show" target="icon_{squad}_hover" />
                </OnHover>
                <OnHoverEnd>
                    <Action type="Hide" target="icon_{squad}_hover" />
                    <Action type="Show" target="icon_{squad}" />
                </OnHoverEnd>
            </UncheckedState>
            <CheckedState acceptInput="false">
                <RenderObject2D
                        texture="data/textures/gui/square.tga"
                        sizeX="64"
                        sizeY="64"
                        color="080808cc"
                    />
                <OnOpen>
                    <Action type="SetOrigin" target="#deploy_squad_buttons" params="-8 0" />
                    <Action type="Show" target="unit_tab{tab_num}" />
                    <Action type="Hide" target="icon_{squad}" />
                    <Action type="Show" target="icon_{squad}_active" />
                </OnOpen>
            </CheckedState>

            <StaticImage name="icon_{squad}" origin="0 0" hidden="true">
                <RenderObject2D
                        texture="data/textures/gui/deploy/gfl_class_icon_{squad}.dds"
                        sizeX="28"
                        sizeY="28"
                        color="E3F6FD"
                    />
            </StaticImage>
            <StaticImage name="icon_{squad}_hover" origin="0 0" hidden="true">
                <RenderObject2D
                        texture="data/textures/gui/deploy/gfl_class_icon_{squad}.dds"
                        sizeX="28"
                        sizeY="28"
                        color="211e1d"
                    />
            </StaticImage>
            <StaticImage name="icon_{squad}_active" origin="0 0" hidden="false">
                <StaticImage name="#ClassBackgroundLeftBar">
                    <RenderObject2D
                            texture="data/textures/gui/deploy/gfl_class_icon_{squad}.dds"
                            sizeX="28"
                            sizeY="28"
                            color="E3F6FD"
                        />
                </StaticImage>
            </StaticImage>
        </Checkbox>

'''
    return template


def generate_tab_content(tab_num, unit, starting_slot, tab_content_y):
    """Generate content for a single tab in GIRL deploy screen."""

    classes = unit["classes"]
    count = unit["count"]
    flag_color = "E3F6FD"

    # Determine layout
    use_two_columns = count > 4
    width = 178 if use_two_columns else 380

    hidden = "false" if tab_num == 0 else "true"

    output = f'    <Item origin="8 {tab_content_y}" name="unit_tab{tab_num}" align="t" hidden="{hidden}">\n'

    # Generate class items
    slot_num = starting_slot
    for i, class_name in enumerate(classes):
        if use_two_columns:
            # Two column layout
            row = i // 2
            col = i % 2
            x_origin = -101 if col == 0 else 100
            y_origin = 0 + (row * -160)
        else:
            # Single column layout
            x_origin = 0
            y_origin = 0 + (i * -160)

        output += "\n"
        output += generate_class_item_girl(
            class_name,
            x_origin,
            y_origin,
            slot_num,
            width,
            flag_color,
            indent="        ",
        )
        slot_num += 1

    output += "\n    </Item> <!-- End Tab " + str(tab_num) + " Content -->\n\n"

    return output


def generate_girl_deploy(units, output_path):
    """Generate gfl_deploy_girl.xml with tabbed interface."""

    total_tabs = len(units)
    tabs_per_row = 5

    # Calculate number of tab containers needed (each holds up to 5 tabs)
    num_containers = (total_tabs + tabs_per_row - 1) // tabs_per_row

    # The first container should always be at the same screen position
    # Container 0 is at Y=0 within GIRL, so GIRL origin determines screen position
    # Keep GIRL at -312 so first container stays in same place
    # Additional containers stack below at Y=-72, Y=-144, etc.
    girl_origin_y = -312

    # Tab content starts 72px below the GIRL origin (after first container)
    # Additional containers add 72px each
    tab_content_start_y = -72 - ((num_containers - 1) * 72)

    output = f"""<GUIItems>
<EventActionBatch name="GAME_GUI_LOADTIME_ACTIONS">
    <Action type="Show" target="GFL-UNIT-GIRL" />
</EventActionBatch>

<Item name="GFL-UNIT-GIRL" origin="0 {girl_origin_y}" hidden="true" align="rt" sizeX="396">
    <OnOpen>
        <Action type="AddMeToParent" target="#unit_header" />
    </OnOpen>

"""

    # Generate each tab container
    for container_idx in range(num_containers):
        container_y = 0 - (container_idx * 72)

        # Calculate which tabs go in this container
        start_tab = container_idx * tabs_per_row
        end_tab = min(start_tab + tabs_per_row, total_tabs)

        output += f"""    <!-- Tab Container {container_idx} (tabs {start_tab}-{end_tab - 1}) -->
    <Item
            origin="0 {container_y}"
            name="girl_tab_menu_{container_idx}"
            align="rt"
            sizeX="396"
            sizeY="64"
            hidden="false"
        >
        <StaticImage name="tab_background" origin="0 0" align="r">
            <RenderObject2D
                    texture="data/textures/gui/square.tga"
                    sizeX="380"
                    sizeY="64"
                    color="211e1dcc"
                />
        </StaticImage>
        <StaticImage name="#ClassBackgroundLeftBar" origin="0 0" align="l">
            <RenderObject2D
                    texture="data/textures/gui/square.tga"
                    sizeX="8"
                    sizeY="64"
                    color="E3F6FD"
                />
        </StaticImage>

"""

        # Generate tabs for this container
        for tab_idx in range(start_tab, end_tab):
            output += generate_tab_button(
                tab_idx, units[tab_idx], total_tabs, container_idx
            )

        output += (
            "    </Item> <!-- End Tab Container " + str(container_idx) + " -->\n\n"
        )

    slot_counter = 0
    for i, unit in enumerate(units):
        output += generate_tab_content(i, unit, slot_counter, tab_content_start_y)
        slot_counter += unit["count"]

    output += "</Item> <!-- End GFL-UNIT-GIRL -->\n</GUIItems>\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)


def main():
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent

    unit_file = project_dir / "mod" / "units" / "gfl_unit.xml"
    deploy_output = project_dir / "mod" / "gui" / "gfl_deploy.xml"
    deploy_girl_output = project_dir / "mod" / "gui" / "gfl_deploy_girl.xml"

    print("=== Generating Deploy Screens ===\n")
    print(f"Reading units from: {unit_file}")

    units = extract_unit_data(unit_file)

    print(f"\nFound {len(units)} units:")
    for unit in units:
        layout = "2-column" if unit["count"] > 4 else "1-column"
        print(
            f"  {unit['name']}: {unit['count']} dolls ({layout}), color={unit['flag_color']}"
        )

    print(f"\nGenerating base deploy screen: {deploy_output}")
    generate_base_deploy(units, deploy_output)

    print(f"Generating GIRL deploy screen: {deploy_girl_output}")
    generate_girl_deploy(units, deploy_girl_output)


if __name__ == "__main__":
    main()
