# Whisper Upgrade and Intro Overlay Fixes

## Overview
Upgrade the transcription model to Whisper Large V3 and fix bugs related to intro overlay mode when `--intro-duration` is set to `none`.

## User Stories

### US-1: Upgrade to Whisper Large V3
**As a** content creator  
**I want** more accurate Vietnamese transcription using Whisper Large V3  
**So that** my subtitles have better accuracy and timing precision

**Acceptance Criteria:**
- AC-1.1: System uses `openai/whisper-large-v3` model from HuggingFace
- AC-1.2: Model supports word-level timestamps for Vietnamese language
- AC-1.3: System gracefully falls back to smaller models if GPU memory is insufficient
- AC-1.4: Transcription accuracy improves compared to current base model
- AC-1.5: Model loading and inference time remains reasonable (< 2x current time)

### US-2: Fix Intro Overlay Positioning
**As a** content creator  
**I want** the intro overlay to stay in the same position throughout the entire video when using `--intro-duration none`  
**So that** my branding remains visible and consistent

**Acceptance Criteria:**
- AC-2.1: When `--intro-duration none`, intro overlay stays at the same screen position for entire video duration
- AC-2.2: Intro overlay does not move, pan, or shift during video playback
- AC-2.3: Intro overlay maintains transparency/alpha channel properly
- AC-2.4: Intro overlay appears on top of all content (images and videos)

### US-3: Enable Content Transitions Under Intro Overlay
**As a** content creator  
**I want** images and videos to transition normally underneath the intro overlay when using `--intro-duration none`  
**So that** my video has dynamic content while maintaining consistent branding

**Acceptance Criteria:**
- AC-3.1: Images transition with pan effects underneath the intro overlay
- AC-3.2: B-roll videos play and transition underneath the intro overlay
- AC-3.3: All content (images + videos) displays for their calculated duration
- AC-3.4: Pan effects (left-to-right) work correctly on images under overlay
- AC-3.5: Blurred backgrounds render correctly under overlay
- AC-3.6: Content timing matches audio duration (no gaps or overlaps)

## Technical Context

### Current Implementation
- **Whisper Model**: Uses `base` model with fallback to `small` and `tiny`
- **Intro Overlay**: Has bugs where overlay moves or content doesn't transition properly
- **Video Composition**: Uses MoviePy's `CompositeVideoClip` for layering

### Proposed Changes
1. **Whisper Upgrade**: Switch from `whisper.load_model()` to HuggingFace Transformers pipeline
2. **Intro Overlay Fix**: Ensure overlay is created as static `ImageClip` with full duration
3. **Content Layer Fix**: Ensure base video layer contains all transitioning content

## Dependencies
- `transformers` library (already in requirements.txt)
- `openai/whisper-large-v3` model from HuggingFace (~3GB)
- Existing MoviePy and PIL dependencies

## Constraints
- Must maintain backward compatibility with existing CLI arguments
- Must preserve GPU memory management and fallback mechanisms
- Must not break existing intro modes (separate intro with fade)
- Should maintain or improve current performance

## Success Metrics
- Subtitle accuracy improves by at least 10% (measured by manual review)
- Intro overlay stays fixed in position (visual verification)
- Content transitions smoothly under overlay (visual verification)
- No regression in video generation time (< 10% increase acceptable)

## Out of Scope
- Changing subtitle styling or positioning
- Modifying other video effects beyond intro overlay
- Adding new intro modes or templates
- Performance optimization beyond maintaining current speed

## Related Files
- `src/media/subtitle_generator.py` - Whisper model loading and transcription
- `src/media/video_composer.py` - Intro overlay creation and video composition
- `src/media/intro_renderer.py` - PowerPoint template rendering
- `requirements.txt` - Python dependencies
