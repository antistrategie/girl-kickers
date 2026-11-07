#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["UnityPy==1.25.0", "lz4"]
# ///
"""Pull named textures out of the GFL2 CN client into scripts/sprites/.cache/.

The client's bundles are hash-named and XOR-encrypted over their first 32 KiB. An
AssetStudio asset map (JSON, built with the GirlsFrontline profile) says which bundle holds
each texture, so only those bundles are opened.

Paths differ per machine, so they come from flags, the environment, or the repo's gitignored
.env:

    GFL2_BUNDLES    .../GF2_Exilium_Data/LocalCache/Data/AssetBundles_Windows
    GFL2_ASSET_MAP  AssetStudio asset map JSON of those bundles

Run:
    uv run scripts/sprites/extract_art.py Avatar_Whole_SuomiSSR Avatar_Head_SuomiSSR
    uv run scripts/sprites/extract_art.py --dolls     # everything the doll and unit tables need
"""

import argparse
import json
import ntpath
import os
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache"
KNOWN = b"UnityFS\0\0\0\0\x075.x."


def load_dotenv():
    env = HERE.parents[1] / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep and not line.lstrip().startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip('"'))


def decrypt(data: bytes) -> bytes:
    if data[:7] == b"UnityFS":
        return data
    key = bytes(a ^ b for a, b in zip(data[:16], KNOWN))
    n = min(len(data), 32768)
    return bytes(data[i] ^ key[i % 16] for i in range(n)) + data[n:]


def wanted_from_tables():
    sys.path.insert(0, str(HERE))
    from tables import DOLLS, UNITS

    names = set()
    for d in DOLLS.values():
        names.add(f"Avatar_Whole_{d['gfl2']}")
        names.add(f"Avatar_Head_{d['gfl2']}")
    for u in UNITS.values():
        names.add(f"Img_CampLogo_{u['logo']}")
    return names


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "names", nargs="*", help="texture names, e.g. Avatar_Whole_SuomiSSR"
    )
    ap.add_argument(
        "--dolls", action="store_true", help="extract every texture tables.py refers to"
    )
    ap.add_argument("--bundles", default=os.environ.get("GFL2_BUNDLES"))
    ap.add_argument("--asset-map", default=os.environ.get("GFL2_ASSET_MAP"))
    ap.add_argument(
        "--force", action="store_true", help="re-extract textures already in the cache"
    )
    args = ap.parse_args()
    if not args.bundles or not args.asset_map:
        ap.error(
            "set GFL2_BUNDLES and GFL2_ASSET_MAP (or pass --bundles and --asset-map)"
        )

    names = set(args.names) | (wanted_from_tables() if args.dolls else set())
    if not names:
        ap.error("name some textures or pass --dolls")
    CACHE.mkdir(exist_ok=True)
    if not args.force:
        names = {n for n in names if not (CACHE / f"{n}.png").exists()}
    if not names:
        print("everything is cached")
        return

    entries = json.loads(Path(args.asset_map).read_text())
    if isinstance(entries, dict):
        entries = entries.get("Assets", entries)
    by_bundle = defaultdict(set)
    for e in entries:
        if e.get("Type") == "Texture2D" and e["Name"] in names:
            by_bundle[ntpath.basename(e["Source"])].add(e["Name"])
    missing = names - set().union(*by_bundle.values()) if by_bundle else names
    for n in sorted(missing):
        print(f"not in the asset map: {n}")

    import UnityPy

    for bundle, want in sorted(by_bundle.items()):
        env = UnityPy.Environment()
        env.load_file(decrypt((Path(args.bundles) / bundle).read_bytes()), name=bundle)
        for obj in env.objects:
            if obj.type.name != "Texture2D":
                continue
            tex = obj.read()
            if tex.m_Name in want:
                path = CACHE / f"{tex.m_Name}.png"
                tex.image.save(path)
                want.discard(tex.m_Name)
                print(f"wrote {path.relative_to(HERE.parents[1])}")
        for n in sorted(want):
            print(f"not found in {bundle}: {n} (may sit in a GFF pack piece)")


if __name__ == "__main__":
    main()
