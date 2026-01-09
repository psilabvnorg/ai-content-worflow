"""Main Orchestrator - TikTok News Video Generator"""
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from crawler.news_crawler import NewsCrawler
from processor.content_summarizer import ContentSummarizer
from processor.text_corrector import TextCorrector
from processor.text_normalizer import TextNormalizer
from processor.subtitle_aligner import SubtitleAligner
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
        self.text_corrector = TextCorrector()  # Add text corrector
        self.text_normalizer = TextNormalizer()  # Add text normalizer for TTS
        self.subtitle_aligner = SubtitleAligner()  # Add subtitle aligner
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
            title=script['title']  # Pass title for intro
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
    
    # Use NGHI-TTS model (ngocngan3701 - Northern Vietnamese male voice)
    tts_model = "models/voice_model/ngocngan3701.onnx"
    
    if not os.path.exists(tts_model):
        print(f"Warning: TTS model not found at {tts_model}")
        print("Will use edge-tts fallback")
        tts_model = None
    else:
        print(f"Using NGHI-TTS model: {os.path.basename(tts_model)}")
    
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
