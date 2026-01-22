"""
Main Orchestrator - TikTok News Video Generator.

This is the entry point that coordinates the entire video generation pipeline.
"""
import os
import sys
import argparse
import json
from datetime import datetime
from core import NewsProcessor
from media import MediaGenerator


class TikTokNewsGenerator:
    '''
    Main orchestrator for TikTok news video generation.
    
    Coordinates the complete pipeline:
    1. Crawl article from news site
    2. Summarize and refine content
    3. Generate voice-over audio
    4. Create synchronized subtitles
    5. Compose final video with effects
    6. Export metadata and summaries
    '''
    
    def __init__(self, voice: str = "binh", image_dir: str = None, broll_dir: str = None,
                 template: str = None, intro_duration: float = 3.0):
        '''
        Initialize the video generator.
        
        Args:
            voice: Voice name for TTS
            image_dir: Custom directory for images
            broll_dir: Directory containing B-roll videos
            template: PowerPoint template slide name/index
            intro_duration: Intro duration in seconds (None = full video)
        '''
        self.custom_image_dir = image_dir
        self.broll_dir = broll_dir
        self.template = template
        self.intro_duration = intro_duration
        
        print("\n" + "="*60)
        print("Initializing TikTok News Generator...")
        print("="*60)
        
        self.processor = NewsProcessor()
        self.media = MediaGenerator(voice=voice)
        
        print("✓ All modules initialized!\n")
    
    def generate_video(self, news_url: str, output_name: str = None) -> str:
        '''
        Complete pipeline: URL → TikTok Video.
        
        Args:
            news_url: URL of news article
            output_name: Output filename (without extension)
            
        Returns:
            Path to generated video file
        '''
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_name:
            output_name = f"tiktok_news_{timestamp}"
        
        print(f"\n{'='*60}")
        print(f"GENERATING TIKTOK VIDEO")
        print(f"{'='*60}\n")
        
        # Step 1: Crawl article
        print("📰 Step 1: Crawling article...")
        article = self.processor.crawl_article(news_url)
        print(f"   ✓ Title: {article['title'][:60]}...")
        print(f"   ✓ Images: {len(article['images'])} downloaded")
        
        # Load custom images/videos if specified
        broll_videos = []
        if self.broll_dir and os.path.isdir(self.broll_dir):
            broll_videos = self._load_media(self.broll_dir, {'.mp4', '.mov', '.avi', '.mkv', '.webm'})
            if broll_videos:
                print(f"   ✓ Found {len(broll_videos)} B-roll videos")
        
        if self.custom_image_dir and os.path.isdir(self.custom_image_dir):
            custom_images = self._load_media(self.custom_image_dir, {'.jpg', '.jpeg', '.png', '.webp', '.bmp'})
            if custom_images:
                article['images'] = custom_images
                print(f"   ✓ Using {len(custom_images)} custom images")
            broll_from_images = self._load_media(self.custom_image_dir, {'.mp4', '.mov', '.avi', '.mkv', '.webm'})
            if broll_from_images:
                broll_videos.extend(broll_from_images)
                print(f"   ✓ Found {len(broll_from_images)} B-roll videos in image directory")
        
        if len(article['images']) < 3:
            print("   ⚠ Warning: Less than 3 images found")
        
        # Step 2: Summarize content
        print("\n📝 Step 2: Summarizing content...")
        body = self.processor.summarize(article)
        print(f"   ✓ Body: {len(body.split())} words")
        
        # Step 3: Correct and refine text
        print("\n🔧 Step 3: Correcting and refining text...")
        body = self.processor.correct_text(body)
        body = self.processor.refine_text(body)
        body = self._final_cleanup(body)
        print(f"   ✓ Final body: {len(body.split())} words")
        
        # Step 4: Add intro and outro
        print("\n📌 Step 4: Adding intro and outro...")
        intro = f"Tin nóng: {article['title'][:50]}..."
        outro = "Theo dõi và follow kênh Tiktok của PSI để cập nhật thêm tin tức!"
        full_script = f"{intro}... {body} ... {outro}"
        print(f"   ✓ Full script: {len(full_script.split())} words")
        
        # Step 5: Export summary
        print("\n📄 Step 5: Exporting summary...")
        summary_path, summary_json = self._export_summary(output_name, article, intro, body, outro, full_script, news_url, timestamp)
        print(f"   ✓ Summary: {summary_path}")
        print(f"   ✓ JSON: {summary_json}")
        
        # Step 6: Generate voice-over
        print("\n🎤 Step 6: Generating voice-over...")
        audio_path = f"output/audio/{output_name}.mp3"
        os.makedirs("output/audio", exist_ok=True)
        self.media.generate_audio(full_script, audio_path)
        audio_duration = self.media.get_audio_duration(audio_path)
        print(f"   ✓ Audio duration: {audio_duration:.1f}s")
        
        # Step 7: Generate subtitles
        print("\n💬 Step 7: Generating subtitles...")
        subtitle_path = f"output/temp/{output_name}.srt"
        os.makedirs("output/temp", exist_ok=True)
        self.media.generate_subtitles(audio_path, subtitle_path, full_script)
        
        # Step 8: Compose video
        print("\n🎬 Step 8: Composing video...")
        video_path = f"output/videos/{output_name}.mp4"
        os.makedirs("output/videos", exist_ok=True)
        background_music = "assets/background_music.mp3" if os.path.exists("assets/background_music.mp3") else None
        typing_sfx = "assets/typing.mp3" if os.path.exists("assets/typing.mp3") else None
        
        self.media.compose_video(
            images=article['images'],
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            output_path=video_path,
            audio_duration=audio_duration,
            title=article['title'],
            background_music=background_music,
            typing_sfx=typing_sfx,
            broll_videos=broll_videos if broll_videos else None,
            template=self.template,
            intro_duration=self.intro_duration
        )
        
        # Step 9: Update JSON with final metadata
        self._update_summary_json(summary_json, audio_duration, video_path, audio_path, subtitle_path)
        
        print(f"\n{'='*60}")
        print(f"✅ VIDEO GENERATION COMPLETE!")
        print(f"{'='*60}")
        print(f"Video:    {video_path}")
        print(f"Duration: {audio_duration:.1f}s")
        print(f"{'='*60}\n")
        
        return video_path
    
    def _load_media(self, directory: str, extensions: set) -> list:
        '''Load media files from directory.'''
        media = []
        for filename in sorted(os.listdir(directory)):
            if os.path.splitext(filename)[1].lower() in extensions:
                media.append(os.path.join(directory, filename))
        return media
    
    def _final_cleanup(self, text: str) -> str:
        '''Final text cleanup - always runs.'''
        import re
        while re.search(r'(\d+)\.\s*(\d{3})', text):
            text = re.sub(r'(\d+)\.\s*(\d{3})', r'\1\2', text)
        text = re.sub(r',([^\s])', r', \1', text)
        text = re.sub(r'([nN])([kK]hởi)', r'\1 \2', text)
        text = re.sub(r'(án|ến|ông|ình|ất|ệt|ực)([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]{2,})', r'\1 \2', text)
        text = re.sub(r'([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ])([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ])', r'\1 \2', text)
        text = re.sub(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', lambda m: f"{'mùng' if int(m.group(1))<=10 else 'ngày'} {m.group(1)} tháng {m.group(2)} năm {m.group(3)}", text)
        text = re.sub(r'\b(\d{1,2})/(\d{1,2})\b', lambda m: f"{'mùng' if int(m.group(1))<=10 else 'ngày'} {m.group(1)} tháng {m.group(2)}", text)
        text = re.sub(r'\s+', ' ', text).strip()
        if text and text[-1] not in '.!?':
            last = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
            text = text[:last+1] if last > len(text)*0.7 else text + '.'
        return text
    
    def _export_summary(self, output_name: str, article: dict, intro: str, body: str, 
                       outro: str, full_script: str, url: str, timestamp: str) -> tuple:
        '''Export summary as text and JSON.'''
        summary_path = f"output/summaries/{output_name}.txt"
        summary_json_path = f"output/summaries/{output_name}.json"
        os.makedirs("output/summaries", exist_ok=True)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("ARTICLE SUMMARIZATION\n")
            f.write("="*70 + "\n\n")
            f.write(f"Title: {article['title']}\n")
            f.write(f"Source: {url}\n")
            f.write(f"Generated: {timestamp}\n")
            f.write(f"Word Count: {len(full_script.split())} words\n")
            f.write("\n" + "="*70 + "\n")
            f.write("INTRO\n" + "="*70 + "\n")
            f.write(intro + "\n")
            f.write("\n" + "="*70 + "\n")
            f.write("MAIN CONTENT\n" + "="*70 + "\n")
            f.write(body + "\n")
            f.write("\n" + "="*70 + "\n")
            f.write("OUTRO\n" + "="*70 + "\n")
            f.write(outro + "\n")
            f.write("\n" + "="*70 + "\n")
            f.write("FULL SCRIPT\n" + "="*70 + "\n")
            f.write(full_script + "\n")
        
        summary_data = {
            "title": article['title'],
            "source_url": url,
            "generated_at": timestamp,
            "word_count": len(full_script.split()),
            "intro": intro,
            "body": body,
            "outro": outro,
            "full_script": full_script,
            "images_count": len(article['images'])
        }
        
        with open(summary_json_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        return summary_path, summary_json_path
    
    def _update_summary_json(self, json_path: str, duration: float, video_path: str, 
                            audio_path: str, subtitle_path: str):
        '''Update JSON with final metadata.'''
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['duration_seconds'] = round(duration, 1)
        data['video_path'] = video_path
        data['audio_path'] = audio_path
        data['subtitle_path'] = subtitle_path
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    '''CLI entry point.'''
    print("\n" + "="*60)
    print("TikTok News Video Generator")
    print("="*60 + "\n")
    
    parser = argparse.ArgumentParser(description='TikTok News Video Generator')
    parser.add_argument('--url', type=str, help='News article URL')
    parser.add_argument('--image-dir', type=str, help='Custom image directory')
    parser.add_argument('--output', type=str, help='Output name (without extension)')
    parser.add_argument('--voice', type=str, default='binh', help='Voice (binh, tuyen, nguyen, son, vinh, huong, ly, ngoc, doan, dung)')
    parser.add_argument('--broll-dir', type=str, help='B-roll video directory')
    parser.add_argument('--template', type=str, help='Intro template (slide name/index)')
    parser.add_argument('--intro-duration', type=str, default='3', help='Intro duration (seconds or "none")')
    args = parser.parse_args()
    
    print("Available voices:")
    print("  Male Northern:   binh, tuyen")
    print("  Male Southern:   nguyen, son, vinh")
    print("  Female Northern: huong, ly, ngoc")
    print("  Female Southern: doan, dung\n")
    
    news_url = args.url or input("Enter news article URL: ").strip()
    if not news_url:
        print("Error: No URL provided")
        return
    
    intro_duration = None if args.intro_duration.lower() == 'none' else float(args.intro_duration)
    
    generator = TikTokNewsGenerator(
        voice=args.voice,
        image_dir=args.image_dir,
        broll_dir=args.broll_dir,
        template=args.template,
        intro_duration=intro_duration
    )
    
    try:
        video_path = generator.generate_video(news_url, output_name=args.output)
        print(f"\n🎉 Success! Video: {video_path}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
