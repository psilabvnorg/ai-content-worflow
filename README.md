# TikTok News Video Generator 🎬

Automated pipeline to convert Vietnamese news articles into TikTok-ready vertical videos (9:16) with AI voice-over, subtitles, and customizable PowerPoint intro templates.

## Features

- 📰 **Auto-crawl** news from VnExpress, Tien Phong
- 🤖 **AI Summarization** using qwen3-vl:4b via Ollama (chunked processing for long articles)
- 🎤 **GPU-accelerated TTS** with VieNeu-TTS (multiple Vietnamese voices)
- 🎬 **Pan effects** with blurred background for images/videos
- 💬 **Auto-subtitles** with Whisper + AI alignment
- 🎨 **PowerPoint Templates** - design custom intros in PowerPoint
- 🎵 **Background music** with typing SFX during intro
- 📄 **Summary Export** in text and JSON formats
- 📱 **TikTok-ready** 1080x1920 MP4 output (~60-90 seconds)

## System Requirements

- Python 3.10+
- NVIDIA GPU with CUDA support (RTX 5070 Ti or similar recommended)
- ~10GB disk space for models
- Ubuntu/Linux (tested on Ubuntu 22.04)

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

### 3. Install Ollama and qwen3-vl:4b (Summarization)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull qwen3-vl:4b model (~2.5GB)
ollama pull qwen3-vl:4b
```

Verify installation:
```bash
ollama list
# Should show: qwen3-vl:4b
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

# The model downloads automatically on first run (~140MB for base model)
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

## Model Summary

| Model | Purpose | Size | Location |
|-------|---------|------|----------|
| qwen3-vl:4b | News summarization | ~2.5GB | Ollama (~/.ollama/models) |
| VieNeu-TTS-0.3B | Vietnamese TTS | ~1.2GB | HuggingFace cache or models/VieNeu-TTS |
| Whisper base | Subtitle transcription | ~140MB | ~/.cache/whisper |

## Quick Start

```bash
# Basic usage
python src/main.py --url "https://vnexpress.net/..."

# With custom intro template
python src/main.py --url "https://vnexpress.net/..." --template "psi" --intro-duration 5

# Full video intro (no fade out)
python src/main.py --url "https://vnexpress.net/..." --template 0 --intro-duration none

# With custom voice
python src/main.py --url "https://vnexpress.net/..." --voice huong
```

## CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--url` | News article URL | (prompted) |
| `--image-dir` | Custom directory for images | (from article) |
| `--broll-dir` | Directory with B-roll videos (.mp4, .mov) | None |
| `--voice` | Voice name (see table below) | binh |
| `--template` | Intro template (slide name or index from PowerPoint) | None |
| `--intro-duration` | Intro duration in seconds, or "none" for full video | 3 |
| `--output` | Output video name (without extension) | auto-generated |

## PowerPoint Intro Templates

Design custom intro templates in `templates/intro_template.pptx`:

1. Each slide = one intro template (e.g., slide 1 for channel A, slide 2 for channel B)
2. Add `{{TITLE_HERE}}` text box for dynamic title insertion
3. Article image is placed at the bottom layer automatically
4. All styling (transparency, colors, icons) is preserved

```bash
# Use slide by name (searches slide text)
python src/main.py --url "..." --template "psi"

# Use slide by index (0-based)
python src/main.py --url "..." --template 0
```

## Available Voices

| Voice | Gender | Region |
|-------|--------|--------|
| binh, tuyen | Male | Northern |
| nguyen, son, vinh | Male | Southern |
| huong, ly, ngoc | Female | Northern |
| doan, dung | Female | Southern |

## Project Structure

```
ai-content-tiktok/
├── src/
│   ├── crawler/news_crawler.py       # Web scraping
│   ├── processor/
│   │   ├── content_summarizer.py     # qwen3-vl:4b chunked summarization
│   │   ├── news_refiner.py           # Grammar/spelling refinement
│   │   ├── text_corrector.py         # Diacritics correction
│   │   └── subtitle_aligner.py       # AI subtitle alignment
│   ├── media/
│   │   ├── tts_generator.py          # VieNeu-TTS (GPU)
│   │   ├── video_composer.py         # Video composition
│   │   ├── intro_renderer.py         # PowerPoint template rendering
│   │   └── subtitle_generator.py     # Whisper transcription
│   └── main.py                       # Main orchestrator
├── templates/intro_template.pptx     # PowerPoint intro templates
├── assets/                           # Logo, icons, music, SFX
├── models/                           # Local model files (optional)
│   └── VieNeu-TTS/                   # Local TTS model
└── output/                           # Generated videos, audio, summaries
```

## Processing Pipeline

```
1. Crawl Article → 2. Chunk & Summarize (qwen3-vl:4b) → 3. Refine Text →
4. Final Cleanup → 5. Generate TTS (GPU) → 6. Whisper Transcription →
7. AI Subtitle Alignment → 8. Render Intro (PowerPoint) → 9. Compose Video
```

## Text Processing

The summarizer automatically handles:
- **Numbers**: `1.890` → `1890` (Vietnamese thousand separator)
- **Dates**: `8/1` → `mùng 8 tháng 1`
- **Stuck words**: `chứng khoánkhởi` → `chứng khoán khởi`
- **Incomplete sentences**: Ensures proper ending punctuation

## Output Specifications

- **Resolution**: 1080x1920 (9:16 vertical)
- **Format**: MP4 (H.264 codec)
- **Frame Rate**: 30 FPS
- **Duration**: ~60-90 seconds
- **Audio**: AAC codec
- **Effects**: Pan left-to-right with blurred background

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
# Manual download
python -c "import whisper; whisper.load_model('base')"

# Or use smaller model
python -c "import whisper; whisper.load_model('tiny')"
```

### Summary too short or cut off
- The chunked summarizer splits long articles into parts
- Each chunk is summarized separately then combined
- Target is ~350 words (~60-90 seconds of speech)

## License

Open source - Free for commercial use

## Credits

- **Summarization**: qwen3-vl:4b via Ollama
- **TTS**: VieNeu-TTS (GPU-accelerated Vietnamese)
- **Transcription**: OpenAI Whisper
- **Video**: MoviePy

---

Made with ❤️ for Vietnamese content creators
