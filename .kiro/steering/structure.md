# Project Structure

```
ai-content-tiktok/
├── src/                          # Main source code
│   ├── main.py                   # Orchestrator - TikTokNewsGenerator class
│   ├── crawler/
│   │   └── news_crawler.py       # NewsCrawler - Web scraping (VnExpress, TienPhong)
│   ├── processor/
│   │   ├── content_summarizer.py # ContentSummarizer - Qwen3:4B chunked summarization
│   │   ├── news_refiner.py       # NewsRefiner - Grammar/spelling refinement
│   │   ├── text_corrector.py     # TextCorrector - Diacritics correction
│   │   ├── text_normalizer.py    # TextNormalizer - Number/date normalization
│   │   ├── text_preprocessor.py  # TextPreprocessor - Text cleanup
│   │   └── subtitle_aligner.py   # SubtitleAligner - AI subtitle alignment
│   ├── media/
│   │   ├── tts_generator.py      # TTSGenerator - VieNeu-TTS (GPU)
│   │   ├── video_composer.py     # VideoComposer - Video composition with effects
│   │   ├── intro_renderer.py     # IntroTemplateRenderer - PowerPoint rendering
│   │   └── subtitle_generator.py # SubtitleGenerator - Whisper transcription
│   └── publisher/
│       └── social_publisher.py   # SocialPublisher - Upload preparation
├── templates/
│   └── intro_template.pptx       # PowerPoint intro templates
├── assets/                       # Static assets
│   ├── logo*.png                 # Logo variants
│   ├── background_music.mp3      # Background music
│   ├── typing.mp3                # Typing SFX
│   └── icon/                     # Social media icons
├── models/                       # Local ML models (optional)
│   ├── VieNeu-TTS/               # Local TTS model
│   ├── voice_model/              # Voice ONNX models
│   └── ...                       # Other models
├── output/                       # Generated outputs
│   ├── videos/                   # Final MP4 videos
│   ├── audio/                    # Generated audio files
│   ├── summaries/                # Text/JSON summaries
│   └── temp/                     # Temporary files (SRT, etc.)
├── requirements.txt              # Python dependencies
├── run.sh                        # Quick run script
└── architecture.md               # Architecture documentation
```

## Module Patterns

- Each module is a class with clear single responsibility
- Classes are initialized in `main.py` orchestrator
- Processing pipeline: Crawler → Processor → Media → Publisher

## Code Conventions

- Docstrings at module and class level
- Type hints for function parameters
- Print statements with emoji prefixes for progress (✓, ⚠, ❌)
- Error handling with fallback mechanisms
- Vietnamese text processing with regex patterns
