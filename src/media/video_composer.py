"""Video Composer Module - Creates TikTok video with zoom/pan effects"""
import moviepy
from moviepy.video.VideoClip import VideoClip, ImageClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import numpy as np
import os

class VideoComposer:
    def __init__(self, resolution=(1080, 1920), fps=30):
        self.width, self.height = resolution
        self.fps = fps
    
    def create_video(self, images: list, audio_path: str, subtitle_path: str, 
                     output_path: str, audio_duration: float, 
                     background_music_path: str = None, title: str = None,
                     typing_sfx_path: str = None, broll_videos: list = None,
                     template: str = None, intro_duration: float = 3.0) -> str:
        """Compose final TikTok video with zoom/pan effects and B-roll videos"""
        
        if not images:
            raise ValueError("No images provided")
        
        # Determine intro duration (None = full video)
        actual_intro_duration = audio_duration if intro_duration is None else intro_duration
        has_separate_intro = intro_duration is not None and title
        
        # Calculate timing for content clips
        total_media_count = len(images) + (len(broll_videos) if broll_videos else 0)
        duration_per_media = audio_duration / total_media_count
        
        clips = []
        
        # Add intro clip with fade out if --intro-duration is specified
        if title:
            intro_clip = self._create_intro_clip(title, images[0], actual_intro_duration, template)
            if has_separate_intro:
                # Add fade out effect at the end of intro
                intro_clip = intro_clip.with_effects([moviepy.video.fx.CrossFadeOut(0.5)])
            clips.append(intro_clip)
        
        # Create image clips with pan left-to-right effect
        for idx, img_path in enumerate(images):
            clip = self._create_effect_clip(img_path, duration_per_media)
            clips.append(clip)
        
        # Add B-roll videos (muted)
        if broll_videos:
            for video_path in broll_videos:
                broll_clip = self._create_broll_clip(video_path, duration_per_media)
                if broll_clip:
                    clips.append(broll_clip)
        
        # Concatenate all clips
        video = concatenate_videoclips(clips, method="compose")
        
        # Add voice-over audio (delayed if intro is separate)
        voice_audio = AudioFileClip(audio_path)
        if has_separate_intro:
            from moviepy.video.VideoClip import AudioClip
            from moviepy.audio.AudioClip import concatenate_audioclips
            silence = AudioClip(lambda t: 0, duration=actual_intro_duration, fps=44100)
            voice_audio = concatenate_audioclips([silence, voice_audio])
        
        audio_layers = [voice_audio]
        total_duration = (actual_intro_duration if has_separate_intro else 0) + audio_duration

        # Add typing SFX during intro
        if title and actual_intro_duration > 0:
            typing_audio = self._add_typing_sfx(actual_intro_duration, typing_sfx_path)
            if typing_audio:
                audio_layers.append(typing_audio)
                print(f"✓ Added typing SFX at 30% volume during intro")
        
        # Add background music
        if background_music_path and os.path.exists(background_music_path):
            try:
                bg_music = AudioFileClip(background_music_path)
                if bg_music.duration < total_duration:
                    from moviepy.audio.AudioClip import concatenate_audioclips
                    loops = int(total_duration / bg_music.duration) + 1
                    bg_music = concatenate_audioclips([bg_music] * loops)
                bg_music = bg_music.subclip(0, total_duration)
                bg_music = bg_music.with_effects([moviepy.audio.fx.MultiplyVolume(0.15)])
                audio_layers.append(bg_music)
                print(f"✓ Background music added at 15% volume")
            except Exception as e:
                print(f"Warning: Could not add background music: {e}")
        
        # Composite audio
        from moviepy.audio.AudioClip import CompositeAudioClip
        video = video.set_audio(CompositeAudioClip(audio_layers))
        
        # Add subtitles
        time_offset = actual_intro_duration if has_separate_intro else 0
        video = self._add_subtitles(video, subtitle_path, time_offset)
        
        # Export
        video.write_videofile(output_path, fps=self.fps, codec='libx264', 
                              audio_codec='aac', bitrate='6000k', preset='medium', threads=4)
        print(f"Video created: {output_path}")
        return output_path
    
    def _create_effect_clip(self, image_path: str, duration: float) -> VideoClip:
        """Create clip with blurred background + image fit to width + pan left-to-right effect"""
        img = Image.open(image_path).convert('RGB')
        img_ratio = img.width / img.height
        
        # Create blurred background
        bg = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=40))
        bg_array = np.array(bg)
        
        # Calculate image size - fit to width, reasonable height
        base_width = self.width
        base_height = int(base_width / img_ratio)
        
        # If image is too tall, limit height to 70% of screen
        if base_height > self.height * 0.7:
            base_height = int(self.height * 0.7)
            base_width = int(base_height * img_ratio)
        
        # If image is too short, make it at least 50% of screen height
        if base_height < self.height * 0.5:
            base_height = int(self.height * 0.5)
            base_width = int(base_height * img_ratio)
        
        # For pan effect, make image wider than screen
        pan_scale = 1.15  # 15% wider for smooth pan
        pan_width = int(base_width * pan_scale)
        pan_height = int(base_height * pan_scale)
        
        def make_frame(t):
            progress = t / duration
            frame = bg_array.copy()
            
            # Smooth easing for pan
            eased = progress * progress * (3 - 2 * progress)
            
            # Resize image for pan
            current = np.array(img.resize((pan_width, pan_height), Image.Resampling.LANCZOS))
            
            # Pan from left to right
            max_pan = max(0, pan_width - self.width)
            x = -int(max_pan * eased)
            y = (self.height - pan_height) // 2
            
            # Paste onto blurred background
            sx1, sy1 = max(0, -x), max(0, -y)
            sx2, sy2 = min(pan_width, self.width - x), min(pan_height, self.height - y)
            dx1, dy1 = max(0, x), max(0, y)
            dx2, dy2 = min(self.width, x + pan_width), min(self.height, y + pan_height)
            if sx2 > sx1 and sy2 > sy1:
                frame[dy1:dy2, dx1:dx2] = current[sy1:sy2, sx1:sx2]
            return frame
        
        return VideoClip(make_frame, duration=duration)

    def _create_broll_clip(self, video_path: str, target_duration: float) -> VideoClip:
        """Create B-roll video clip with blurred background"""
        try:
            from moviepy.video.io.VideoFileClip import VideoFileClip
            if not os.path.exists(video_path):
                return None
            
            broll = VideoFileClip(video_path).without_audio()
            if broll.duration > target_duration:
                broll = broll.subclip(0, target_duration)
            elif broll.duration < target_duration:
                from moviepy.video.compositing.concatenate import concatenate_videoclips
                loops = int(target_duration / broll.duration) + 1
                broll = concatenate_videoclips([broll] * loops).subclip(0, target_duration)
            
            return self._resize_broll_with_blur(broll)
        except Exception as e:
            print(f"   ⚠ Error loading B-roll {video_path}: {e}")
            return None
    
    def _resize_broll_with_blur(self, video_clip: VideoClip) -> VideoClip:
        """Resize B-roll with blurred background and pan effect"""
        ow, oh = video_clip.size
        ratio = ow / oh
        
        # Fit to width, reasonable height (50-70% of screen)
        nw = self.width
        nh = int(nw / ratio)
        
        if nh > self.height * 0.7:
            nh = int(self.height * 0.7)
            nw = int(nh * ratio)
        if nh < self.height * 0.5:
            nh = int(self.height * 0.5)
            nw = int(nh * ratio)
        
        # Add 15% for pan effect
        pan_w = int(nw * 1.15)
        pan_h = int(nh * 1.15)
        
        resized = video_clip.resized((pan_w, pan_h))
        
        # Create blurred background
        bg = Image.fromarray(video_clip.get_frame(0))
        bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=40))
        bg_array = np.array(bg)
        
        duration = video_clip.duration
        
        def make_frame(t):
            progress = t / duration
            eased = progress * progress * (3 - 2 * progress)
            
            frame = bg_array.copy()
            vf = resized.get_frame(t)
            
            # Pan from left to right
            max_pan = max(0, pan_w - self.width)
            x = -int(max_pan * eased)
            y = (self.height - pan_h) // 2
            
            sx1, sy1 = max(0, -x), max(0, -y)
            sx2, sy2 = min(pan_w, self.width - x), min(pan_h, self.height - y)
            dx1, dy1 = max(0, x), max(0, y)
            dx2, dy2 = min(self.width, x + pan_w), min(self.height, y + pan_h)
            if sx2 > sx1 and sy2 > sy1:
                frame[dy1:dy2, dx1:dx2] = vf[sy1:sy2, sx1:sx2]
            return frame
        
        return VideoClip(make_frame, duration=duration)
    
    def _add_typing_sfx(self, duration: float, custom_path: str = None) -> AudioFileClip:
        """Add typing sound effect"""
        paths = [custom_path, 'assets/typing.mp3', 'assets/typing.wav']
        sfx_path = next((p for p in paths if p and os.path.exists(p)), None)
        if not sfx_path:
            return None
        try:
            audio = AudioFileClip(sfx_path)
            if audio.duration < duration:
                from moviepy.audio.AudioClip import concatenate_audioclips
                audio = concatenate_audioclips([audio] * (int(duration / audio.duration) + 1))
            return audio.subclip(0, duration).with_effects([moviepy.audio.fx.MultiplyVolume(0.3)])
        except:
            return None

    def _add_subtitles(self, video: CompositeVideoClip, subtitle_path: str, time_offset: float = 0.0) -> CompositeVideoClip:
        """Add subtitles to video"""
        try:
            import pysrt
            subs = pysrt.open(subtitle_path, encoding='utf-8')
            clips = []
            for sub in subs:
                start = (sub.start.ordinal / 1000) + time_offset
                duration = (sub.end.ordinal / 1000) + time_offset - start
                img = self._create_subtitle_image(sub.text)
                clip = ImageClip(img, duration=duration).with_position(('center', self.height - 250)).with_start(start)
                clips.append(clip)
            video = CompositeVideoClip([video] + clips)
            print(f"✓ Added {len(clips)} subtitle clips")
        except Exception as e:
            print(f"Warning: Could not add subtitles: {e}")
        return video
    
    def _create_intro_clip(self, title: str, image_path: str, duration: float, template: str = None) -> VideoClip:
        """Create intro clip using PowerPoint template or fallback"""
        if template:
            try:
                from media.intro_renderer import IntroTemplateRenderer
                renderer = IntroTemplateRenderer("templates/intro_template.pptx")
                slides = renderer.list_slides()
                slide_idx = 0
                for s in slides:
                    for text in s.get('preview_text', []):
                        if template.lower() in text.lower():
                            slide_idx = s['index']
                            break
                try:
                    slide_idx = int(template)
                except:
                    pass
                intro_array = renderer.render_to_numpy(slide_idx, title, image_path)
                print(f"✓ Using PowerPoint template slide {slide_idx}")
                return ImageClip(intro_array, duration=duration)
            except Exception as e:
                print(f"⚠ PowerPoint template failed: {e}, using fallback")
        
        return self._create_fallback_intro(title, image_path, duration)
    
    def _create_fallback_intro(self, title: str, image_path: str, duration: float) -> VideoClip:
        """Fallback intro"""
        img = Image.open(image_path).convert('RGB')
        img = self._resize_image_full(img)
        
        if os.path.exists('assets/tiktok_background.png'):
            overlay = Image.open('assets/tiktok_background.png').convert('RGBA')
            overlay = overlay.resize((self.width, self.height), Image.Resampling.LANCZOS)
            img = Image.alpha_composite(img.convert('RGBA'), overlay)
        else:
            img = img.convert('RGBA')
        
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
        
        y = self.height // 2 + 200
        for line in lines:
            draw.text((60, y), line, font=font, fill='white')
            y += 60
        
        return ImageClip(np.array(img.convert('RGB')), duration=duration)

    def _resize_image_full(self, img: Image.Image) -> Image.Image:
        """Resize image to fill screen (crop if needed)"""
        ratio = img.width / img.height
        target = self.width / self.height
        
        if ratio > target:
            nh = self.height
            nw = int(nh * ratio)
            img = img.resize((nw, nh), Image.Resampling.LANCZOS)
            left = (nw - self.width) // 2
            img = img.crop((left, 0, left + self.width, self.height))
        else:
            nw = self.width
            nh = int(nw / ratio)
            img = img.resize((nw, nh), Image.Resampling.LANCZOS)
            top = (nh - self.height) // 2
            img = img.crop((0, top, self.width, top + self.height))
        return img
    
    def _get_font(self, size: int):
        """Get font with fallback"""
        for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                  '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf']:
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()
    
    def _create_subtitle_image(self, text: str, max_width: int = 980) -> np.ndarray:
        """Create subtitle image"""
        font = self._get_font(38)
        temp = Image.new('RGB', (max_width, 500), 'black')
        draw = ImageDraw.Draw(temp)
        
        words, lines, cur = text.split(), [], []
        for w in words:
            test = ' '.join(cur + [w])
            if draw.textbbox((0, 0), test, font=font)[2] <= max_width - 40:
                cur.append(w)
            else:
                if cur: lines.append(' '.join(cur))
                cur = [w]
        if cur: lines.append(' '.join(cur))
        
        line_h = 48
        total_h = len(lines) * line_h + 30
        img = Image.new('RGBA', (max_width, total_h), (0, 0, 0, 220))
        draw = ImageDraw.Draw(img)
        
        y = 15
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (max_width - (bbox[2] - bbox[0])) // 2
            color = '#FFFF99' if any(p in line for p in '.!?:') else 'white'
            draw.text((x, y), line, font=font, fill=color)
            y += line_h
        
        return np.array(img)
