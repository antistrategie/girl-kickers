# Development Scripts

## Prerequisites

This project uses [mise](https://mise.jdx.dev/) for managing Python and [uv](https://docs.astral.sh/uv/) for dependencies.

```bash
# Install mise if you don't have it
# See: https://mise.jdx.dev/getting-started.html

# Install Python and tools (from project root)
cd /path/to/girl-kickers
mise install

# Sync Python dependencies
uv sync
```

## Scripts

Check the scripts themselves for documentation on what they do and how to use them.

## GPU Support for Whisper Transcription (Optional but Recommended)

The `transcribe_voices.py` script uses OpenAI Whisper for speech-to-text, which can be very slow on CPU. GPU acceleration makes transcription significantly faster.

### For AMD GPUs (ROCm)

```bash
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2
```

### For NVIDIA 🤮 GPUs (CUDA)

```bash
uv pip install torch torchvision torchaudio
```

The transcription script will automatically detect and use your GPU if available.

## Sprites from GFL2 art

`scripts/sprites/` builds doll portraits (`gfl_<id>.dds`, `gfl_<id>_large.dds`), unit flag images (`gfl_<unit>_bg.dds`) and class icons (`gfl_class_icon_<unit>.dds`) from the GFL2 CN client's own art.

1. Point `GFL2_BUNDLES` (the client's `AssetBundles_Windows` folder) and `GFL2_ASSET_MAP` (an AssetStudio asset map JSON of it) at your install, in the environment or the repo's `.env`.
2. Add a row to `scripts/sprites/tables.py`: the doll's portrait id and her GFL2 art name (`SuomiSSR`, `LottaSR`), or a unit slug and its `Img_CampLogo_*` logo.
3. Run `mise run sprites`. Pass `--preview` to `make_sprites.py` for PNG copies in `scripts/sprites/.cache/preview/`.

The large portrait is placed by the face. If the detector misses (a cap or visor over the face), set `face_box` on the row. Extracted art is cached in `scripts/sprites/.cache/` (gitignored).
