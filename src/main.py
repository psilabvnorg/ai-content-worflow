"""Main Orchestrator - TikTok News Video Generator"""
import os
import sys
import argparse
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from crawler.news_crawler import NewsCrawler
from processor.content_summarizer import ContentSummarizer
from processor.text_corrector import TextCorrector
from processor.text_normalizer import TextNormalizer
from processor.news_refiner import NewsRefiner
from processor.subtitle_aligner import SubtitleAligner
from media.tts_generator import TTSGenerator
from media.subtitle_generator import SubtitleGenerator
from media.video_composer import VideoComposer
from publisher.social_publisher import SocialPublisher

class TikTokNewsGenerator:
    def __init__(self, language: str = "vietnamese", image_dir: str = None, voice: str = None, 
                 broll_dir: str = None, template: str = None, intro_duration: float = 3.0):
        self.language = language
        self.custom_image_dir = image_dir
        self.broll_dir = broll_dir
        self.template = template  # PowerPoint template slide name
        self.intro_duration = intro_duration  # None = full video, float = seconds
        
        # Initialize modules
        print("Initializing TikTok News Generator...")
        self.crawler = NewsCrawler()
        self.summarizer = ContentSummarizer(language=language)
        self.text_corrector = TextCorrector()
        self.text_normalizer = TextNormalizer()
        self.news_refiner = NewsRefiner()
        self.subtitle_aligner = SubtitleAligner()
        self.tts = TTSGenerator(language=language, voice=voice)
        self.subtitle_gen = SubtitleGenerator()
        self.video_composer = VideoComposer()
        self.publisher = SocialPublisher(platform="tiktok")
        
        if image_dir:
            print(f"✓ Using custom image directory: {image_dir}")
        if broll_dir:
            print(f"✓ Using B-roll directory: {broll_dir}")
        if template:
            print(f"✓ Using intro template: {template}")
        if intro_duration is None:
            print(f"✓ Intro duration: full video")
        else:
            print(f"✓ Intro duration: {intro_duration}s")
        
        print("✓ All modules initialized!\n")
    
    def generate_video(self, news_url: str, output_name: str = None) -> str:
        """Complete pipeline: URL → TikTok Video"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_name:
            output_name = f"tiktok_news_{timestamp}"
        
        print(f"\n{'='*60}")
        print(f"GENERATING TIKTOK VIDEO")
        print(f"{'='*60}\n")
        
        # Step 1: Crawl article
        print("📰 Step 1: Crawling article...")
        article = self.crawler.crawl_article(news_url)
        print(f"   ✓ Title: {article['title'][:60]}...")
        print(f"   ✓ Images: {len(article['images'])} downloaded")
        
        # Initialize B-roll videos list
        broll_videos = []
        
        # Load B-roll videos if directory specified
        if self.broll_dir and os.path.isdir(self.broll_dir):
            broll_videos = self._load_broll_videos(self.broll_dir)
            if broll_videos:
                print(f"   ✓ Found {len(broll_videos)} B-roll videos from B-roll directory")
        
        # Use custom image directory if specified
        if self.custom_image_dir and os.path.isdir(self.custom_image_dir):
            custom_images = self._load_custom_images(self.custom_image_dir)
            if custom_images:
                article['images'] = custom_images
                print(f"   ✓ Using {len(custom_images)} images from custom directory: {self.custom_image_dir}")
            
            # Also load B-roll videos from the same directory
            broll_from_images = self._load_broll_videos(self.custom_image_dir)
            if broll_from_images:
                broll_videos.extend(broll_from_images)
                print(f"   ✓ Found {len(broll_from_images)} B-roll videos in image directory")
        
        if len(article['images']) < 3:
            print("   ⚠ Warning: Less than 3 images found. Video may be short.")
        
        # Step 2: Summarize content (body only, no intro/outro)
        print("\n📝 Step 2: Summarizing content...")
        script = self.summarizer.create_script(article)
        print(f"   ✓ Body: {script['word_count']} words")
        print(f"   Preview: {script['body'][:100]}...")
        
        # Step 2.5: Correct text spelling and diacritics (body only)
        print("\n🔧 Step 2.5: Correcting text...")
        script = self.text_corrector.correct_script(script)
        print(f"   ✓ Corrected body: {script['word_count']} words")
        print(f"   Preview: {script['body'][:100]}...")
        
        # Step 2.8: Refine news summarization with Qwen3:4B
        print("\n✨ Step 2.8: Refining news summarization...")
        print("   Using Qwen3:4B to improve grammar, spelling, punctuation, and wording...")
        script = self.news_refiner.refine_script(script)
        print(f"   ✓ Refined body: {script['word_count']} words")
        
        # Step 2.9: Final cleanup - ALWAYS runs to fix any remaining issues
        print("\n🧹 Step 2.9: Final text cleanup...")
        script['body'] = self._final_text_cleanup(script['body'])
        script['word_count'] = len(script['body'].split())
        print(f"   ✓ Final body: {script['word_count']} words")
        
        # Step 2.6: Add intro and outro AFTER correction
        print("\n📌 Step 2.6: Adding intro and outro...")
        if self.language == "vietnamese":
            intro = f"Tin nóng: {script['title'][:50]}..."
            outro = "Theo dõi và follow kênh Tiktok của PSI để cập nhật thêm tin tức!"
        else:
            intro = f"Breaking: {script['title'][:50]}..."
            outro = "Follow for more updates!"
        
        # Add break pacing for natural pauses
        # SSML break tags work with edge-tts
        # For other TTS, we use punctuation and spacing
        intro_with_break = f"{intro}... "  # Triple dots + space for pause
        outro_with_break = f" ... {outro}"  # Pause before outro (space before dots)
        
        # Build full script with breaks for natural pacing
        # The pauses help separate intro, body, and outro
        full_script = f"{intro_with_break}{script['body']}{outro_with_break}"
        
        script['intro'] = intro
        script['outro'] = outro
        script['script'] = full_script
        script['word_count'] = len(full_script.split())
        
        print(f"   ✓ Intro: {intro}")
        print(f"   ✓ Outro: {outro}")
        print(f"   ✓ Full script: {script['word_count']} words")
        print(f"   ✓ Added break pacing for natural pauses")
        
        # Step 2.7: Export summarization
        print("\n📄 Step 2.7: Exporting summarization...")
        summary_path = f"output/summaries/{output_name}.txt"
        summary_json_path = f"output/summaries/{output_name}.json"
        os.makedirs("output/summaries", exist_ok=True)
        
        # Export as text file
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("ARTICLE SUMMARIZATION\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Title: {script['title']}\n")
            f.write(f"Source: {news_url}\n")
            f.write(f"Generated: {timestamp}\n")
            f.write(f"Word Count: {script['word_count']} words\n")
            f.write("\n" + "="*70 + "\n")
            f.write("INTRO\n")
            f.write("="*70 + "\n")
            f.write(script['intro'] + "\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("MAIN CONTENT (CORRECTED)\n")
            f.write("="*70 + "\n")
            f.write(script['body'] + "\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("OUTRO\n")
            f.write("="*70 + "\n")
            f.write(script['outro'] + "\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("FULL SCRIPT (FOR TTS)\n")
            f.write("="*70 + "\n")
            f.write(script['script'] + "\n")
        
        # Export as JSON file (without duration yet)
        import json
        summary_data = {
            "title": script['title'],
            "source_url": news_url,
            "generated_at": timestamp,
            "word_count": script['word_count'],
            "intro": script['intro'],
            "body": script['body'],
            "outro": script['outro'],
            "full_script": script['script'],
            "images_count": len(article['images'])
        }
        
        with open(summary_json_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✓ Summary saved to: {summary_path}")
        print(f"   ✓ JSON data saved to: {summary_json_path}")
        
        # Step 3: Generate voice-over (with full script including intro/outro)
        print("\n🎤 Step 3: Generating voice-over...")
        audio_path = f"output/audio/{output_name}.mp3"
        os.makedirs("output/audio", exist_ok=True)
        self.tts.generate(full_script, audio_path)
        audio_duration = self.tts.get_audio_duration(audio_path)
        print(f"   ✓ Audio duration: {audio_duration:.1f} seconds")
        
        # Step 4: Generate subtitles
        print("\n💬 Step 4: Generating subtitles...")
        subtitle_path = f"output/temp/{output_name}.srt"
        os.makedirs("output/temp", exist_ok=True)
        # DO NOT pass text corrector - use Whisper output as-is
        # The script is already corrected before TTS, so Whisper should transcribe it correctly
        self.subtitle_gen.generate_from_audio(audio_path, subtitle_path)
        
        # Step 4.5: Align subtitles with original script using Qwen3:4b
        print("\n🔄 Step 4.5: Aligning subtitles with original script...")
        print("   Using Qwen3:4b to match subtitle timing with corrected text...")
        self.subtitle_aligner.align_subtitles(subtitle_path, full_script)
        
        # Step 5: Compose video
        print("\n🎬 Step 5: Composing video...")
        video_path = f"output/videos/{output_name}.mp4"
        os.makedirs("output/videos", exist_ok=True)
        
        # Background music path
        background_music = "assets/background_music.mp3"
        if not os.path.exists(background_music):
            print(f"   ⚠ Background music not found at {background_music}")
            background_music = None
        
        self.video_composer.create_video(
            images=article['images'],
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            output_path=video_path,
            audio_duration=audio_duration,
            background_music_path=background_music,
            title=script['title'],
            broll_videos=broll_videos if broll_videos else None,
            template=self.template,
            intro_duration=self.intro_duration
        )
        
        # Step 6: Update JSON with duration and file paths
        print("\n📝 Step 6: Updating summary with duration and paths...")
        summary_data['duration_seconds'] = round(audio_duration, 1)
        summary_data['video_path'] = video_path
        summary_data['audio_path'] = audio_path
        summary_data['subtitle_path'] = subtitle_path
        
        with open(summary_json_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        print(f"   ✓ Updated JSON with duration: {audio_duration:.1f}s")
        
        # Step 7: Prepare for publishing
        print("\n📤 Step 7: Preparing for upload...")
        metadata = self.publisher.prepare_metadata(article, script)
        upload_info = self.publisher.upload_video(video_path, metadata)
        
        print(f"\n{'='*60}")
        print(f"✅ VIDEO GENERATION COMPLETE!")
        print(f"{'='*60}")
        print(f"Video:    {video_path}")
        print(f"Summary:  {summary_path}")
        print(f"JSON:     {summary_json_path}")
        print(f"Duration: {audio_duration:.1f} seconds")
        print(f"Resolution: 1080x1920 (9:16)")
        print(f"{'='*60}\n")
        
        return video_path
    
    def _load_custom_images(self, image_dir: str) -> list:
        """Load images from custom directory"""
        supported_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        images = []
        
        for filename in sorted(os.listdir(image_dir)):
            ext = os.path.splitext(filename)[1].lower()
            if ext in supported_extensions:
                images.append(os.path.join(image_dir, filename))
        
        return images
    
    def _load_broll_videos(self, broll_dir: str) -> list:
        """Load B-roll videos from directory"""
        supported_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
        videos = []
        
        for filename in sorted(os.listdir(broll_dir)):
            ext = os.path.splitext(filename)[1].lower()
            if ext in supported_extensions:
                videos.append(os.path.join(broll_dir, filename))
        
        return videos
    
    def _final_text_cleanup(self, text: str) -> str:
        """Final cleanup that ALWAYS runs - fixes numbers, dates, stuck words"""
        import re
        
        # Fix numbers with dots/spaces (Vietnamese thousand separator)
        # "1. 890" or "1.890" -> "1890"
        while re.search(r'(\d+)\.\s*(\d{3})', text):
            text = re.sub(r'(\d+)\.\s*(\d{3})', r'\1\2', text)
        
        # Fix comma without space after it
        text = re.sub(r',([^\s])', r', \1', text)
        
        # Fix stuck words - specific patterns
        text = re.sub(r'([nN])([kK]hởi)', r'\1 \2', text)  # khoánkhởi -> khoán khởi
        text = re.sub(r'(án|ến|ông|ình|ất|ệt|ực)([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]{2,})', r'\1 \2', text)
        
        # Fix lowercase followed by uppercase (stuck words)
        text = re.sub(r'([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ])([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ])', r'\1 \2', text)
        
        # Convert dates to Vietnamese text
        def convert_date_short(match):
            day = int(match.group(1))
            month = int(match.group(2))
            return f"mùng {day} tháng {month}" if day <= 10 else f"ngày {day} tháng {month}"
        
        def convert_date_full(match):
            day = int(match.group(1))
            month = int(match.group(2))
            year = match.group(3)
            return f"mùng {day} tháng {month} năm {year}" if day <= 10 else f"ngày {day} tháng {month} năm {year}"
        
        text = re.sub(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', convert_date_full, text)
        text = re.sub(r'\b(\d{1,2})/(\d{1,2})\b', convert_date_short, text)
        
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Ensure ends with complete sentence
        if text and text[-1] not in '.!?':
            last_period = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
            if last_period > len(text) * 0.7:
                text = text[:last_period + 1]
            else:
                text = text + '.'
        
        return text


def main():
    """Example usage with CLI arguments"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='TikTok News Video Generator')
    parser.add_argument('--url', type=str, help='News article URL')
    parser.add_argument('--image-dir', type=str, help='Custom directory for video images')
    parser.add_argument('--output', type=str, help='Output video name (without extension)')
    parser.add_argument('--voice', type=str, help='Voice name (binh, tuyen, nguyen, son, vinh, huong, ly, ngoc, doan, dung)')
    parser.add_argument('--broll-dir', type=str, help='Directory containing B-roll videos (mp4, mov, avi)')
    parser.add_argument('--template', type=str, help='Intro template name (slide name from templates/intro_template.pptx)')
    parser.add_argument('--intro-duration', type=str, default='3', 
                        help='Intro duration in seconds, or "none" for full video (default: 3)')
    
    args = parser.parse_args()
    
    print("TikTok News Video Generator")
    print("=" * 60)
    
    # Show available voices
    if args.voice:
        print(f"Using voice: {args.voice}")
    else:
        print("Using default voice: Binh (male Northern)")
    
    print("\nAvailable voices:")
    print("  Male Northern:  binh, tuyen")
    print("  Male Southern:  nguyen, son, vinh")
    print("  Female Northern: huong, ly, ngoc")
    print("  Female Southern: doan, dung")
    print("")
    
    # Get URL from argument or user input
    news_url = args.url
    if not news_url:
        news_url = input("\nEnter news article URL: ").strip()
    
    if not news_url:
        print("Error: No URL provided")
        return
    
    # Validate custom image directory if provided
    if args.image_dir:
        if not os.path.isdir(args.image_dir):
            print(f"Warning: Image directory not found: {args.image_dir}")
            args.image_dir = None
        else:
            print(f"Using custom image directory: {args.image_dir}")
    
    # Parse intro duration
    intro_duration = 3.0  # default
    if args.intro_duration:
        if args.intro_duration.lower() == 'none':
            intro_duration = None  # Full video
        else:
            try:
                intro_duration = float(args.intro_duration)
            except ValueError:
                print(f"Warning: Invalid intro duration '{args.intro_duration}', using default 3s")
                intro_duration = 3.0
    
    # Initialize generator
    generator = TikTokNewsGenerator(
        language="vietnamese", 
        image_dir=args.image_dir,
        voice=args.voice,
        broll_dir=args.broll_dir,
        template=args.template,
        intro_duration=intro_duration
    )
    
    # Generate video
    try:
        video_path = generator.generate_video(news_url, output_name=args.output)
        print(f"\n🎉 Success! Video saved to: {video_path}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
