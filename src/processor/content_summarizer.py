"""Content Summarizer Module - Summarizes news using Qwen3:4B via Ollama with chunked processing"""
import requests
import re

OLLAMA_URL = "http://172.18.96.1:11434/api/generate"
OLLAMA_MODEL = "qwen3-vl:4b"

class ContentSummarizer:
    def __init__(self, language: str = "vietnamese", ollama_url: str = "http://172.18.96.1:11434", model: str = "qwen3-vl:4b"):
        self.language = language
        self.ollama_url = ollama_url
        self.model = model
        self.max_chunk_chars = 1500  # Keep chunks small for 4b model
        
        print(f"[LLM] Initializing Content Summarizer", flush=True)
        print(f"[LLM] Using API: {OLLAMA_URL}", flush=True)
        print(f"[LLM] Using model: {OLLAMA_MODEL}", flush=True)
    
    def _split_into_chunks(self, text: str) -> list:
        """Split text into chunks at sentence boundaries"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < self.max_chunk_chars:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text]
    
    def _summarize_chunk(self, chunk: str, chunk_num: int, total_chunks: int) -> str:
        """Summarize a single chunk"""
        prompt = f"""Tóm tắt đoạn văn sau (phần {chunk_num}/{total_chunks}) thành 2-3 câu ngắn gọn, giữ nguyên thông tin quan trọng:

"{chunk}"

Tóm tắt ngắn gọn:"""

        try:
            print(f"[LLM] Processing chunk {chunk_num}/{total_chunks}", flush=True)
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 500
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('response', '').strip()
                summary = re.sub(r'<think>.*?</think>', '', summary, flags=re.DOTALL)
                return summary.strip()
        except Exception as e:
            print(f"[LLM] Chunk {chunk_num} error: {e}", flush=True)
        
        return ""
    
    def _combine_summaries(self, title: str, summaries: list, target_words: int = 350) -> str:
        """Combine chunk summaries into final coherent summary"""
        combined = " ".join(s for s in summaries if s)
        
        prompt = f"""Bạn là biên tập viên tin tức. Viết lại đoạn tóm tắt sau thành bài tin tức hoàn chỉnh, mạch lạc, khoảng {target_words} từ để đọc trên TikTok.

Tiêu đề: {title}

Nội dung tóm tắt:
{combined}

QUY TẮC:
1. Viết thành đoạn văn liền mạch, hoàn chỉnh
2. Số viết liền: 1.890 → 1890
3. Ngày tháng viết chữ: 8/1 → mùng 8 tháng 1
4. Kết thúc bằng câu hoàn chỉnh

Bài tin tức hoàn chỉnh:"""

        try:
            print(f"[LLM] Combining summaries into final article", flush=True)
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 2000
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                final = result.get('response', '').strip()
                final = self._clean_summary(final)
                if final and len(final.split()) >= 80:
                    return final
        except Exception as e:
            print(f"[LLM] Combine error: {e}", flush=True)
        
        # Fallback: just clean and return combined
        return self._clean_summary(combined)
    
    def summarize(self, article: dict, target_words: int = 350) -> str:
        """Summarize article using chunked processing"""
        
        content = article.get('content', '')
        description = article.get('description', '')
        title = article.get('title', '')
        
        full_text = f"{description} {content}".strip()
        
        # If text is short enough, process directly
        if len(full_text) < self.max_chunk_chars:
            return self._summarize_direct(article, target_words)
        
        # Split into chunks
        chunks = self._split_into_chunks(full_text)
        print(f"   Splitting into {len(chunks)} chunks for processing...")
        
        # Summarize each chunk
        summaries = []
        for i, chunk in enumerate(chunks, 1):
            print(f"      Processing chunk {i}/{len(chunks)}...")
            summary = self._summarize_chunk(chunk, i, len(chunks))
            if summary:
                summaries.append(summary)
        
        if not summaries:
            return self._fallback_summarize(article)
        
        # Combine summaries into final text
        print(f"   Combining {len(summaries)} summaries...")
        final = self._combine_summaries(title, summaries, target_words)
        
        return final
    
    def _summarize_direct(self, article: dict, target_words: int) -> str:
        """Direct summarization for short articles"""
        full_text = f"Tiêu đề: {article['title']}\n\nNội dung: {article.get('description', '')} {article.get('content', '')}"
        
        prompt = f"""Tóm tắt bài báo sau thành khoảng {target_words} từ:

{full_text}

QUY TẮC: Số viết liền (1890 không phải 1.890), ngày viết chữ (mùng 8 tháng 1), câu hoàn chỉnh.

Tóm tắt:"""

        try:
            print(f"[LLM] Direct summarization for article", flush=True)
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 2000
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('response', '').strip()
                return self._clean_summary(summary)
        except Exception as e:
            print(f"[LLM] Direct summarize error: {e}", flush=True)
        
        return self._fallback_summarize(article)
    
    def _clean_summary(self, text: str) -> str:
        """Clean up the model response"""
        # Remove thinking tags
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
        # Remove common prefixes
        prefixes = ["Đây là", "Tóm tắt:", "Đoạn văn", "Dưới đây", "Kết quả:", "Bài tin tức:"]
        for prefix in prefixes:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
                if text.startswith(':'):
                    text = text[1:].strip()
        
        # Remove quotes
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        
        # Fix numbers with dots/spaces
        while re.search(r'(\d+)\.\s*(\d{3})', text):
            text = re.sub(r'(\d+)\.\s*(\d{3})', r'\1\2', text)
        
        # Fix comma without space
        text = re.sub(r',([^\s])', r', \1', text)
        
        # Fix stuck words
        text = re.sub(r'([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ])([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ])', r'\1 \2', text)
        text = re.sub(r'([nN])([kK]hởi)', r'\1 \2', text)
        text = re.sub(r'(án|ến|ông|ình|ất|ệt|ực)([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]{2,})', r'\1 \2', text)
        
        # Convert dates
        def convert_date_short(match):
            day, month = int(match.group(1)), int(match.group(2))
            return f"mùng {day} tháng {month}" if day <= 10 else f"ngày {day} tháng {month}"
        
        def convert_date_full(match):
            day, month, year = int(match.group(1)), int(match.group(2)), match.group(3)
            return f"mùng {day} tháng {month} năm {year}" if day <= 10 else f"ngày {day} tháng {month} năm {year}"
        
        text = re.sub(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', convert_date_full, text)
        text = re.sub(r'\b(\d{1,2})/(\d{1,2})\b', convert_date_short, text)
        
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Ensure complete sentence
        if text and text[-1] not in '.!?':
            last = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
            if last > len(text) * 0.7:
                text = text[:last + 1]
            else:
                text = text + '.'
        
        return text
    
    def _fallback_summarize(self, article: dict) -> str:
        """Simple fallback if Qwen fails"""
        content = article.get('content', article.get('description', ''))
        sentences = re.split(r'[.!?]', content)
        summary = '. '.join(s.strip() for s in sentences[:12] if s.strip())
        return self._clean_summary(summary + '.' if summary else article['title'])
    
    def create_script(self, article: dict) -> dict:
        """Create TikTok script"""
        print("   Using Qwen3:4B with chunked processing...")
        summary = self.summarize(article)
        
        return {
            'body': summary,
            'word_count': len(summary.split()),
            'title': article['title']
        }
