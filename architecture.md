# TikTok News Video Generator - Architecture

## System Workflow

```
1. Content Crawler → 2. Content Processor → 3. Script Generator → 4. Media Pipeline → 5. Video Composer → 6. Output
```

### Detailed Flow:
1. **Content Crawler**: Scrape news articles + images from Vietnamese news sites
2. **Content Processor**: Summarize article to 45-second script (Vietnamese/English)
3. **TTS Generator**: Convert script to voice-over audio
4. **Media Pipeline**: Process images (resize, transitions, effects)
5. **Subtitle Generator**: Create synchronized subtitles from audio
6. **Video Composer**: Combine images + audio + subtitles → 9:16 MP4
7. **API Publisher** (Optional): Upload to TikTok/YouTube

## OOP Module Structure

```
src/
├── crawler/
│   └── news_crawler.py          # NewsCrawler class
├── processor/
│   └── content_summarizer.py    # ContentSummarizer class
├── media/
│   ├── tts_generator.py         # TTSGenerator class
│   ├── video_composer.py        # VideoComposer class
│   └── subtitle_generator.py    # SubtitleGenerator class
├── publisher/
│   └── social_publisher.py      # SocialPublisher class
└── main.py                      # Orchestrator
```

## Recommended Models (HuggingFace)

### 1. Text Summarization
- **Vietnamese**: `VietAI/vit5-base-vietnews-summarization` (optimized for Vietnamese news)
- **English**: `facebook/bart-large-cnn` (fast, accurate)
- **Multilingual**: `csebuetnlp/mT5_multilingual_XLSum` (supports both)

### 2. Text-to-Speech (TTS)

#### Vietnamese TTS: NGHI-TTS (Piper-based)
- **Repository**: https://github.com/nghimestudio/nghitts
- **Model Storage**: https://drive.google.com/drive/folders/1f_pCpvgqfvO4fdNKM7WS4zTuXC0HBskL
- **Available Male Voices**:
  - `deepman3909.onnx` (~60.6 MB) - Deep male voice
  - `vietthao3886.onnx` (~60.6 MB) - Việt Thảo voice
  - `Oryx` - Super deep male voice (new)
  - `Trấn Thành` - Celebrity voice (new)
- **Features**:
  - Based on Piper TTS (fine-tuned with 1,000+ Vietnamese audio samples)
  - ONNX format for fast inference (~5× real-time speed)
  - Automatic Vietnamese text processing (numbers, dates, currency, etc.)
  - Free, open-source, commercial use allowed
  - High-quality natural voices

#### English TTS:
- **Option 1**: `edge-tts` library (Microsoft Edge TTS) - free, high quality
- **Option 2**: `facebook/mms-tts-eng` (HuggingFace)

### 3. Why NGHI-TTS for Vietnamese?
- Specifically trained on Vietnamese celebrity voices
- Superior quality compared to generic multilingual models
- Fast inference with ONNX Runtime
- Handles Vietnamese text normalization automatically
- Free and production-ready
- Each model requires both `.onnx` and `.onnx.json` files

## Image-to-Video Strategy (45 seconds)

### Approach: Dynamic Ken Burns Effect + Transitions

**Timing Breakdown:**
- 45 seconds total
- 6-8 images from article
- Each image: 5-6 seconds display time
- Smooth transitions: 0.5-1 second between images

**Visual Effects:**
1. **Ken Burns Effect**: Slow zoom-in/pan on each image (adds dynamism)
2. **Transitions**: Fade, slide, or crossfade between images
3. **Text Overlay**: Highlight key points from script
4. **Background**: Subtle blur or gradient behind images if aspect ratio doesn't match

**Implementation:**
- Use `moviepy` for video composition
- Apply zoom/pan transformations to static images
- Sync image timing with voice-over pacing
- Add subtle background music (optional, low volume)

### Image Processing Pipeline:
```python
For each image:
1. Resize to 720x1280 (9:16)
2. Apply Ken Burns effect (zoom 1.0 → 1.1 over 5 seconds)
3. Add fade-in/fade-out transitions
4. Overlay subtitles at bottom
5. Composite all clips sequentially
```

## Technical Specifications

### Video Output:
- **Resolution**: 1080x1920 (1080p vertical)
- **Aspect Ratio**: 9:16
- **Format**: MP4 (H.264 codec)
- **Frame Rate**: 30 FPS
- **Bitrate**: 5000-8000 kbps (high quality)
- **Audio**: AAC codec, 128 kbps

### Performance Optimization:
- Use GPU acceleration for video encoding (if available)
- Cache downloaded images
- Parallel processing for image transformations
- Async web scraping for faster crawling

## Dependencies (requirements.txt)

```
beautifulsoup4==4.12.2
requests==2.31.0
transformers==4.36.0
torch==2.1.0
moviepy==1.0.3
Pillow==10.1.0
numpy==1.24.3

# Vietnamese TTS (NGHI-TTS)
onnxruntime==1.16.3
piper-phonemize==1.1.0
edge-tts==6.1.9  # For English TTS fallback
```

## Next Steps

1. Download Vietnamese TTS models from Google Drive (deepman3909.onnx + config)
2. Implement NewsCrawler class (scrape VnExpress, TienPhong)
3. Implement ContentSummarizer (Vietnamese news summarization)
4. Implement TTSGenerator with NGHI-TTS (ONNX Runtime + Piper)
5. Implement VideoComposer (moviepy + Ken Burns effect)
6. Implement SubtitleGenerator (sync with audio)
7. Create main orchestrator
8. Test end-to-end pipeline

### TTS Model Setup:
```bash
# Download from Google Drive:
# https://drive.google.com/drive/folders/1f_pCpvgqfvO4fdNKM7WS4zTuXC0HBskL

# Required files for each voice:
# - deepman3909.onnx
# - deepman3909.onnx.json

# Place in: models/tts/
```
