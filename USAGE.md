# Complete Usage Guide

## Installation Complete ✅

All packages have been installed in the virtual environment:
- ✅ PyTorch 2.9.1
- ✅ Transformers 4.57.3
- ✅ MoviePy 2.2.1
- ✅ Edge-TTS 7.2.7
- ✅ ONNX Runtime 1.23.2
- ✅ BeautifulSoup4, Requests, Pillow, OpenCV, etc.

## Three Ways to Use

### 1. Interactive Demo (Recommended for First Time)

```bash
source venv/bin/activate
python demo.py
```

**What it does:**
- Guides you through the entire process
- Shows progress for each step
- Provides detailed output information

### 2. Simple Test Script

```bash
source venv/bin/activate
python test_example.py
```

**What it does:**
- Quick test of the pipeline
- Minimal output
- Good for debugging

### 3. Direct Python API

```bash
source venv/bin/activate
python src/main.py
```

Or use in your own script:

```python
from src.main import TikTokNewsGenerator

# Initialize
generator = TikTokNewsGenerator(language="vietnamese")

# Generate video
video_path = generator.generate_video(
    news_url="https://vnexpress.net/your-article-url",
    output_name="my_custom_name"  # Optional
)

print(f"Video created: {video_path}")
```

## Step-by-Step Example

### Step 1: Find a News Article

Go to VnExpress or Tien Phong and copy an article URL:

**Example URLs:**
```
https://vnexpress.net/bong-da/...
https://tienphong.vn/the-thao/...
```

### Step 2: Run the Generator

```bash
source venv/bin/activate
python demo.py
```

### Step 3: Enter the URL

When prompted:
```
Enter news article URL: [paste your URL here]
```

### Step 4: Wait for Processing

The system will:
1. **Crawl** the article (5-10 seconds)
2. **Summarize** using AI (10-30 seconds, first time downloads model)
3. **Generate voice** (5-15 seconds)
4. **Create subtitles** (1-2 seconds)
5. **Compose video** (30-60 seconds)

### Step 5: Find Your Video

```
output/videos/tiktok_news_YYYYMMDD_HHMMSS.mp4
```

## Advanced Configuration

### Change Language to English

```python
generator = TikTokNewsGenerator(language="english")
```

### Use Custom TTS Model (Vietnamese)

1. Download model from [Google Drive](https://drive.google.com/drive/folders/1f_pCpvgqfvO4fdNKM7WS4zTuXC0HBskL)
2. Place in `models/tts/`
3. Use in code:

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
    # Change 120 to:
    # - 90 for ~35 seconds
    # - 150 for ~60 seconds
```

### Modify Video Resolution

Edit `src/media/video_composer.py`:

```python
def __init__(self, resolution=(1080, 1920), fps=30):
    # Change to:
    # - (720, 1280) for lower quality
    # - (1440, 2560) for higher quality
```

## Module-by-Module Usage

### 1. Crawler Only

```python
from src.crawler.news_crawler import NewsCrawler

crawler = NewsCrawler()
article = crawler.crawl_article("https://vnexpress.net/...")

print(article['title'])
print(article['images'])
```

### 2. Summarizer Only

```python
from src.processor.content_summarizer import ContentSummarizer

summarizer = ContentSummarizer(language="vietnamese")
script = summarizer.create_script(article)

print(script['script'])
```

### 3. TTS Only

```python
from src.media.tts_generator import TTSGenerator

tts = TTSGenerator(language="vietnamese")
tts.generate("Xin chào, đây là tin tức", "output.mp3")
```

### 4. Video Composer Only

```python
from src.media.video_composer import VideoComposer

composer = VideoComposer()
composer.create_video(
    images=['img1.jpg', 'img2.jpg'],
    audio_path='audio.mp3',
    subtitle_path='subs.srt',
    output_path='video.mp4',
    audio_duration=45.0
)
```

## Batch Processing

Process multiple articles:

```python
from src.main import TikTokNewsGenerator

urls = [
    "https://vnexpress.net/article1",
    "https://vnexpress.net/article2",
    "https://vnexpress.net/article3"
]

generator = TikTokNewsGenerator(language="vietnamese")

for idx, url in enumerate(urls):
    try:
        video = generator.generate_video(url, output_name=f"batch_{idx}")
        print(f"✓ Created: {video}")
    except Exception as e:
        print(f"✗ Failed: {url} - {e}")
```

## Performance Tips

### Speed Up Processing

1. **Use GPU** (if available):
   - PyTorch will automatically use CUDA if available
   - Check: `python -c "import torch; print(torch.cuda.is_available())"`

2. **Cache Models**:
   - Models are cached after first download
   - Located in `~/.cache/huggingface/`

3. **Reduce Video Quality**:
   - Lower resolution: `(720, 1280)`
   - Lower FPS: `fps=24`
   - Lower bitrate: `bitrate='4000k'`

### Reduce Memory Usage

1. **Process fewer images**:
   - Edit `news_crawler.py`: `img_tags[:8]` → `img_tags[:5]`

2. **Use smaller model**:
   - Change to `facebook/bart-large-cnn` (English only)

## Troubleshooting

### Issue: "No module named 'moviepy.editor'"

**Solution:**
```bash
source venv/bin/activate
pip install moviepy --upgrade
```

### Issue: "ffmpeg not found"

**Solution:**
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # macOS
```

### Issue: Video encoding fails

**Solution:**
```bash
# Install additional codecs
sudo apt install libx264-dev libavcodec-extra
```

### Issue: Out of memory

**Solution:**
- Process fewer images
- Use lower resolution
- Close other applications

### Issue: TTS fails

**Solution:**
- Check internet connection (edge-tts requires internet)
- Try: `pip install edge-tts --upgrade`

## Output Files

```
output/
├── videos/
│   └── tiktok_news_20260106_143022.mp4  ← Final video
├── audio/
│   └── tiktok_news_20260106_143022.mp3  ← Voice-over
├── images/
│   ├── vnexpress_0_1234.jpg             ← Downloaded images
│   ├── vnexpress_1_5678.jpg
│   └── ...
└── temp/
    └── tiktok_news_20260106_143022.srt  ← Subtitles
```

## API Integration (Future)

### TikTok Upload (Placeholder)

```python
from src.publisher.social_publisher import SocialPublisher

publisher = SocialPublisher(platform="tiktok")
metadata = {
    'title': 'Breaking News',
    'description': 'Latest updates...',
    'tags': ['news', 'viral']
}

# Currently shows upload info only
# Actual upload requires TikTok API credentials
result = publisher.upload_video(video_path, metadata)
```

## Best Practices

1. **Test with one article first** before batch processing
2. **Check image count** - articles with 6-8 images work best
3. **Review output** - adjust settings based on results
4. **Keep videos under 60 seconds** for TikTok
5. **Use descriptive output names** for organization

## Next Steps

- ✅ Generate your first video
- ✅ Experiment with different news categories
- ✅ Try English articles
- ✅ Customize video settings
- ✅ Set up batch processing
- ⏳ Download NGHI-TTS models (optional)
- ⏳ Integrate TikTok API (advanced)

---

**Questions?** Check README.md or architecture.md for more details.
