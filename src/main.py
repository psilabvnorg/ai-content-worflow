"""Main Orchestrator - TikTok News Video Generator"""
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from crawler.news_crawler import NewsCrawler
from processor.content_summarizer import ContentSummarizer
from media.tts_generator import TTSGenerator
from media.subtitle_generator import SubtitleGenerator
from media.video_composer import VideoComposer
from publisher.social_publisher import SocialPublisher

class TikTokNewsGenerator:
    def __init__(self, language: str = "vietnamese", tts_model_path: str = None):
        self.language = language
        
        # Initialize modules
        print("Initializing TikTok News Generator...")
        self.crawler = NewsCrawler()
        self.summarizer = ContentSummarizer(language=language)
        self.tts = TTSGenerator(language=language, model_path=tts_model_path)
        self.subtitle_gen = SubtitleGenerator()
        self.video_composer = VideoComposer()
        self.publisher = SocialPublisher(platform="tiktok")
        
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
        
        if len(article['images']) < 3:
            print("   ⚠ Warning: Less than 3 images found. Video may be short.")
        
        # Step 2: Summarize content
        print("\n📝 Step 2: Summarizing content...")
        script = self.summarizer.create_script(article)
        print(f"   ✓ Script: {script['word_count']} words")
        print(f"   Preview: {script['script'][:100]}...")
        
        # Step 3: Generate voice-over
        print("\n🎤 Step 3: Generating voice-over...")
        audio_path = f"output/audio/{output_name}.mp3"
        os.makedirs("output/audio", exist_ok=True)
        self.tts.generate(script['script'], audio_path)
        audio_duration = self.tts.get_audio_duration(audio_path)
        print(f"   ✓ Audio duration: {audio_duration:.1f} seconds")
        
        # Step 4: Generate subtitles
        print("\n💬 Step 4: Generating subtitles...")
        subtitle_path = f"output/temp/{output_name}.srt"
        os.makedirs("output/temp", exist_ok=True)
        self.subtitle_gen.generate_from_script(script['script'], audio_duration, subtitle_path)
        
        # Step 5: Compose video
        print("\n🎬 Step 5: Composing video...")
        video_path = f"output/videos/{output_name}.mp4"
        os.makedirs("output/videos", exist_ok=True)
        self.video_composer.create_video(
            images=article['images'],
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            output_path=video_path,
            audio_duration=audio_duration
        )
        
        # Step 6: Prepare for publishing
        print("\n📤 Step 6: Preparing for upload...")
        metadata = self.publisher.prepare_metadata(article, script)
        upload_info = self.publisher.upload_video(video_path, metadata)
        
        print(f"\n{'='*60}")
        print(f"✅ VIDEO GENERATION COMPLETE!")
        print(f"{'='*60}")
        print(f"Output: {video_path}")
        print(f"Duration: {audio_duration:.1f} seconds")
        print(f"Resolution: 1080x1920 (9:16)")
        print(f"{'='*60}\n")
        
        return video_path


def main():
    """Example usage"""
    
    # Example Vietnamese news URLs:
    # VnExpress: https://vnexpress.net/...
    # Tien Phong: https://tienphong.vn/...
    
    print("TikTok News Video Generator")
    print("=" * 60)
    
    # Get URL from user
    news_url = input("\nEnter news article URL: ").strip()
    
    if not news_url:
        print("Error: No URL provided")
        return
    
    # Optional: Specify TTS model path for Vietnamese
    # tts_model = "models/tts/deepman3909.onnx"
    tts_model = None  # Will use edge-tts
    
    # Initialize generator
    generator = TikTokNewsGenerator(language="vietnamese", tts_model_path=tts_model)
    
    # Generate video
    try:
        video_path = generator.generate_video(news_url)
        print(f"\n🎉 Success! Video saved to: {video_path}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
