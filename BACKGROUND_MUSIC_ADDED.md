# Background Music Feature

## Implementation

Added background music support to the video composer with automatic volume balancing.

## Changes

### 1. Video Composer (`src/media/video_composer.py`)

**Added parameter:** `background_music_path` to `create_video()` method

**Features:**
- Loads background music from specified path
- Automatically loops music if shorter than video duration
- Reduces background music volume to **15%** (so voice-over is clear)
- Composites voice-over (100% volume) + background music (15% volume)
- Graceful fallback if music file not found

**Code:**
```python
# Load background music
bg_music = AudioFileClip(background_music_path)

# Loop if needed
if bg_music.duration < audio_duration:
    loops_needed = int(audio_duration / bg_music.duration) + 1
    bg_music = concatenate_audioclips([bg_music] * loops_needed)

# Trim to match video duration
bg_music = bg_music.subclipped(0, audio_duration)

# Reduce volume to 15%
bg_music = bg_music.with_effects([moviepy.audio.fx.MultiplyVolume(0.15)])

# Composite: voice + background music
final_audio = CompositeAudioClip([voice_audio, bg_music])
```

### 2. Main Pipeline (`src/main.py`)

**Added:** Background music path configuration

**Path:** `assets/background_music.mp3`

**Features:**
- Checks if background music file exists
- Passes path to video composer
- Warns if file not found (continues without music)

## Audio Levels

- **Voice-over:** 100% volume (full clarity)
- **Background music:** 15% volume (subtle, doesn't interfere)

This ratio ensures:
- ✅ Voice is always clear and understandable
- ✅ Music adds atmosphere without distraction
- ✅ Professional TikTok-style audio mix

## File Location

**Background music:** `assets/background_music.mp3` (8.1 MB)

## Usage

The background music is automatically added when generating videos:

```bash
python src/main.py
# Enter news URL
# Video will include background music at 15% volume
```

## Testing

Generate a video and verify:
1. Voice-over is clear and loud
2. Background music is audible but subtle
3. Music loops seamlessly if video is longer than music
4. Music stops exactly when video ends

## Volume Adjustment

To change background music volume, edit `src/media/video_composer.py`:

```python
# Current: 15% volume
bg_music = bg_music.with_effects([moviepy.audio.fx.MultiplyVolume(0.15)])

# For louder music (20%):
bg_music = bg_music.with_effects([moviepy.audio.fx.MultiplyVolume(0.20)])

# For quieter music (10%):
bg_music = bg_music.with_effects([moviepy.audio.fx.MultiplyVolume(0.10)])
```

## Files Modified

1. ✅ `src/media/video_composer.py` - Background music support
2. ✅ `src/main.py` - Pass background music path
3. ✅ `BACKGROUND_MUSIC_ADDED.md` - Documentation

## Result

Videos now have:
- ✅ Clear voice-over narration
- ✅ Subtle background music (15% volume)
- ✅ Professional audio mixing
- ✅ Automatic music looping
- ✅ TikTok-style production quality
