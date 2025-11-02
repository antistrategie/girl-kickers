# Adding a New Doll

This guide covers the complete process for adding a new doll to the mod. The process involves creating XML entries across multiple files and using automation scripts to generate deployment screens and GIRL unit variants.

**Prerequisites:** This guide assumes all non-XML assets (3D models, textures, audio files) are already created. For information on creating these assets, see the separate asset creation documentation.

## Naming Conventions

All naming follows strict patterns that must be adhered to for the automation scripts to work correctly:

- **Entity Names**: `{SQUAD}-{WEAPON}`
  - Examples: `ELMOCE-DP12`, `DEFY-AN94`, `CAFE-WA2000`

- **Unit Names**: `GFL-UNIT-{SQUAD}`
  - Examples: `GFL-UNIT-ELMOCE`, `GFL-UNIT-DEFY`, `GFL-UNIT-CAFE`

- **Class Names**: `GFL-DOLL-{WEAPON}`
  - Examples: `GFL-DOLL-DP12`, `GFL-DOLL-AN94`, `GFL-DOLL-WA2000`

- **Weapon Names**: `GFL-WEAP-{WEAPON}`
  - Examples: `GFL-WEAP-DP12`, `GFL-WEAP-AN94`, `GFL-WEAP-WA2000`

- **Voice Pack Names**: `{CharacterName}-Voice`
  - Examples: `Helen-Voice`, `Alva-Voice`, `Lewis-Voice`

- **Localisation Keys**:
  - `@DOLL-{WEAPON}-NAME` - Character name
  - `@DOLL-{WEAPON}-DESC` - Character description
  - `@WEAP-{WEAPON}-NAME` - Weapon name
  - `@WEAP-{WEAPON}-DESC` - Weapon description

## Required Assets

Before starting XML work, ensure these assets exist in the correct locations:

### 1. Models

**Doll Model** (in `/mod/models/dolls/`):
- `{weapon}.khm` - 3D model file
- `{weapon}.dds` - Full-size texture

Example: `dp12.khm`, `dp12.dds`

**Signature Weapon** (in `/mod/models/signatures/`):
- `{weapon}.khm` - Weapon model
- `{weapon}.dds` - Weapon texture
- `{weapon}_ui.dds` - UI icon for weapon

Example: `dp12.khm`, `dp12.dds`, `dp12_ui.dds`

### 2. Textures

**Portraits** (in `/mod/textures/portraits/`):
- `gfl_{weapon}.dds` - Small portrait
- `gfl_{weapon}_large.dds` - Large portrait

Example: `gfl_dp12.dds`, `gfl_dp12_large.dds`

### 3. Audio

**Voice Files** (in `/mod/sounds/voice/{CharacterName}/`):
- Create a directory named after the character (e.g., `Helen`, `Lewis`)
- Voice files should be processed WAV files with radio effect applied
- See [Voice Lines](#7-voice-lines) for processing instructions

## XML Files to Modify

The following XML files require manual entries when adding a new character.

### 1. Equipment - Weapon Definition

**File:** `/mod/equipment/gfl_weapons.xml`

Add two entries for each weapon:

#### A. Bind Definition
Maps the weapon to compatible ammunition and attachments.

#### B. Firearm Definition
Defines weapon statistics, behaviour, rendering, and sounds.

> [!IMPORTANT]
> Different weapon types have different attributes (sights, animation sets, mobility modifiers, etc.). Always reference an existing weapon of the same type to ensure all attributes are correct.

Reference examples:
- ARs: `GFL-WEAP-AN94`
- SMGs: `GFL-WEAP-UMP45`
- DMRs: `GFL-WEAP-WA2000` (Note: sniper rifles don't exist in Door Kickers (as an equipable gun), so they're set as DMRs)
- Shotguns: `GFL-WEAP-DP12`
- LMGs: `GFL-WEAP-LEWIS`

**Key fields to customise:**
- `name` - Must follow `GFL-WEAP-{WEAPON}` pattern
- `tooltip` and `description` - Reference localisation keys
- `img` - Path to weapon UI icon (`data/models/signatures/{weapon}_ui.dds`)
- `model` and `diffuseTex` - Paths to weapon 3D model and texture
- `AttackTypes` - Custom attack patterns (see next section)

### 2. Equipment - Class Bindings

**File:** `/mod/equipment/gfl_binds.xml`

Define what equipment the doll class can use. Each `<Bind>` entry specifies all items that can be equipped by the doll class.

Add a `<Bind to="GFL-DOLL-{WEAPON}">` entry containing the doll's signature weapon and all compatible equipment (armour variants, pistols, utilities, gear, NVG, and special items).

Reference existing bindings for similar weapon types to ensure all appropriate equipment is included.

### 3. Equipment - Attack Types and Ammunition

**Files:** `/mod/equipment/gfl_attacktypes.xml` and `/mod/equipment/gfl_ammo.xml`

#### Attack Types

If your weapon requires custom attack behaviour (e.g., burst fire, double shots, different behaviour at various ranges), define attack types in `gfl_attacktypes.xml`. These are referenced in the weapon's `<AttackTypes>` section.

> [!TIP]
> Simple weapons may not need custom attack types. Check the base game files first (in the Door Kickers installation directory) to see if suitable attack types already exist before creating new ones.

Reference examples:
- Burst fire: `DP12_DoubleShotClose`, `DP12_DoubleShotMed`
- Standard patterns: Look at existing definitions for similar weapons

Each attack type defines:
- Aim time ranges
- Number of shots (min/max)
- Accuracy modifiers
- Crit chance
- Reset time between bursts

#### Ammunition

If your weapon uses a unique calibre or ammunition type, you may need to add ammunition definitions in `gfl_ammo.xml`.

> [!IMPORTANT]
> Check the base game files first to see if suitable ammunition types already exist before creating new ones. Most weapons can use existing ammunition types from either the mod or base game.

### 4. Entity Definition

**File:** `/mod/entities/gfl_humans.xml`

Add an entity for the character to their squad. The entity defines the character's physical properties, equipment loadout, and links to their unit/class.

**Key fields to customise:**
- `name` - Must follow `{SQUAD}-{WEAPON}` pattern (e.g., `ELMOCE-DP12`)
- `model` and `diffuseTex` - Paths to character model and texture
- `unit` - Squad unit name (e.g., `GFL-UNIT-ELMOCE`)
- `class` - Class name following `GFL-DOLL-{WEAPON}` pattern
- `portrait` - Path to small portrait texture
- `voicePack` - Voice pack name (e.g., `Helen-Voice`)
- `Equipment` - List of items the character starts with

> [!NOTE]
> Squad leaders and breachers (anyone with a shotgun) should have `<Item name="GFL_FeetOfTitanium" />` instead of `FeetOfSteel`. This allows them to kick down locked doors in one kick.

Reference examples grouped by squad:
- CAFE: `CAFE-WA2000`, `CAFE-M1903`
- DEFY: `DEFY-AN94`, `DEFY-AK12`
- ELMOCE: `ELMOCE-DP12`, `ELMOCE-SABRINA`
- GROZA: `GROZA-OTS14`, `GROZA-VEPLEY`
- 404: `404-G11`, `404-HK416`

> [!IMPORTANT]
> The entity name pattern `{SQUAD}-{WEAPON}` is critical for the generation scripts to work correctly.

### 5. Unit - Class Definition

**File:** `/mod/units/gfl_unit.xml`

Add a class definition to the appropriate squad's unit. Classes define the character type that appears in the deployment screen.

Find the `<Unit name="GFL-UNIT-{SQUAD}">` section for your squad and add a new `<Class>` entry.

**Key fields to customise:**
- `name` - Must follow `GFL-DOLL-{WEAPON}` pattern
- `nameUI` - Reference to localisation key for character name
- `description` - Reference to localisation key for character description
- `numSlots` - Number of deployment slots (typically `1`)
- `supply` - Supply cost (typically `100`)
- `iconTex` - Class icon texture path
- `upgrades` - Available upgrades (typically `BH_Defence1, BH_Offence1, BH_Defence2, BH_Offence2`)
- `maxUpgradeable` - Maximum number of upgrades (typically `2`)

### 6. Unit - Portrait Entries

**File:** `/mod/units/gfl_human_identities.xml`

Add portrait entries for **both** the squad unit and the GIRL unit. This ensures the character appears correctly in both deployment screens.

Add two `<Portrait>` entries:

```xml
<Portrait
    tex="data/textures/portraits/gfl_{weapon}.dds"
    unit="GFL-UNIT-{SQUAD}"
    class="GFL-DOLL-{WEAPON}"
    gender="0"
    customName="{CHARACTER_NAME}"
/>
<Portrait
    tex="data/textures/portraits/gfl_{weapon}.dds"
    unit="GFL-UNIT-GIRL"
    class="GFL-DOLL-{WEAPON}"
    gender="0"
    customName="{CHARACTER_NAME}"
/>
```

> [!NOTE]
> The character name in `customName` should be in all caps.

### 7. Voice Lines

**File:** `/mod/sounds/gfl_voice_lines_{squad}.xml`

#### Step 1: Process Voice Files

Before creating the voice pack XML, process your raw voice files using the voice processing script:

```bash
python scripts/process_voice.py /path/to/raw/audio/directory CharacterName
```

**Example:**
```bash
python scripts/process_voice.py /home/justin/dev/github.com/beanpuppy/gfl2-voice/JP/VO_Lewis_JP Lewis
```

> [!NOTE]
> You can get raw voice files from the [gfl2-voice](https://github.com/beanpuppy/gfl2-voice) repository. This mod uses Japanese voice lines.

> [!IMPORTANT]
> Use the Japanese romanisation of character names as they appear in the voice file directories, not the English localised names. For example, Makiatto is called "Macqiato" in the Japanese files, so the directory should be `Macqiato` and the voice pack should be `Macqiato-Voice`.

This script will:
- Apply a radio/walkie-talkie effect to the audio
- Shorten filenames by removing redundant prefixes
- Output processed files to `/mod/sounds/voice/{CharacterName}/`

**Next:** Generate transcriptions of the voice lines:

```bash
python scripts/transcribe_voices.py
```

This creates a `_trans.txt` file for all directories that don't have one, showing what each voice line says (machine translated, so far from perfect). This is essential for matching them to appropriate game events if you don't speak Japanese.

#### Step 2: Create Voice Pack XML

Create a voice pack that maps game events to voice files. Add a new `<Pack>` entry to the appropriate squad's voice lines file.

The voice pack maps various in-game events (combat, movement, status changes) to audio files:

**Common voice events:**
- `VOX_DYING` - Death/dying sounds (typically uses `HittedLast` files)
- `VOX_INJURED` - Hit/damage sounds (typically uses `Hitted` files)
- `VOX_TRPR_TANGODOWN` - Kill confirmation
- `VOX_TRPR_GO_GO_GO` - Battle start/movement commands
- `VOX_TRPR_MOVING` - Movement acknowledgement
- `VOX_TRPR_ROGER` - Command acknowledgement
- `VOX_TRPR_CLEAR` - Mission complete
- `VOX_WARN_GRENADE` - Grenade warning
- Many more tactical callouts...

**Reference examples:**
- Look at existing voice packs in the same squad file to see the complete structure
- Voice file paths must exactly match the files in `/mod/sounds/voice/{CharacterName}/`
- Use `data/sounds/voice/` prefix for all paths

> [!TIP]
> Use the `_trans.txt` file in your character's voice directory to help match voice lines to appropriate game events based on their content.

#### Step 3: Validate and Clean Up

After creating the voice pack XML, validate that all voice file paths are correct:

```bash
python scripts/validate_voice_files.py
```

This will check that all voice files referenced in the XML actually exist and report any missing files.

Once validation passes and you've checked the voices in-game, clean up any unused voice files:

```bash
python scripts/cleanup_unused_sounds.py
```

This removes voice files that exist in the directories but aren't referenced in any voice pack XML, keeping the mod at an acceptable file size.

### 8. Localisation

**File:** `/mod/localization/gfl_game.txt`

Add localisation strings for the character and weapon. These are referenced throughout the XML files.

Required entries:
```
@DOLL-{WEAPON}-NAME=CHARACTER NAME
@DOLL-{WEAPON}-DESC=Character description/backstory
@WEAP-{WEAPON}-NAME=Weapon Name
@WEAP-{WEAPON}-DESC=Weapon description
```

Example:
```
@DOLL-DP12-NAME=HELEN
@DOLL-DP12-DESC=In the chaos of Griffin's disbandment, Helen accepted a corporate position at Mangi Security Service while still looking for the Commander...
@WEAP-DP12-NAME=DP-12
@WEAP-DP12-DESC=The DP-12 is a bullpup double-barrel pump-action shotgun with dual magazine tubes...
```

## Generated Files (DO NOT EDIT MANUALLY)

The following files are automatically generated by scripts and should never be edited manually. Any manual changes will be overwritten the next time the scripts run.

- `/mod/entities/gfl_humans_girl.xml` - Generated by `generate_girls.py --entities`
- `/mod/units/gfl_unit_girl.xml` - Generated by `generate_girls.py --units`
- `/mod/gui/gfl_deploy.xml` - Generated by `generate_deploy.py`
- `/mod/gui/gfl_deploy_girl.xml` - Generated by `generate_deploy.py`

These files are created from the base definitions in `gfl_humans.xml`, `gfl_unit.xml`, and other source files.

## Automation Scripts

### Generation Scripts

#### `scripts/generate_girls.py`
Generates GIRL unit variants from base squad entities and units.

**Usage:**
```bash
python scripts/generate_girls.py            # Generate both entities and units
python scripts/generate_girls.py --entities # Generate only entities
python scripts/generate_girls.py --units    # Generate only units
```

**What it does:**
- Reads from `gfl_humans.xml` → generates `gfl_humans_girl.xml`
- Reads from `gfl_unit.xml` → generates `gfl_unit_girl.xml`
- Creates GIRL- prefixed entity variants
- Consolidates all classes into the GFL-UNIT-GIRL unit

#### `scripts/generate_deploy.py`
Generates deployment screen GUI from unit definitions.

**Usage:**
```bash
python scripts/generate_deploy.py
```

**What it does:**
- Reads from `gfl_unit.xml` and `gfl_unit_girl.xml`
- Generates `gfl_deploy.xml` (squad deployment screens)
- Generates `gfl_deploy_girl.xml` (tabbed GIRL deployment interface)
- Automatically handles layout (1-2 columns based on character count)
- Supports multiple tab rows (5 tabs per row maximum)

## TLDR - Complete Workflow

Follow these steps in order when adding a new character:

### 1: Asset Preparation

1. Ensure all models, textures, and portraits are in place (see Required Assets section)
2. Process voice files:
   ```bash
   python scripts/process_voice.py /path/to/raw/voices CharacterName
   python scripts/transcribe_voices.py
   ```

### 2: Manual XML Entries

3. Add weapon to `/mod/equipment/gfl_weapons.xml`
4. Add class bindings to `/mod/equipment/gfl_binds.xml`
5. Add attack types to `/mod/equipment/gfl_attacktypes.xml` (if needed)
6. Add ammunition to `/mod/equipment/gfl_ammo.xml` (if needed)
7. Add entity to `/mod/entities/gfl_humans.xml`
8. Add class to `/mod/units/gfl_unit.xml`
9. Add portraits to `/mod/units/gfl_human_identities.xml` (both squad and GIRL)
10. Add voice pack to `/mod/sounds/gfl_voice_lines_{squad}.xml`
11. Add localisation to `/mod/localization/gfl_game.txt`

### 3: Validation

12. Validate voice files:
    ```bash
    python scripts/validate_voice_files.py
    ```

### 4: Generation

13. Generate GIRL variants:
    ```bash
    python scripts/generate_girls.py
    ```

14. Generate deployment screens:
    ```bash
    python scripts/generate_deploy.py
    ```

### 5: Testing & Cleanup

15. Test in-game to verify everything works
16. Clean up unused voice files:
    ```bash
    python scripts/cleanup_unused_sounds.py
    ```
