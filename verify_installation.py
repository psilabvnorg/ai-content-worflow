#!/usr/bin/env python3
"""Verify TikTok News Generator Installation"""

import sys
import os

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python version OK")
        return True
    else:
        print("❌ Python 3.8+ required")
        return False

def check_packages():
    """Check required packages"""
    packages = {
        'torch': 'PyTorch',
        'transformers': 'Transformers',
        'moviepy': 'MoviePy',
        'edge_tts': 'Edge-TTS',
        'onnxruntime': 'ONNX Runtime',
        'bs4': 'BeautifulSoup4',
        'requests': 'Requests',
        'PIL': 'Pillow',
        'cv2': 'OpenCV',
        'pysrt': 'pysrt',
        'numpy': 'NumPy'
    }
    
    all_ok = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - NOT INSTALLED")
            all_ok = False
    
    return all_ok

def check_directories():
    """Check required directories"""
    dirs = [
        'src',
        'src/crawler',
        'src/processor',
        'src/media',
        'src/publisher',
        'output',
        'output/videos',
        'output/audio',
        'output/images',
        'output/temp',
        'models/tts'
    ]
    
    all_ok = True
    for dir_path in dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - MISSING")
            all_ok = False
    
    return all_ok

def check_modules():
    """Check custom modules"""
    modules = [
        'src.crawler.news_crawler',
        'src.processor.content_summarizer',
        'src.media.tts_generator',
        'src.media.video_composer',
        'src.media.subtitle_generator',
        'src.publisher.social_publisher',
        'src.main'
    ]
    
    sys.path.insert(0, 'src')
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module} - ERROR: {e}")
            all_ok = False
    
    return all_ok

def check_ffmpeg():
    """Check ffmpeg installation"""
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              timeout=5)
        if result.returncode == 0:
            print("✅ ffmpeg installed")
            return True
        else:
            print("⚠️  ffmpeg not found (required for video encoding)")
            return False
    except:
        print("⚠️  ffmpeg not found (install: sudo apt install ffmpeg)")
        return False

def main():
    """Run all checks"""
    print_header("TIKTOK NEWS GENERATOR - INSTALLATION VERIFICATION")
    
    print_header("1. Python Version")
    python_ok = check_python_version()
    
    print_header("2. Required Packages")
    packages_ok = check_packages()
    
    print_header("3. Directory Structure")
    dirs_ok = check_directories()
    
    print_header("4. Custom Modules")
    modules_ok = check_modules()
    
    print_header("5. External Dependencies")
    ffmpeg_ok = check_ffmpeg()
    
    print_header("VERIFICATION SUMMARY")
    
    all_checks = [
        ("Python Version", python_ok),
        ("Required Packages", packages_ok),
        ("Directory Structure", dirs_ok),
        ("Custom Modules", modules_ok),
        ("FFmpeg", ffmpeg_ok)
    ]
    
    for check_name, status in all_checks:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check_name}")
    
    print("\n" + "="*70)
    
    if all([status for _, status in all_checks]):
        print("\n🎉 ALL CHECKS PASSED! System is ready to use.")
        print("\nQuick start:")
        print("  $ source venv/bin/activate")
        print("  $ python demo.py")
    else:
        print("\n⚠️  Some checks failed. Please review errors above.")
        if not ffmpeg_ok:
            print("\nNote: FFmpeg is required for video encoding.")
            print("Install: sudo apt install ffmpeg")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
