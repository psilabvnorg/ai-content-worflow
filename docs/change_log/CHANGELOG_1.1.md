# Changelog - Version 1.1

## Overview
This release includes major improvements to transcription accuracy, video composition for full-video intros, and bug fixes for the intro overlay system.

## Changes

### 1. Upgraded Transcription Model to Whisper Large V3
**File:** `src/media/subtitle_generator.py`, `requirements.txt`

- **Changed:** Replaced Whisper base model with `openai/whisper-large-v3` for significantly improved transcription accuracy
- **Benefit:** Better Vietnamese language recognition, more accurate word-level timestamps, and improved subtitle quality
- **Implementation:**
  - Updated model loading from `whisper.load_model("base")` to `whisper.load_model("large-v3")`
  - Added explicit `task="transcribe"` parameter for clarity
  - Updated requirements.txt to include `openai-whisper>=20231117`
- **Reference:** https://huggingface.co/openai/whisper-large-v3

### 2. Fixed Intro Overlay for Full Video Duration (`--intro-duration none`)
**File:** `src/media/video_composer.py`

- **Fixed:** When `--intro-duration` is set to `none`, the intro now correctly stays as an overlay for the entire video duration
- **Previous Behavior:** Intro was treated as a separate clip, causing it to disappear after the first segment
- **New Behavior:**
  - Intro is created as a semi-transparent overlay that stays on top throughout the video
  - Images and videos transition normally underneath the intro overlay
  - Intro position remains fixed at the top of the screen
- **Implementation:**
  - Added `_create_intro_overlay()` method for creating persistent intro overlays
  - Added `_create_fallback_intro_overlay()` method for fallback overlay rendering
  - Modified `create_video()` to detect full-video intro mode and composite overlay on top of video
  - Intro overlay uses `CompositeVideoClip` to layer on top of content clips

### 3. Fixed Image and Video Transitions with Full Video Intro
**File:** `src/media/video_composer.py`

- **Fixed:** Images now properly transition with pan effects when `--intro-duration none` is used
- **Fixed:** B-roll videos now play correctly alongside image transitions
- **Previous Behavior:** Top part (intro) stayed static, but images/videos didn't transition properly
- **New Behavior:**
  - All images use pan left-to-right effect regardless of intro mode
  - B-roll videos play with proper pan effects
  - Content clips are concatenated and play sequentially under the intro overlay
  - Each media item gets equal duration based on total audio duration

### 4. Code Improvements

#### Video Composer Logic
- Separated intro rendering logic into two modes:
  - **Separate Intro Mode:** `intro_duration` is a number (e.g., 3.0 seconds) - intro plays as first clip with fade out
  - **Full Video Intro Mode:** `intro_duration` is `None` - intro stays as overlay for entire video
- Added `full_video_intro` boolean flag for clearer logic flow
- Improved variable naming: `actual_intro_duration` now correctly represents the intro duration in both modes

#### Intro Overlay Rendering
- PowerPoint template support for overlay mode
- Fallback overlay with semi-transparent background (180 alpha) at top of screen
- Overlay positioned at top center with proper text wrapping
- Maintains consistency with existing intro clip rendering

## Testing Recommendations

### Test Case 1: Full Video Intro with Images
```bash
python src/main.py --url "https://vnexpress.net/..." --intro-duration none
```
**Expected:** Intro overlay stays at top for entire video, images pan left-to-right underneath

### Test Case 2: Full Video Intro with B-roll
```bash
python src/main.py --url "https://vnexpress.net/..." --intro-duration none --broll-dir "path/to/videos"
```
**Expected:** Intro overlay stays at top, videos play with pan effects underneath

### Test Case 3: Separate Intro (Default Behavior)
```bash
python src/main.py --url "https://vnexpress.net/..." --intro-duration 3
```
**Expected:** Intro plays for 3 seconds with fade out, then content clips play

### Test Case 4: Whisper Large V3 Transcription
```bash
python src/main.py --url "https://vnexpress.net/..."
```
**Expected:** More accurate Vietnamese transcription with better word-level timing

## Dependencies Updated

- `openai-whisper>=20231117` - Added for Whisper Large V3 support

## Breaking Changes

None. All changes are backward compatible.

## Performance Notes

- Whisper Large V3 requires more VRAM and processing time than base model
- Recommended: NVIDIA GPU with at least 8GB VRAM for optimal performance
- CPU transcription will be significantly slower but still functional

## Known Issues

None identified in this release.

## Contributors

- AI Assistant (Kiro)

---

**Version:** 1.1  
**Release Date:** January 21, 2026  
**Previous Version:** 1.0
