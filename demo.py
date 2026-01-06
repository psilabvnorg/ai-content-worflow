#!/usr/bin/env python3
"""
Demo script for TikTok News Video Generator
Shows the complete workflow with example URLs
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from main import TikTokNewsGenerator

def print_banner():
    print("\n" + "="*70)
    print("  🎬 TIKTOK NEWS VIDEO GENERATOR - DEMO")
    print("="*70 + "\n")

def demo_workflow():
    """Demonstrate the complete workflow"""
    
    print_banner()
    
    print("This demo will:")
    print("  1. Crawl a Vietnamese news article")
    print("  2. Summarize it using AI")
    print("  3. Generate Vietnamese voice-over")
    print("  4. Create synchronized subtitles")
    print("  5. Compose a TikTok-ready video (9:16, 1080x1920)")
    print("\n" + "-"*70 + "\n")
    
    # Get URL from user
    print("📰 Supported news sites:")
    print("   • VnExpress: https://vnexpress.net/...")
    print("   • Tien Phong: https://tienphong.vn/...")
    print()
    
    news_url = input("Enter news article URL: ").strip()
    
    if not news_url:
        print("\n❌ No URL provided. Exiting.")
        return
    
    # Validate URL
    if not ('vnexpress.net' in news_url or 'tienphong.vn' in news_url):
        print("\n⚠️  Warning: URL may not be supported. Trying anyway...")
    
    print("\n" + "-"*70 + "\n")
    
    # Initialize generator
    print("🚀 Initializing TikTok News Generator...")
    print("   Language: Vietnamese")
    print("   TTS: Microsoft Edge TTS (Vietnamese Male Voice)")
    print("   Summarization: VietAI/vit5-base-vietnews-summarization")
    print()
    
    try:
        generator = TikTokNewsGenerator(language="vietnamese")
        
        # Generate video
        output_name = input("Output filename (press Enter for auto): ").strip()
        if not output_name:
            output_name = None
        
        print("\n" + "="*70)
        print("  STARTING VIDEO GENERATION...")
        print("="*70 + "\n")
        
        video_path = generator.generate_video(news_url, output_name=output_name)
        
        # Success message
        print("\n" + "="*70)
        print("  🎉 SUCCESS!")
        print("="*70)
        print(f"\n📹 Video saved to: {video_path}")
        print(f"📁 Full path: {os.path.abspath(video_path)}")
        print("\n✅ Video is ready for TikTok upload!")
        print("\nVideo specifications:")
        print("  • Resolution: 1080x1920 (9:16)")
        print("  • Format: MP4 (H.264)")
        print("  • Frame rate: 30 FPS")
        print("  • Audio: AAC codec")
        print("  • Subtitles: Embedded")
        print("\n" + "="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
    except Exception as e:
        print("\n" + "="*70)
        print("  ❌ ERROR OCCURRED")
        print("="*70)
        print(f"\nError: {e}")
        print("\nDebug information:")
        import traceback
        traceback.print_exc()
        print("\n" + "="*70 + "\n")

def main():
    """Main entry point"""
    try:
        demo_workflow()
    except KeyboardInterrupt:
        print("\n\nExiting...")

if __name__ == "__main__":
    main()
