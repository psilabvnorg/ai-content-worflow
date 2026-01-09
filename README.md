# TikTok News Video Generator 🎬

Automated pipeline to convert Vietnamese/English news articles into TikTok-ready vertical videos (9:16) with voice-over and subtitles.

## Features

- 📰 **Auto-crawl** news from VnExpress, Tien Phong
- 🤖 **AI Summarization** using VietAI/vit5 for Vietnamese
- 🎤 **Text-to-Speech** with Vietnamese male voices (edge-tts)
- 🎬 **Ken Burns Effect** for dynamic image transitions
- 💬 **Auto-subtitles** synchronized with audio
- 🎨 **Intro Screen** with gradient overlay, logo, and title
- 📄 **Summary Export** in text and JSON formats
- 📱 **TikTok-ready** 1080x1920 MP4 output

## Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies (already done)
pip install -r requirements.txt
```

## Quick Start

### Method 1: Interactive Mode

```bash
python src/main.py
```

Then enter a news article URL when prompted.

### Method 2: Test Script

```bash
python test_example.py
```

### Method 3: Python API

```python
from src.main import TikTokNewsGenerator

# Initialize
generator = TikTokNewsGenerator(language="vietnamese")

# Generate video from URL
video_path = generator.generate_video(
    news_url="https://vnexpress.net/...",
    output_name="my_video"
)

print(f"Video created: {video_path}")
```

## Project Structure

```
ai-content-tiktok/
├── src/
│   ├── crawler/
│   │   └── news_crawler.py          # Web scraping
│   ├── processor/
│   │   └── content_summarizer.py    # AI summarization
│   ├── media/
│   │   ├── tts_generator.py         # Text-to-speech
│   │   ├── video_composer.py        # Video creation
│   │   └── subtitle_generator.py    # Subtitle generation
│   ├── publisher/
│   │   └── social_publisher.py      # Upload (placeholder)
│   └── main.py                      # Main orchestrator
├── models/tts/                      # TTS models (optional)
├── output/
│   ├── videos/                      # Final MP4 videos
│   ├── audio/                       # Generated audio
│   ├── images/                      # Downloaded images
│   └── temp/                        # Temporary files
├── requirements.txt
└── README.md
```

## Supported News Sites

- ✅ **VnExpress** (vnexpress.net)
- ✅ **Tien Phong** (tienphong.vn)

## Configuration

### Language

```python
# Vietnamese (default)
generator = TikTokNewsGenerator(language="vietnamese")

# English
generator = TikTokNewsGenerator(language="english")
```

### Vietnamese TTS Models (Optional)

Download NGHI-TTS models from [Google Drive](https://drive.google.com/drive/folders/1f_pCpvgqfvO4fdNKM7WS4zTuXC0HBskL):

1. Download `deepman3909.onnx` + `deepman3909.onnx.json`
2. Place in `models/tts/`
3. Use in code:

```python
generator = TikTokNewsGenerator(
    language="vietnamese",
    tts_model_path="models/tts/deepman3909.onnx"
)
```

**Note**: Currently using edge-tts (Microsoft) for Vietnamese as it's easier to set up. NGHI-TTS requires additional phonemization setup.

## Output Specifications

- **Resolution**: 1080x1920 (9:16 vertical)
- **Format**: MP4 (H.264 codec)
- **Frame Rate**: 30 FPS
- **Duration**: ~45 seconds
- **Audio**: AAC codec, 128 kbps
- **Subtitles**: Embedded in video

## Example Workflow

```
1. Input URL → 2. Crawl Article → 3. Summarize (AI) → 
4. Generate Voice → 5. Create Subtitles → 6. Compose Video → 
7. Output MP4
```

## Troubleshooting

### No images found
- Some articles may have lazy-loaded images
- Try a different article URL

### Audio/Video sync issues
- Adjust `words_per_sub` in `subtitle_generator.py`
- Modify `duration_per_image` calculation in `video_composer.py`

### TTS model not found
- Ensure edge-tts is installed: `pip install edge-tts`
- For NGHI-TTS, download models from Google Drive

## Future Enhancements

- [ ] Auto-upload to TikTok API
- [ ] YouTube Shorts support
- [ ] Background music integration
- [ ] Multiple voice options
- [ ] Batch processing
- [ ] Web UI interface

## License

Open source - Free for commercial use

## Credits

- **Summarization**: VietAI/vit5-base-vietnews-summarization
- **TTS**: Microsoft Edge TTS, NGHI-TTS (Piper-based)
- **Video**: MoviePy

---

Made with ❤️ for Vietnamese content creators
