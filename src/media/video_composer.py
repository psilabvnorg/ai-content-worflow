"""Video Composer Module - Creates TikTok video with Ken Burns effect"""
import moviepy
from moviepy import (VideoClip, ImageClip, AudioFileClip, TextClip, 
                     CompositeVideoClip, concatenate_videoclips)
from PIL import Image
import numpy as np
import os

class VideoComposer:
    def __init__(self, resolution=(1080, 1920), fps=30):
        self.width, self.height = resolution
        self.fps = fps
    
    def create_video(self, images: list, audio_path: str, subtitle_path: str, 
                     output_path: str, audio_duration: float, 
                     background_music_path: str = None, title: str = None) -> str:
        """Compose final TikTok video"""
        
        if not images:
            raise ValueError("No images provided")
        
        # Calculate timing
        intro_duration = 3.0 if title else 0.0
        num_images = len(images)
        duration_per_image = audio_duration / num_images
        
        # Create video clips from images
        clips = []
        
        # Add intro clip if title is provided
        if title:
            # Use first article image for intro background
            intro_clip = self._create_intro_clip(title, images[0], duration=intro_duration)
            clips.append(intro_clip)
        
        for idx, img_path in enumerate(images):
            clip = self._create_ken_burns_clip(img_path, duration_per_image)
            clips.append(clip)
        
        # Concatenate all clips with crossfade transitions (TikTok style)
        # Use padding=0 and method="compose" for smooth transitions
        video = concatenate_videoclips(clips, method="compose", padding=-0.5)  # 0.5s overlap for crossfade
        
        # Add voice-over audio (delayed by intro duration)
        voice_audio = AudioFileClip(audio_path)
        if intro_duration > 0:
            # Add silence at the beginning for intro
            from moviepy import AudioClip
            silence = AudioClip(lambda t: 0, duration=intro_duration, fps=44100)
            from moviepy import concatenate_audioclips
            voice_audio = concatenate_audioclips([silence, voice_audio])
        
        # Add background music if provided
        if background_music_path and os.path.exists(background_music_path):
            try:
                print(f"Adding background music: {background_music_path}")
                bg_music = AudioFileClip(background_music_path)
                
                total_duration = intro_duration + audio_duration
                
                # Loop background music if it's shorter than video
                if bg_music.duration < total_duration:
                    # Calculate how many loops needed
                    loops_needed = int(total_duration / bg_music.duration) + 1
                    from moviepy import concatenate_audioclips
                    bg_music = concatenate_audioclips([bg_music] * loops_needed)
                
                # Trim to match video duration
                bg_music = bg_music.subclipped(0, total_duration)
                
                # Reduce background music volume to 15% (so voice is clear)
                bg_music = bg_music.with_effects([moviepy.audio.fx.MultiplyVolume(0.15)])
                
                # Composite audio: voice at full volume + background music at low volume
                from moviepy import CompositeAudioClip
                final_audio = CompositeAudioClip([voice_audio, bg_music])
                video = video.with_audio(final_audio)
                
                print(f"✓ Background music added at 15% volume")
            except Exception as e:
                print(f"Warning: Could not add background music: {e}")
                video = video.with_audio(voice_audio)
        else:
            video = video.with_audio(voice_audio)
        
        # Add logo overlay
        video = self._add_logo(video)
        
        # Add subtitles (offset by intro duration)
        video = self._add_subtitles(video, subtitle_path, time_offset=intro_duration)
        
        # Export video
        video.write_videofile(
            output_path,
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            bitrate='6000k',
            preset='medium',
            threads=4
        )
        
        print(f"Video created: {output_path}")
        return output_path
    
    def _create_ken_burns_clip(self, image_path: str, duration: float) -> ImageClip:
        """Create clip with horizontal image on blurred background (TikTok style)"""
        from PIL import ImageFilter
        
        # Load original image
        img = Image.open(image_path)
        
        # Create blurred background (90% blur)
        bg = img.copy()
        bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
        # Apply heavy blur (radius 50 for 90% blur effect)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=50))
        
        # Resize main image to fit horizontally while maintaining aspect ratio
        img_ratio = img.width / img.height
        target_ratio = self.width / self.height
        
        # Calculate size to fit horizontally with some margin
        margin = 100  # pixels margin on sides
        target_width = self.width - (margin * 2)
        target_height = int(target_width / img_ratio)
        
        # If height is too large, scale down
        if target_height > self.height - 200:  # Leave space for subtitles
            target_height = self.height - 200
            target_width = int(target_height * img_ratio)
        
        # Resize main image
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Composite: paste main image on blurred background
        # Center the image
        x_offset = (self.width - target_width) // 2
        y_offset = (self.height - target_height) // 2
        
        bg.paste(img, (x_offset, y_offset))
        
        # Convert to numpy array
        img_array = np.array(bg)
        
        # Create clip with duration
        clip = ImageClip(img_array, duration=duration)
        
        return clip
    
    def _resize_image(self, img: Image.Image) -> Image.Image:
        """Resize image to 9:16 aspect ratio"""
        target_ratio = self.width / self.height
        img_ratio = img.width / img.height
        
        if img_ratio > target_ratio:
            # Image is wider, crop width
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # Image is taller, crop height
            new_height = int(img.width / target_ratio)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))
        
        # Resize to target resolution
        img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
        return img
    
    def _add_logo(self, video: CompositeVideoClip) -> CompositeVideoClip:
        """Add logo to top left corner"""
        try:
            # Try to find logo
            logo_paths = [
                'assets/logo.png',
                'logo.png',
                '#logo.png'
            ]
            
            logo_path = None
            for path in logo_paths:
                if os.path.exists(path):
                    logo_path = path
                    break
            
            if not logo_path:
                print("Warning: Logo not found, skipping logo overlay")
                return video
            
            # Load and resize logo
            logo_img = Image.open(logo_path)
            
            # Resize logo to reasonable size (150px width)
            logo_width = 150
            logo_ratio = logo_img.height / logo_img.width
            logo_height = int(logo_width * logo_ratio)
            logo_img = logo_img.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            # Convert to RGBA if not already
            if logo_img.mode != 'RGBA':
                logo_img = logo_img.convert('RGBA')
            
            # Create logo clip
            logo_array = np.array(logo_img)
            logo_clip = ImageClip(logo_array, duration=video.duration)
            
            # Position at top left with 20px margin
            logo_clip = logo_clip.with_position((20, 20))
            
            # Composite logo over video
            video = CompositeVideoClip([video, logo_clip])
            print(f"✓ Added logo from {logo_path}")
            
        except Exception as e:
            print(f"Warning: Could not add logo: {e}")
        
        return video
    
    def _add_subtitles(self, video: CompositeVideoClip, subtitle_path: str, time_offset: float = 0.0) -> CompositeVideoClip:
        """Add subtitles to video with black background (TikTok style)"""
        try:
            import pysrt
            from PIL import Image, ImageDraw, ImageFont
            
            subs = pysrt.open(subtitle_path, encoding='utf-8')
            
            subtitle_clips = []
            for sub in subs:
                start = (sub.start.ordinal / 1000) + time_offset
                end = (sub.end.ordinal / 1000) + time_offset
                duration = end - start
                
                # Create subtitle image with PIL (more reliable than TextClip)
                subtitle_img = self._create_subtitle_image(sub.text)
                
                # Create ImageClip from the subtitle
                txt_clip = ImageClip(subtitle_img, duration=duration)
                txt_clip = txt_clip.with_position(('center', self.height - 250))
                txt_clip = txt_clip.with_start(start)
                subtitle_clips.append(txt_clip)
            
            video = CompositeVideoClip([video] + subtitle_clips)
            print(f"✓ Added {len(subtitle_clips)} subtitle clips")
        except Exception as e:
            print(f"Warning: Could not add subtitles: {e}")
            import traceback
            traceback.print_exc()
        
        return video
    
    def _create_intro_clip(self, title: str, article_image_path: str, duration: float = 3.0) -> VideoClip:
        """Create intro clip with article image background, gradient overlay, title, and logo"""
        from PIL import Image, ImageDraw, ImageFont
        
        # Load and resize article image to fit 9:16
        article_img = Image.open(article_image_path).convert('RGB')
        article_img = self._resize_image(article_img)
        
        # Load the gradient overlay PNG
        gradient_path = 'assets/tiktok_background.png'
        if not os.path.exists(gradient_path):
            raise FileNotFoundError(f"Gradient overlay not found: {gradient_path}")
        
        gradient_overlay = Image.open(gradient_path).convert('RGBA')
        
        # Composite: article image + gradient overlay
        # Convert article image to RGBA for compositing
        article_img = article_img.convert('RGBA')
        composite = Image.alpha_composite(article_img, gradient_overlay)
        
        # Add logo to top left
        try:
            logo_paths = [
                'assets/logo.png',
                'logo.png',
            ]
            
            logo_path = None
            for path in logo_paths:
                if os.path.exists(path):
                    logo_path = path
                    break
            
            if logo_path:
                logo_img = Image.open(logo_path).convert('RGBA')
                
                # Resize logo to reasonable size (120px width)
                logo_width = 120
                logo_ratio = logo_img.height / logo_img.width
                logo_height = int(logo_width * logo_ratio)
                logo_img = logo_img.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                
                # Paste logo at top left with 20px margin
                composite.paste(logo_img, (20, 20), logo_img)
                
        except Exception as e:
            print(f"Warning: Could not add logo to intro: {e}")
        
        # Add title text to the bottom half with left alignment
        draw = ImageDraw.Draw(composite)
        
        # Load font (smaller size)
        try:
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                'C:\\Windows\\Fonts\\arial.ttf',
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 48)  # Reduced from 60 to 48
                    break
            if font is None:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Word wrap title with left margin
        left_margin = 60  # Left margin for text
        right_margin = 60  # Right margin for text
        max_width = self.width - left_margin - right_margin
        words = title.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw text in bottom half (left-aligned)
        line_height = 60
        total_text_height = len(lines) * line_height
        start_y = self.height // 2 + (self.height // 2 - total_text_height) // 2
        
        for i, line in enumerate(lines):
            x_position = left_margin  # Left-aligned
            y_position = start_y + i * line_height
            
            # Draw text with white color
            draw.text((x_position, y_position), line, font=font, fill='white')
        
        # Convert to RGB for video
        composite = composite.convert('RGB')
        
        # Convert to numpy array and create clip
        img_array = np.array(composite)
        clip = ImageClip(img_array, duration=duration)
        
        return clip
    
    def _create_subtitle_image(self, text: str, max_width: int = 980) -> np.ndarray:
        """Create subtitle image with black background and white text (TikTok style)"""
        from PIL import Image, ImageDraw, ImageFont
        
        # Try to load a font, fallback to default if not available
        try:
            # Try common font paths
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                'C:\\Windows\\Fonts\\arial.ttf',
            ]
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 38)  # Reduced from 48 to 38
                    break
            
            if font is None:
                # Use default font
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Create a temporary image to measure text size
        temp_img = Image.new('RGB', (max_width, 500), color='black')
        draw = ImageDraw.Draw(temp_img)
        
        # Split text into words and add emphasis
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width - 40:  # 20px padding on each side
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate total height needed (smaller line height)
        line_height = 48  # Reduced from 60 to 48
        total_height = len(lines) * line_height + 30  # Reduced padding
        
        # Create final image with black background
        img = Image.new('RGBA', (max_width, total_height), color=(0, 0, 0, 220))  # More opaque
        draw = ImageDraw.Draw(img)
        
        # Draw each line of text with emphasis on important words
        y_offset = 15
        for line in lines:
            # Get text bounding box for centering
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_position = (max_width - text_width) // 2
            
            # Draw text with white color and yellow highlight for emphasis
            # Check if line contains punctuation (end of sentence)
            if any(p in line for p in ['.', '!', '?', ':']):
                # Add slight yellow tint for emphasis
                draw.text((x_position, y_offset), line, font=font, fill='#FFFF99')
            else:
                draw.text((x_position, y_offset), line, font=font, fill='white')
            
            y_offset += line_height
        
        # Convert to numpy array
        return np.array(img)

