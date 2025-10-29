# Development Scripts Setup

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

## Running Scripts

After setup, you can run any script with:

```bash
python scripts/script_name.py --help
```

This will show you all available options and usage information for each script.

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
