"""Text Preprocessor - Clean and normalize Vietnamese text"""
import re

class TextPreprocessor:
    def __init__(self):
        self.month_names = {
            '1': 'một', '2': 'hai', '3': 'ba', '4': 'tư', '5': 'năm', '6': 'sáu',
            '7': 'bảy', '8': 'tám', '9': 'chín', '10': 'mười', '11': 'mười một', '12': 'mười hai'
        }
    
    def convert_date_to_text(self, text: str) -> str:
        """Convert dates like 17/3/2019 to 'Ngày 17 tháng 3 năm 2019'"""
        # Pattern: DD/MM/YYYY or D/M/YYYY
        pattern = r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b'
        
        def replace_date(match):
            day = match.group(1)
            month = match.group(2)
            year = match.group(3)
            
            month_text = self.month_names.get(month.lstrip('0'), month)
            return f"ngày {day} tháng {month_text} năm {year}"
        
        text = re.sub(pattern, replace_date, text)
        
        # Pattern: DD-MM-YYYY or D-M-YYYY
        pattern2 = r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b'
        text = re.sub(pattern2, replace_date, text)
        
        return text
    
    def convert_numbers_to_text(self, text: str) -> str:
        """Convert common numbers to Vietnamese text"""
        # This is a simplified version - can be expanded
        replacements = {
            r'\b2024\b': 'hai nghìn không trăm hai mươi bốn',
            r'\b2025\b': 'hai nghìn không trăm hai mươi lăm',
            r'\b2026\b': 'hai nghìn không trăm hai mươi sáu',
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove garbled Vietnamese characters (common model artifacts)
        # These are uppercase Vietnamese characters that shouldn't appear
        garbled_patterns = [
            r'[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]{3,}',  # 3+ uppercase Vietnamese
            r'\.[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]{2,}',  # Dot followed by uppercase
        ]
        
        for pattern in garbled_patterns:
            text = re.sub(pattern, '', text)
        
        # Remove standalone uppercase Vietnamese characters
        text = re.sub(r'\s+[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]{1,2}\s+', ' ', text)
        
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s\.,;:!?\-/()]', '', text)
        
        # Normalize Vietnamese characters
        text = text.strip()
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def preprocess(self, text: str) -> str:
        """Full preprocessing pipeline"""
        text = self.clean_text(text)
        text = self.convert_date_to_text(text)
        # Uncomment if you want number conversion
        # text = self.convert_numbers_to_text(text)
        return text
