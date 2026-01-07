"""Test that intro and outro are NOT corrected"""
import sys
sys.path.insert(0, 'src')

from processor.text_corrector import TextCorrector

# Initialize corrector
corrector = TextCorrector()

# Test script with intro, body, outro
test_script = {
    'intro': 'Tin nóng: Ông Maduro tuyên bố tôi vô tội...',
    'body': 'Trong phía diệu trần, ông Maduro nói bằng tiếng Tây Bà Nhà rằng ông là tổng thống Vê Nê Duê La.',
    'outro': 'Theo dõi và follow kênh Tiktok của PSI để cập nhật thêm tin tức!',
    'script': '',
    'word_count': 0
}

print("="*80)
print("TESTING PROTECTED PHRASES (INTRO/OUTRO)")
print("="*80)

print("\n--- BEFORE CORRECTION ---")
print(f"Intro:  {test_script['intro']}")
print(f"Body:   {test_script['body']}")
print(f"Outro:  {test_script['outro']}")

# Apply correction
corrected = corrector.correct_script(test_script)

print("\n--- AFTER CORRECTION ---")
print(f"Intro:  {corrected['intro']}")
print(f"Body:   {corrected['body']}")
print(f"Outro:  {corrected['outro']}")

print("\n--- VERIFICATION ---")
if corrected['intro'] == test_script['intro']:
    print("✅ Intro preserved (NOT corrected)")
else:
    print(f"❌ Intro was changed: '{test_script['intro']}' → '{corrected['intro']}'")

if corrected['outro'] == test_script['outro']:
    print("✅ Outro preserved (NOT corrected)")
else:
    print(f"❌ Outro was changed: '{test_script['outro']}' → '{corrected['outro']}'")

if corrected['body'] != test_script['body']:
    print("✅ Body was corrected (as expected)")
else:
    print("⚠️  Body was NOT corrected")

print("\n--- FULL SCRIPT ---")
print(corrected['script'])

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
