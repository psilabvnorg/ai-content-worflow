# Spec: Fix Intro Overlay Bug When intro-duration=none

## Problem Statement

When `--intro-duration none` is used, the intro overlay should stay visible for the entire video duration while the underlying images and B-roll videos continue to transition and play normally. Currently, the intro overlay is blocking or interfering with the content transitions.

## Current Behavior (Bug)

When `--intro-duration none`:
- ✅ Intro overlay stays for full video duration
- ❌ Images/videos underneath don't transition properly
- ❌ The "top part" stays static instead of showing content transitions

## Expected Behavior

When `--intro-duration none`:
- ✅ Intro overlay stays for full video duration (as transparent overlay)
- ✅ Images transition with pan effects underneath the overlay
- ✅ B-roll videos play and transition underneath the overlay
- ✅ All content behaves the same as when intro is a separate clip, just with overlay on top

## Root Cause Analysis

In `src/media/video_composer.py`, line 318:

**BUG FOUND**: 
```python
return ImageClip(intro_array, duration=duration).with_position(('center', 'center'))
```

**Issues**:
1. Position is `('center', 'center')` instead of `('center', 'top')` - this centers the overlay and blocks content
2. PowerPoint template is rendered as RGB (no alpha channel) - completely opaque, blocks all content
3. The fallback overlay correctly uses `('center', 'top')` and RGBA with transparency, but PowerPoint template doesn't

## Acceptance Criteria

### AC1: Intro Overlay Transparency
- [ ] Intro overlay has proper alpha channel/transparency
- [ ] Only the intro text/graphics are visible, not a solid background
- [ ] Content underneath is visible through transparent areas

### AC2: Content Transitions Work
- [ ] Images pan left-to-right as normal
- [ ] B-roll videos play and transition as normal
- [ ] All visual effects (blur, pan) work correctly

### AC3: Overlay Positioning
- [ ] Intro overlay is positioned at top of frame
- [ ] Overlay doesn't cover the entire video frame
- [ ] Subtitles at bottom remain visible

### AC4: Fallback Intro Overlay
- [ ] `_create_fallback_intro_overlay()` creates semi-transparent overlay
- [ ] Overlay only covers top portion (e.g., 300px height)
- [ ] Rest of frame shows content transitions

## Technical Implementation

### Files to Modify
- `src/media/video_composer.py`

### Changes Required

1. **Fix `_create_intro_overlay()` method**:
   - Ensure PowerPoint template has transparent background
   - Return clip with proper alpha channel support
   - Position at top of frame, not center

2. **Fix `_create_fallback_intro_overlay()` method**:
   - Create RGBA image with transparency
   - Only add semi-transparent background at top (e.g., 300px)
   - Rest of image should be fully transparent (alpha=0)
   - Position at top of frame

3. **Fix compositing in `create_video()` method**:
   - Ensure overlay is composited with proper blending mode
   - Verify z-order: content clips → intro overlay → subtitles

### Code Changes

```python
def _create_intro_overlay(self, title: str, image_path: str, duration: float, template: str = None) -> VideoClip:
    """Create intro overlay that stays on top for entire video duration"""
    if template:
        try:
            from media.intro_renderer import IntroTemplateRenderer
            renderer = IntroTemplateRenderer("templates/intro_template.pptx")
            # ... existing template logic ...
            intro_array = renderer.render_to_numpy(slide_idx, title, image_path)
            print(f"✓ Using PowerPoint template slide {slide_idx} as overlay")
            # FIX: Position at top, not center
            return ImageClip(intro_array, duration=duration).with_position(('center', 'top'))
        except Exception as e:
            print(f"⚠ PowerPoint template failed: {e}, using fallback overlay")
    
    return self._create_fallback_intro_overlay(title, image_path, duration)

def _create_fallback_intro_overlay(self, title: str, image_path: str, duration: float) -> VideoClip:
    """Fallback intro overlay with semi-transparent background at top only"""
    # FIX: Create fully transparent image
    img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
    
    # Add semi-transparent background ONLY at top
    overlay_height = 300
    overlay_bg = Image.new('RGBA', (self.width, overlay_height), (0, 0, 0, 180))
    img.paste(overlay_bg, (0, 0))
    
    draw = ImageDraw.Draw(img)
    font = self._get_font(48)
    
    # Word wrap title
    words, lines, cur = title.split(), [], []
    for w in words:
        test = ' '.join(cur + [w])
        if draw.textbbox((0, 0), test, font=font)[2] <= self.width - 120:
            cur.append(w)
        else:
            if cur: lines.append(' '.join(cur))
            cur = [w]
    if cur: lines.append(' '.join(cur))
    
    # Draw title text at top
    y = 60
    for line in lines:
        draw.text((60, y), line, font=font, fill='white')
        y += 60
    
    # FIX: Return with proper positioning
    return ImageClip(np.array(img), duration=duration).with_position(('center', 'top'))
```

## Testing Plan

### Test Case 1: Intro Overlay with Images
```bash
python src/main.py --url "..." --template "tiktok_psi" --intro-duration none
```
**Expected**: Intro stays at top, images pan underneath

### Test Case 2: Intro Overlay with B-roll
```bash
python src/main.py --url "..." --broll-dir "videos/" --intro-duration none
```
**Expected**: Intro stays at top, videos play underneath

### Test Case 3: Fallback Intro Overlay
```bash
python src/main.py --url "..." --intro-duration none
# (without template or with invalid template)
```
**Expected**: Fallback overlay at top, content transitions underneath

### Test Case 4: Normal Intro (Regression Test)
```bash
python src/main.py --url "..." --template "tiktok_psi" --intro-duration 3
```
**Expected**: Separate intro clip with fade out, then content

## Related Issues

- Update #1, Task #3: "when --intro-duration is set to none, top part stayed the same which is wrong, correct way: it should have images with default transition and videos plays along with it"

## Notes

- The overlay should be truly transparent (RGBA with alpha=0) except for the intro graphics area
- MoviePy's `CompositeVideoClip` should handle alpha blending automatically
- Position should be `('center', 'top')` not `('center', 'center')`
- The current `_create_fallback_intro_overlay()` already has the right approach, just needs verification
