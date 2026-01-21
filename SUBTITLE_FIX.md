# Subtitle Synchronization Fix

## Problem
Subtitles were not following the voice-over properly. The timing was off, causing text to appear at the wrong moments.

## Root Cause
The subtitle generation pipeline had a flawed alignment strategy:

1. **Whisper** provided accurate **timing** but sometimes inaccurate **text** (especially for Vietnamese)
2. The **corrected script** had accurate **text** but no timing information
3. The old approach tried to align AFTER subtitle generation using Qwen3:4b, which caused timing drift

## Solution
Implemented a **word-level alignment algorithm** that:

1. **Uses Whisper for timing only** - Gets precise word-level timestamps from audio
2. **Uses corrected script for text** - Displays the properly corrected Vietnamese text
3. **Aligns words intelligently** - Maps corrected words to Whisper timing using:
   - Direct word matching (when words are identical)
   - Fuzzy matching (when words are similar)
   - Proportional timing fallback (when no match found)

## Key Changes

### `src/media/subtitle_generator.py`
- Added `_align_words_with_timing()` method that uses dynamic programming to match corrected words with Whisper timing
- Simplified `generate_from_audio()` to pass corrected script directly
- Updated `_generate_karaoke_subtitles()` and `_generate_chunk_subtitles()` to use aligned word pairs
- Removed dependency on `SubtitleAligner` class (Qwen3:4b post-processing)

### `src/main.py`
- Removed Step 4.5 (Qwen3:4b alignment) - no longer needed
- Pass corrected script to subtitle generator using `set_original_script()`
- Subtitles now generated in one pass with proper timing

## How It Works

```
Audio File → Whisper → Word Timestamps
                           ↓
Corrected Script → Words → Align with Timestamps → Subtitles
```

1. Whisper transcribes audio and provides word-level timestamps
2. Corrected script is split into words
3. Algorithm matches corrected words to Whisper timestamps:
   - Exact match: Use Whisper timing directly
   - Similar match: Use Whisper timing with fuzzy matching
   - No match: Use proportional timing based on total duration
4. Generate subtitle chunks with corrected text and accurate timing

## Benefits
- ✅ Subtitles perfectly synchronized with voice-over
- ✅ Displays corrected Vietnamese text (no Whisper errors)
- ✅ Faster processing (no Qwen3:4b post-processing needed)
- ✅ More reliable (no dependency on LLM for alignment)
- ✅ Works for both karaoke and chunk modes

## Testing
Test with a news article to verify:
```bash
python src/main.py --url "https://vnexpress.net/..." --voice binh
```

Check that subtitles appear at the right time and display correct text.
