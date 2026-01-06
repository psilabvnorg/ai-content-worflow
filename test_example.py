"""Quick test example for TikTok News Generator"""
import sys
sys.path.insert(0, 'src')

from main import TikTokNewsGenerator

# Example Vietnamese news URLs (replace with actual URLs):
EXAMPLE_URLS = {
    'vnexpress': 'https://vnexpress.net/bong-da',  # Replace with actual article URL
    'tienphong': 'https://tienphong.vn/the-thao'   # Replace with actual article URL
}

def test_generator():
    """Test the video generator"""
    
    print("Testing TikTok News Video Generator")
    print("=" * 60)
    
    # Use a real news URL here
    test_url = input("Enter a Vietnamese news article URL: ").strip()
    
    if not test_url:
        print("No URL provided. Exiting.")
        return
    
    # Initialize generator (using edge-tts for Vietnamese)
    generator = TikTokNewsGenerator(language="vietnamese")
    
    # Generate video
    try:
        video_path = generator.generate_video(test_url, output_name="test_video")
        print(f"\n✅ Test successful! Video: {video_path}")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generator()
