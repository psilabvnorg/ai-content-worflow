# TikTok News Video Generator 🎬

Automated pipeline to convert Vietnamese news articles into TikTok-ready vertical videos (9:16) with AI voice-over, subtitles, and customizable PowerPoint intro templates.

## Table of Contents
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- 📰 **Auto-crawl** news from VnExpress, Tien Phong
- 🤖 **AI Summarization** using Qwen3:4B via Ollama (chunked processing for long articles)
- 🎤 **GPU-accelerated TTS** with VieNeu-TTS (multiple Vietnamese voices)
- 🎬 **Pan effects** with blurred background for images/videos
- 💬 **Auto-subtitles** with Whisper word-level timing + intelligent text alignment
- 🎨 **PowerPoint Templates** - design custom intros in PowerPoint
- 🎵 **Background music** with typing SFX during intro
- 📄 **Summary Export** in text and JSON formats
- 📱 **TikTok-ready** 1080x1920 MP4 output (~60-90 seconds)

---

## System Requirements

- Python 3.10+
- NVIDIA GPU with CUDA support (RTX 5070 Ti or similar recommended)
- ~10GB disk space for models
- Ubuntu/Linux (tested on Ubuntu 22.04)

---

## Installation

### 1. Clone and Setup Environment

```bash
git clone <repo>
cd ai-content-tiktok

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Install System Dependencies

```bash
# FFmpeg for audio/video processing
sudo apt install ffmpeg

# espeak-ng for Vietnamese phonemization (required by VieNeu-TTS)
sudo apt install espeak-ng

# LibreOffice for PowerPoint template rendering
sudo apt install libreoffice
```

### 3. Install Ollama and Qwen3:4B (Summarization)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull Qwen3:4B model (~2.5GB)
ollama pull qwen3:4b
```

Verify installation:
```bash
ollama list
# Should show: qwen3:4b
```

### 4. Install VieNeu-TTS Model (Text-to-Speech)

```bash
# Install vieneu package
pip install vieneu

# The model will auto-download on first run, or manually download:
python -c "
from vieneu import Vieneu
tts = Vieneu(backbone_repo='pnnbao-ump/VieNeu-TTS-0.3B')
print('VieNeu-TTS downloaded successfully')
"
```

For local model (faster loading):
```bash
# Clone to models directory
git lfs install
git clone https://huggingface.co/pnnbao-ump/VieNeu-TTS models/VieNeu-TTS
```

### 5. Install Whisper Model (Subtitle Transcription)

```bash
# Install openai-whisper
pip install openai-whisper

# The model downloads automatically on first run
# System will try base model first (~140MB), then fall back to smaller models if GPU memory is limited
# Or pre-download:
python -c "import whisper; whisper.load_model('base')"
```

### 6. Verify GPU Setup

```bash
python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')
"
```

---

## Quick Start

```bash
# Basic usage
python src/main.py --url "https://vnexpress.net/..."

# With custom intro template (separate 5-second intro with fade out)
python src/main.py --url "https://vnexpress.net/..." --template "psi" --intro-duration 5

# Intro overlay mode (intro stays as transparent overlay for entire video)
python src/main.py --url "https://vnexpress.net/..." --template 0 --intro-duration none

# With custom voice
python src/main.py --url "https://vnexpress.net/..." --voice huong
```

### CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--url` | News article URL | (prompted) |
| `--image-dir` | Custom directory for images | (from article) |
| `--broll-dir` | Directory with B-roll videos (.mp4, .mov) | None |
| `--voice` | Voice name (see table below) | binh |
| `--template` | Intro template (slide name or index from PowerPoint) | None |
| `--intro-duration` | Intro duration in seconds (separate clip with fade), or "none" for overlay mode (stays entire video) | 3 |
| `--output` | Output video name (without extension) | auto-generated |

### Available Voices

| Voice | Gender | Region |
|-------|--------|--------|
| binh, tuyen | Male | Northern |
| nguyen, son, vinh | Male | Southern |
| huong, ly, ngoc | Female | Northern |
| doan, dung | Female | Southern |

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    TikTokNewsGenerator                      │
│                   (Main Orchestrator)                       │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
             ▼                                ▼
    ┌────────────────┐              ┌────────────────┐
    │ NewsProcessor  │              │ MediaGenerator │
    │   (core.py)    │              │   (media.py)   │
    └────────────────┘              └────────────────┘
             │                                │
             ├─ Crawling                      ├─ TTS (VieNeu)
             ├─ Summarization (Qwen3:4B)     ├─ Subtitles (Whisper)
             ├─ Text Correction              ├─ Video Composition
             └─ Text Refinement              └─ PowerPoint Rendering
```

### Processing Pipeline

```
1. Crawl Article → 2. Chunk & Summarize (Qwen3:4B) → 3. Refine Text →
4. Final Cleanup → 5. Generate TTS (GPU) → 6. Whisper Word-Level Timing →
7. Intelligent Subtitle Alignment → 8. Render Intro (PowerPoint) → 9. Compose Video
```

### Subtitle Synchronization

The subtitle system uses a hybrid approach for perfect timing:

1. **Whisper** extracts precise word-level timestamps from audio (uses base model with automatic fallback to smaller models if GPU memory is limited)
2. **Corrected script** provides accurate Vietnamese text (no transcription errors)
3. **Intelligent alignment** maps corrected words to Whisper timing using:
   - Direct word matching (exact matches)
   - Fuzzy matching (similar words)
   - Proportional timing fallback (when no match found)

This ensures subtitles are perfectly synchronized with voice-over while displaying correct Vietnamese text.

---

## Project Structure

```
ai-content-tiktok/
├── src/                          # Main source code (3 core modules)
│   ├── __init__.py               # Package marker
│   ├── core.py                   # NewsProcessor - Crawling, summarization, text processing
│   ├── media.py                  # MediaGenerator - TTS, subtitles, video composition
│   └── main.py                   # TikTokNewsGenerator - Main orchestrator
│
├── templates/                    # PowerPoint templates
│   └── intro_template.pptx       # Multi-slide intro templates
│
├── assets/                       # Static assets
│   ├── logo*.png                 # Logo variants
│   ├── background_music.mp3      # Background music
│   ├── typing.mp3                # Typing SFX
│   └── icon/                     # Social media icons
│
├── models/                       # ML models (optional local storage)
│   ├── VieNeu-TTS/               # Vietnamese TTS model
│   ├── voice_model/              # ONNX voice models
│   └── ...                       # Other models
│
├── output/                       # Generated outputs
│   ├── videos/                   # Final MP4 videos
│   ├── audio/                    # Generated audio files
│   ├── summaries/                # Text and JSON summaries
│   └── temp/                     # Temporary files (SRT, etc.)
│
├── requirements.txt              # Python dependencies
├── run.sh                        # Quick run script
└── README.md                     # This file
```

### Module Responsibilities

#### `src/core.py` - NewsProcessor
**Purpose:** News article processing and text manipulation

**Key Methods:**
- `crawl_article(url)` - Web scraping from VnExpress/TienPhong
- `summarize(article, target_words)` - LLM-based summarization with chunking
- `correct_text(text)` - Vietnamese spelling/diacritics correction
- `refine_text(text)` - Grammar and style refinement

#### `src/media.py` - MediaGenerator
**Purpose:** Media generation (audio, subtitles, video)

**Key Methods:**
- `generate_audio(text, output_path)` - TTS synthesis
- `generate_subtitles(audio_path, output_path, script)` - Whisper + alignment
- `compose_video(...)` - Video composition with effects

#### `src/main.py` - TikTokNewsGenerator
**Purpose:** Pipeline orchestration and CLI

**Key Methods:**
- `generate_video(news_url, output_name)` - Complete pipeline

---

## Configuration

### Model Summary

| Model | Purpose | Size | Location |
|-------|---------|------|----------|
| Qwen3:4B | News summarization | ~2.5GB | Ollama (~/.ollama/models) |
| VieNeu-TTS-0.3B | Vietnamese TTS | ~1.2GB | HuggingFace cache or models/VieNeu-TTS |
| Whisper base | Subtitle transcription | ~140MB | ~/.cache/whisper |

### Video Settings

```python
resolution = (1080, 1920)  # 9:16 aspect ratio
fps = 30
bitrate = '6000k'
codec = 'libx264'
audio_codec = 'aac'
```

### PowerPoint Intro Templates

Design custom intro templates in `templates/intro_template.pptx`:

1. Each slide = one intro template (e.g., slide 1 for channel A, slide 2 for channel B)
2. Add `{{TITLE_HERE}}` text box for dynamic title insertion
3. Article image is placed at the bottom layer automatically
4. All styling (transparency, colors, icons) is preserved

**Intro Modes:**
- **Separate intro** (`--intro-duration 3`): Intro plays as separate clip with fade out, then content starts
- **Overlay mode** (`--intro-duration none`): Intro stays as transparent overlay at top while images/videos transition underneath for entire video

```bash
# Use slide by name (searches slide text)
python src/main.py --url "..." --template "psi"

# Use slide by index (0-based)
python src/main.py --url "..." --template 0

# Overlay mode - intro stays entire video
python src/main.py --url "..." --template "psi" --intro-duration none
```

### Text Processing

The summarizer automatically handles:
- **Numbers**: `1.890` → `1890` (Vietnamese thousand separator)
- **Dates**: `8/1` → `mùng 8 tháng 1`
- **Stuck words**: `chứng khoánkhởi` → `chứng khoán khởi`
- **Incomplete sentences**: Ensures proper ending punctuation

---

## Troubleshooting

### Ollama connection failed
```bash
# Start Ollama service
ollama serve

# Check if running
curl http://localhost:11434/api/tags
```

### TTS too slow / No GPU
```bash
# Check CUDA
python -c "import torch; print(torch.cuda.is_available())"

# If False, reinstall PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### espeak-ng not found
```bash
sudo apt install espeak-ng
```

### PowerPoint template not rendering
```bash
# Install LibreOffice
sudo apt install libreoffice

# Test conversion
libreoffice --headless --convert-to png templates/intro_template.pptx
```

### Whisper model download fails
```bash
# Manual download (base model - good balance of accuracy and speed)
python -c "import whisper; whisper.load_model('base')"

# System automatically falls back to smaller models (small, tiny) if GPU memory is limited
# Or force CPU mode if needed
python -c "import whisper; whisper.load_model('base', device='cpu')"
```

### Summary too short or cut off
- The chunked summarizer splits long articles into parts
- Each chunk is summarized separately then combined
- Target is ~350 words (~60-90 seconds of speech)

---

## Performance

### Processing Time
- Crawling: ~2-5 seconds
- Summarization: ~10-30 seconds (depends on article length)
- TTS: ~5-10 seconds
- Subtitles: ~10-20 seconds
- Video composition: ~30-60 seconds
- **Total:** ~1-2 minutes per video

### GPU Usage
- **VieNeu-TTS:** Primary GPU user (CUDA required for best quality)
- **Whisper:** GPU-accelerated (falls back to CPU if OOM)
- **Text Correction:** GPU-accelerated (ProtonX model)

---

## Output Specifications

- **Resolution**: 1080x1920 (9:16 vertical)
- **Format**: MP4 (H.264 codec)
- **Frame Rate**: 30 FPS
- **Duration**: ~60-90 seconds
- **Audio**: AAC codec
- **Effects**: Pan left-to-right with blurred background

---

## License

Open source - Free for commercial use

## Credits

- **Summarization**: Qwen3:4B via Ollama
- **TTS**: VieNeu-TTS (GPU-accelerated Vietnamese)
- **Transcription**: OpenAI Whisper (adaptive model selection)
- **Video**: MoviePy

---

Made with ❤️ for Vietnamese content creators
