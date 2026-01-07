"""Test improved text correction with aggressive mode"""
import sys
sys.path.insert(0, 'src')

from processor.text_corrector import TextCorrector
from processor.text_normalizer import TextNormalizer

# Test cases with common TTS pronunciation errors
test_texts = [
    "Tình nổng, ông Maduro tuyên bố tôi vô tội ở Toa Án Mỹ",
    "Trong phía diệu trần, ông Maduro nói bằng tiếng Tây Bà Nhà",
    "ông là tổng thống Vê Nê Duê La",
    "Kim ngạch xuất khẩu 475 tỷ đô la Mỹ năm 2025",
    "Chính sách thuyết minh vẫn gây sức F lên tỷ trọng",
]

print("="*80)
print("TESTING IMPROVED TEXT CORRECTION")
print("="*80)

# Initialize corrector and normalizer
corrector = TextCorrector()
normalizer = TextNormalizer()

for i, text in enumerate(test_texts, 1):
    print(f"\n--- Test {i} ---")
    print(f"Original:  {text}")
    
    # Standard correction
    corrected = corrector.correct_text(text, aggressive=False)
    print(f"Standard:  {corrected}")
    
    # Aggressive correction (double-pass)
    corrected_aggressive = corrector.correct_text(text, aggressive=True)
    print(f"Aggressive: {corrected_aggressive}")
    
    # Normalized for TTS
    normalized = normalizer.normalize_for_tts(corrected_aggressive)
    print(f"TTS-ready: {normalized}")

print("\n" + "="*80)
print("CORRECTION TEST COMPLETE")
print("="*80)
