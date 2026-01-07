"""Text Normalizer - Prepares text for better TTS pronunciation"""
import re

class TextNormalizer:
    def __init__(self):
        # Common Vietnamese proper nouns that TTS often mispronounces
        self.proper_nouns = {
            'Venezuela': 'Vê-nê-zu-ê-la',
            'Maduro': 'Ma-đu-rô',
            'Mỹ': 'Mỹ',
            'Tây Ban Nha': 'Tây Ban Nha',
            'Tòa án': 'Tòa án',
            'phiên điều trần': 'phiên điều trần',
            'tổng thống': 'tổng thống',
        }
        
        # Protected phrases that should NOT be normalized
        self.protected_phrases = [
            "Tin nóng",
            "Theo dõi và follow kênh Tiktok của PSI để cập nhật thêm tin tức",
            "PSI"
        ]
    
    def normalize_for_tts(self, text: str) -> str:
        """Normalize text to improve TTS pronunciation
        
        Preserves protected phrases (intro/outro) from normalization
        """
        
        # Store protected phrases temporarily
        protected_map = {}
        temp_text = text
        for i, phrase in enumerate(self.protected_phrases):
            if phrase in temp_text:
                placeholder = f"__PROTECTED_{i}__"
                protected_map[placeholder] = phrase
                temp_text = temp_text.replace(phrase, placeholder)
        
        # 1. Add pauses at punctuation for better pacing
        temp_text = re.sub(r'([.!?])\s+', r'\1 ... ', temp_text)
        
        # 2. Add spaces around numbers for clearer pronunciation
        temp_text = re.sub(r'(\d+)', r' \1 ', temp_text)
        
        # 3. Ensure proper spacing
        temp_text = re.sub(r'\s+', ' ', temp_text)
        
        # 4. Add slight pauses before important proper nouns
        for noun in self.proper_nouns.keys():
            temp_text = temp_text.replace(noun, f' {noun} ')
        
        # 5. Clean up extra spaces
        temp_text = re.sub(r'\s+', ' ', temp_text).strip()
        
        # Restore protected phrases
        for placeholder, phrase in protected_map.items():
            temp_text = temp_text.replace(placeholder, phrase)
        
        return temp_text
    
    def denormalize_for_display(self, text: str) -> str:
        """Remove TTS-specific formatting for display"""
        
        # Remove extra pauses
        text = text.replace(' ... ', ' ')
        
        # Clean up spacing
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
