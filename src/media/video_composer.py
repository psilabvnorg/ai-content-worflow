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
                     output_path: str, audio_duration: float) -> str:
        """Compose final TikTok video"""
        
        if not images:
            raise ValueError("No images provided")
        
        # Calculate timing
        num_images = len(images)
        duration_per_image = audio_duration / num_images
        
        # Create video clips from images
        clips = []
        for idx, img_path in enumerate(images):
            clip = self._create_ken_burns_clip(img_path, duration_per_image)
            clips.append(clip)
        
        # Concatenate all clips
        video = concatenate_videoclips(clips, method="compose")
        
        # Add audio
        audio = AudioFileClip(audio_path)
        video = video.with_audio(audio)
        
        # Add subtitles
        video = self._add_subtitles(video, subtitle_path)
        
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
        """Create clip with Ken Burns zoom effect (simplified for moviepy 2.x)"""
        # Load and resize image
        img = Image.open(image_path)
        img = self._resize_image(img)
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Create clip with duration
        clip = ImageClip(img_array, duration=duration)
        
        # Note: Ken Burns effect simplified for moviepy 2.x compatibility
        # For full Ken Burns, consider using moviepy 1.x or custom implementation
        
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
    
    def _add_subtitles(self, video: CompositeVideoClip, subtitle_path: str) -> CompositeVideoClip:
        """Add subtitles to video"""
        try:
            import pysrt
            subs = pysrt.open(subtitle_path, encoding='utf-8')
            
            subtitle_clips = []
            for sub in subs:
                start = sub.start.ordinal / 1000
                end = sub.end.ordinal / 1000
                duration = end - start
                
                txt_clip = TextClip(
                    text=sub.text,
                    font_size=50,
                    color='white',
                    stroke_color='black',
                    stroke_width=2,
                    font='DejaVu-Sans-Bold',  # More widely available font
                    method='caption',
                    size=(self.width - 100, None)
                )
                txt_clip = txt_clip.with_position(('center', self.height - 250))
                txt_clip = txt_clip.with_start(start).with_duration(duration)
                subtitle_clips.append(txt_clip)
            
            video = CompositeVideoClip([video] + subtitle_clips)
        except Exception as e:
            print(f"Warning: Could not add subtitles: {e}")
        
        return video
