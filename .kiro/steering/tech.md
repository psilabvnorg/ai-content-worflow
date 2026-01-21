# Tech Stack

## Language & Runtime

- Python 3.10+
- NVIDIA GPU with CUDA support (recommended for TTS)
- Ubuntu/Linux (tested on Ubuntu 22.04)

## Core Dependencies

### AI/ML Models
- **Qwen3:4B** via Ollama - News summarization
- **VieNeu-TTS** - Vietnamese text-to-speech (GPU-accelerated)
- **OpenAI Whisper** - Subtitle transcription

### Web Scraping
- `beautifulsoup4` - HTML parsing
- `requests` - HTTP client
- `lxml` - XML/HTML parser

### NLP & Summarization
- `transformers` - HuggingFace transformers
- `torch` - PyTorch (CUDA support)
- `sentencepiece` - Tokenization

### Text-to-Speech
- `vieneu` - Vietnamese TTS (primary)
- `edge-tts` - Microsoft Edge TTS (fallback)
- `soundfile` - Audio file I/O

### Video Processing
- `moviepy` - Video composition
- `Pillow` - Image processing
- `opencv-python` - Computer vision
- `numpy` - Numerical operations

### Subtitles
- `pysrt` - SRT file handling
- `openai-whisper` - Speech recognition

### Templates
- `python-pptx` - PowerPoint template rendering

## System Dependencies

```bash
# Required system packages
sudo apt install ffmpeg espeak-ng libreoffice
```

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the generator
python src/main.py --url "https://vnexpress.net/..." --voice binh

# With custom intro template
python src/main.py --url "..." --template "psi" --intro-duration 5

# Full video intro (no fade out)
python src/main.py --url "..." --template 0 --intro-duration none
```

## External Services

- **Ollama** - Local LLM server (http://localhost:11434)
  - Start with: `ollama serve`
  - Pull model: `ollama pull qwen3:4b`
