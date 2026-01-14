"""News Refiner Module - Refines summarization using Qwen3:4B via Ollama"""
import requests
import json
import re

class NewsRefiner:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "qwen3:4b"
        
        # Verify model availability
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                # Find qwen3 model first, then qwen
                qwen3_models = [name for name in model_names if 'qwen3' in name.lower()]
                qwen_models = [name for name in model_names if 'qwen' in name.lower()]
                if qwen3_models:
                    self.model = qwen3_models[0]
                elif qwen_models:
                    self.model = qwen_models[0]
                print(f"✓ News Refiner using Ollama model: {self.model}")
        except Exception as e:
            print(f"⚠ Cannot connect to Ollama: {e}")
    
    def refine_script(self, script_dict: dict) -> dict:
        """
        Refine the news summarization:
        - Correct grammatical errors
        - Fix spelling mistakes
        - Improve punctuation
        - Make wording more natural and professional (news-reporting style)
        """
        print("Refining news content with Qwen3:4B...")
        
        if 'body' not in script_dict or not script_dict['body']:
            print("   ⚠ No body content to refine")
            return script_dict
        
        original_body = script_dict['body']
        
        # Refine the body text
        refined_body = self._refine_text(original_body)
        
        if refined_body:
            script_dict['body'] = refined_body
            script_dict['word_count'] = len(refined_body.split())
            print(f"   ✓ Body refined ({len(original_body)} → {len(refined_body)} chars)")
            print(f"   Before: {original_body[:80]}...")
            print(f"   After:  {refined_body[:80]}...")
        
        return script_dict
    
    def _refine_text(self, text: str) -> str:
        """Use Qwen3:4B to refine the text"""
        
        # Use a clearer prompt format with /no_think
        prompt = f"""/no_think
Nhiệm vụ: Chỉnh sửa văn bản tin tức sau đây.

QUY TẮC BẮT BUỘC:
1. Sửa lỗi ngữ pháp và chính tả
2. Mỗi từ PHẢI cách nhau bằng dấu cách (SAI: "chứng khoánkhởi" → ĐÚNG: "chứng khoán khởi")
3. Số viết liền không dấu chấm: 1.890 → 1890, 2.500.000 → 2500000
4. Ngày tháng viết bằng chữ: 8/1 → mùng 8 tháng 1, 11/09/2001 → ngày 11 tháng 9 năm 2001
5. Giữ nguyên toàn bộ nội dung và ý nghĩa
6. Kết thúc bằng câu hoàn chỉnh (dấu chấm)

Văn bản gốc:
"{text}"

Văn bản đã chỉnh sửa:"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Lower temperature for more consistent output
                        "num_predict": 2000
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                refined_text = result.get('message', {}).get('content', '').strip()
                
                # Clean up the response
                refined_text = self._clean_response(refined_text)
                
                # Validate the refinement
                if self._is_valid_refinement(text, refined_text):
                    return refined_text
                else:
                    print(f"   ⚠ Invalid refinement, keeping original")
                    return text
            else:
                print(f"   ⚠ Qwen API error: {response.status_code}")
                return text
                
        except requests.exceptions.Timeout:
            print(f"   ⚠ Qwen request timeout")
            return text
        except Exception as e:
            print(f"   ⚠ Error calling Qwen: {e}")
            return text
    
    def _clean_response(self, text: str) -> str:
        """Clean up the model response and fix common issues"""
        # Remove common prefixes the model might add
        prefixes_to_remove = [
            "Đây là đoạn văn đã chỉnh sửa:",
            "Đoạn văn đã chỉnh sửa:",
            "Kết quả:",
            "Đoạn văn sau khi chỉnh sửa:",
            "Văn bản đã chỉnh sửa:",
            "CHỈ đoạn văn đã được chỉnh sửa",
            "Dưới đây là văn bản đã chỉnh sửa:",
        ]
        
        for prefix in prefixes_to_remove:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
            # Also check if it contains only the prefix
            if text.lower().strip() == prefix.lower().strip():
                return ""
        
        # Remove quotes if the model wrapped the response
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        if text.startswith("'") and text.endswith("'"):
            text = text[1:-1]
        
        # Remove thinking tags
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
        # Fix numbers with spaces or dots (Vietnamese thousand separator)
        # "1. 890" or "1.890" -> "1890"
        while re.search(r'(\d+)\.\s*(\d{3})', text):
            text = re.sub(r'(\d+)\.\s*(\d{3})', r'\1\2', text)
        
        # Fix comma without space after it
        text = re.sub(r',([^\s])', r', \1', text)
        
        # Fix stuck words (missing spaces) - common Vietnamese patterns
        # Pattern: lowercase letter followed by uppercase
        text = re.sub(r'([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ])([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ])', r'\1 \2', text)
        # Specific fix for "khoánkhởi" -> "khoán khởi"
        text = re.sub(r'([nN])([kK]hởi)', r'\1 \2', text)
        # Common Vietnamese word endings that shouldn't be stuck
        text = re.sub(r'(án|ến|ông|ình|ất|ệt|ực)([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]{2,})', r'\1 \2', text)
        
        # Convert date formats to Vietnamese text
        def convert_date_short(match):
            day = int(match.group(1))
            month = int(match.group(2))
            if day <= 10:
                return f"mùng {day} tháng {month}"
            return f"ngày {day} tháng {month}"
        
        def convert_date_full(match):
            day = int(match.group(1))
            month = int(match.group(2))
            year = match.group(3)
            if day <= 10:
                return f"mùng {day} tháng {month} năm {year}"
            return f"ngày {day} tháng {month} năm {year}"
        
        text = re.sub(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', convert_date_full, text)
        text = re.sub(r'\b(\d{1,2})/(\d{1,2})\b', convert_date_short, text)
        
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Ensure text ends with complete sentence
        if text and text[-1] not in '.!?':
            last_period = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
            if last_period > len(text) * 0.7:
                text = text[:last_period + 1]
            else:
                text = text + '.'
        
        return text.strip()
    
    def _is_valid_refinement(self, original: str, refined: str) -> bool:
        """Validate that the refinement is reasonable"""
        if not refined:
            return False
        
        # Check if refined text is just instruction echo
        invalid_patterns = [
            "chỉ đoạn văn",
            "đã được chỉnh sửa",
            "văn bản đã chỉnh sửa",
            "không giải thích",
        ]
        refined_lower = refined.lower()
        for pattern in invalid_patterns:
            if pattern in refined_lower and len(refined) < 100:
                print(f"   ⚠ Response appears to be instruction echo")
                return False
        
        # Check length - refined should be similar length (within 50%)
        len_ratio = len(refined) / len(original) if original else 0
        if len_ratio < 0.5 or len_ratio > 1.5:
            print(f"   ⚠ Length ratio out of bounds: {len_ratio:.2f}")
            return False
        
        # Check word count - should be similar
        original_words = len(original.split())
        refined_words = len(refined.split())
        word_ratio = refined_words / original_words if original_words else 0
        if word_ratio < 0.5 or word_ratio > 1.5:
            print(f"   ⚠ Word count ratio out of bounds: {word_ratio:.2f}")
            return False
        
        return True
