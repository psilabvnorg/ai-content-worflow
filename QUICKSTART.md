# Quick Start Guide 🚀

## 1. Run the Demo

```bash
# Activate virtual environment
source venv/bin/activate

# Run demo
python demo.py
```

Then paste a Vietnamese news article URL when prompted.

## 2. Example URLs to Try

### VnExpress
- Sports: `https://vnexpress.net/bong-da/...`
- Politics: `https://vnexpress.net/thoi-su/...`
- Economics: `https://vnexpress.net/kinh-doanh/...`

### Tien Phong
- Sports: `https://tienphong.vn/the-thao/...`
- News: `https://tienphong.vn/xa-hoi/...`

## 3. What Happens

```
Input URL
    ↓
Crawl Article (title, content, images)
    ↓
AI Summarization (VietAI/vit5)
    ↓
Text-to-Speech (Vietnamese male voice)
    ↓
Generate Subtitles
    ↓
Compose Video (Ken Burns effect)
    ↓
Output: output/videos/tiktok_news_YYYYMMDD_HHMMSS.mp4
```

## 4. Output Location

Videos are saved to: `output/videos/`

## 5. Customize

### Change Language
```python
generator = TikTokNewsGenerator(language="english")
```

### Use NGHI-TTS Model (Vietnamese)
```python
generator = TikTokNewsGenerator(
    language="vietnamese",
    tts_model_path="models/tts/deepman3909.onnx"
)
```

### Adjust Video Duration
Edit `src/processor/content_summarizer.py`:
```python
def summarize(self, article: dict, target_words: int = 120):
    # 120 words ≈ 45 seconds
    # Increase for longer videos
```

## 6. Troubleshooting

**Problem**: No images found
- **Solution**: Try a different article with more images

**Problem**: Video too short/long
- **Solution**: Adjust `target_words` in summarizer

**Problem**: TTS fails
- **Solution**: Check internet connection (edge-tts requires internet)

**Problem**: Video encoding fails
- **Solution**: Install ffmpeg: `sudo apt install ffmpeg`

## 7. Next Steps

- Upload video to TikTok manually
- Try different news categories
- Experiment with English articles
- Download NGHI-TTS models for better Vietnamese voices

## 8. File Structure

```
output/
├── videos/          # Final MP4 videos ✅
├── audio/           # Generated voice-overs
├── images/          # Downloaded article images
└── temp/            # Temporary files (subtitles)
```

## 9. Tips

- Use articles with 6-8 images for best results
- Longer articles = better summarization
- Check video in `output/videos/` folder
- Videos are TikTok-ready (9:16, 1080x1920)

---

**Need help?** Check README.md for detailed documentation.
