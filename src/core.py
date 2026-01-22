"""
Core Module - Consolidated news processing and content generation.

This module combines crawler, summarizer, and text processing into a single
cohesive class for efficient news article processing.
"""
import os
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List
from urllib.parse import urlparse
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


class NewsProcessor:
    '''
    Unified news processing class that handles crawling, summarization, and text correction.
    
    Responsibilities:
    - Crawl articles from Vietnamese news sites (VnExpress, TienPhong)
    - Summarize content using Qwen3:4B via Ollama
    - Correct Vietnamese spelling and diacritics
    - Normalize text for TTS
    '''
    
    def __init__(self, ollama_url: str = "http://172.18.96.1:11434", 
                 ollama_model: str = "qwen3-vl:4b", output_dir: str = "output/images"):
        '''
        Initialize the news processor with all required components.
        
        Args:
            ollama_url: URL for Ollama API server
            ollama_model: Model name for summarization
            output_dir: Directory to save downloaded images
        '''
        # Try to connect to Ollama, fallback to localhost if needed
        self.ollama_model = ollama_model
        self.output_dir = output_dir
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        os.makedirs(output_dir, exist_ok=True)
        
        # Test connection and fallback to localhost if needed
        self.ollama_url = self._test_ollama_connection(ollama_url)
        
        # Initialize text correction model
        self._init_corrector()
        
        print(f"✓ NewsProcessor initialized (Ollama: {self.ollama_url}, Model: {ollama_model})")
    
    def _test_ollama_connection(self, primary_url: str) -> str:
        '''Test Ollama connection and fallback to localhost if needed.'''
        urls_to_try = [primary_url, "http://localhost:11434", "http://127.0.0.1:11434"]
        
        for url in urls_to_try:
            try:
                response = requests.get(f"{url}/api/tags", timeout=2)
                if response.status_code == 200:
                    print(f"   ✓ Ollama connected: {url}")
                    return url
            except:
                continue
        
        print(f"   ⚠ Warning: Could not connect to Ollama at any URL")
        print(f"   Using: {primary_url} (may fail if not available)")
        return primary_url
    
    def _init_corrector(self):
        '''Initialize Vietnamese text correction model.'''
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model_path = "models/protonx-legal-tc" if os.path.exists("models/protonx-legal-tc") else "protonx-models/protonx-legal-tc"
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.corrector_model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(self.device)
        self.corrector_model.eval()
        print(f"   ✓ Text corrector loaded on {self.device}")
    
    def crawl_article(self, url: str) -> Dict:
        '''
        Crawl article from supported news sites.
        
        Args:
            url: Article URL
            
        Returns:
            Dictionary with title, description, content, images, source, url
        '''
        domain = urlparse(url).netloc
        if 'vnexpress' in domain:
            return self._crawl_vnexpress(url)
        elif 'tienphong' in domain:
            return self._crawl_tienphong(url)
        raise ValueError(f"Unsupported news site: {domain}")
    
    def _crawl_vnexpress(self, url: str) -> Dict:
        '''Crawl VnExpress article.'''
        response = requests.get(url, headers=self.headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('h1', class_='title-detail')
        desc = soup.find('p', class_='description')
        content_div = soup.find('article', class_='fck_detail')
        paragraphs = content_div.find_all('p', class_='Normal') if content_div else []
        
        images = []
        if content_div:
            for idx, img in enumerate(content_div.find_all('img')[:8]):
                img_url = img.get('data-src') or img.get('src')
                if img_url:
                    img_path = self._download_image(img_url, f"vnexpress_{idx}")
                    if img_path:
                        images.append(img_path)
        
        return {
            'title': title.get_text(strip=True) if title else "",
            'description': desc.get_text(strip=True) if desc else "",
            'content': ' '.join([p.get_text(strip=True) for p in paragraphs]),
            'images': images,
            'source': 'VnExpress',
            'url': url
        }
    
    def _crawl_tienphong(self, url: str) -> Dict:
        '''Crawl TienPhong article.'''
        response = requests.get(url, headers=self.headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('h1', class_='article-title')
        desc = soup.find('h2', class_='article-sapo')
        content_div = soup.find('div', class_='article-body')
        paragraphs = content_div.find_all('p') if content_div else []
        
        images = []
        if content_div:
            for idx, img in enumerate(content_div.find_all('img')[:8]):
                img_url = img.get('data-src') or img.get('src')
                if img_url:
                    img_path = self._download_image(img_url, f"tienphong_{idx}")
                    if img_path:
                        images.append(img_path)
        
        return {
            'title': title.get_text(strip=True) if title else "",
            'description': desc.get_text(strip=True) if desc else "",
            'content': ' '.join([p.get_text(strip=True) for p in paragraphs]),
            'images': images,
            'source': 'Tien Phong',
            'url': url
        }
    
    def _download_image(self, img_url: str, prefix: str) -> str:
        '''Download image and return local path.'''
        try:
            if not img_url.startswith('http'):
                return None
            response = requests.get(img_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                ext = img_url.split('.')[-1].split('?')[0][:4]
                filename = f"{prefix}_{hash(img_url) % 10000}.{ext}"
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return filepath
        except Exception as e:
            print(f"Failed to download image: {e}")
        return None
    
    def summarize(self, article: Dict, target_words: int = 350) -> str:
        '''
        Summarize article using Qwen3:4B with chunked processing.
        
        Args:
            article: Article dictionary from crawl_article
            target_words: Target word count for summary
            
        Returns:
            Summarized text
        '''
        content = f"{article.get('description', '')} {article.get('content', '')}".strip()
        
        if len(content) < 1500:
            return self._summarize_direct(article, target_words)
        
        chunks = self._split_into_chunks(content)
        print(f"   Splitting into {len(chunks)} chunks...")
        
        summaries = []
        for i, chunk in enumerate(chunks, 1):
            summary = self._summarize_chunk(chunk, i, len(chunks))
            if summary:
                summaries.append(summary)
        
        if not summaries:
            return self._fallback_summarize(article)
        
        return self._combine_summaries(article['title'], summaries, target_words)
    
    def _split_into_chunks(self, text: str) -> List[str]:
        '''Split text into chunks at sentence boundaries.'''
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks, current = [], ""
        
        for sentence in sentences:
            if len(current) + len(sentence) < 1500:
                current += " " + sentence if current else sentence
            else:
                if current:
                    chunks.append(current.strip())
                current = sentence
        
        if current:
            chunks.append(current.strip())
        return chunks if chunks else [text]
    
    def _summarize_chunk(self, chunk: str, chunk_num: int, total: int) -> str:
        '''Summarize a single chunk using Ollama.'''
        prompt = f"""Tóm tắt đoạn văn sau (phần {chunk_num}/{total}) thành 2-3 câu ngắn gọn:

"{chunk}"

Tóm tắt:"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.ollama_model, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.2, "num_predict": 500}},
                timeout=60
            )
            if response.status_code == 200:
                return re.sub(r'<think>.*?</think>', '', response.json().get('response', ''), flags=re.DOTALL).strip()
        except Exception as e:
            print(f"Chunk {chunk_num} error: {e}")
        return ""
    
    def _combine_summaries(self, title: str, summaries: List[str], target_words: int) -> str:
        '''Combine chunk summaries into final coherent summary.'''
        combined = " ".join(s for s in summaries if s)
        prompt = f"""Viết lại thành bài tin tức hoàn chỉnh, khoảng {target_words} từ.

Tiêu đề: {title}
Nội dung: {combined}

QUY TẮC: Số viết liền (1890), ngày viết chữ (mùng 8 tháng 1), câu hoàn chỉnh.

Bài tin:"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.ollama_model, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.3, "num_predict": 2000}},
                timeout=120
            )
            if response.status_code == 200:
                final = response.json().get('response', '').strip()
                return self._clean_text(final) if final and len(final.split()) >= 80 else self._clean_text(combined)
        except Exception as e:
            print(f"Combine error: {e}")
        return self._clean_text(combined)
    
    def _summarize_direct(self, article: Dict, target_words: int) -> str:
        '''Direct summarization for short articles.'''
        prompt = f"""Tóm tắt bài báo sau thành khoảng {target_words} từ:

Tiêu đề: {article['title']}
Nội dung: {article.get('description', '')} {article.get('content', '')}

QUY TẮC: Số viết liền, ngày viết chữ, câu hoàn chỉnh.

Tóm tắt:"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.ollama_model, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.2, "num_predict": 2000}},
                timeout=120
            )
            if response.status_code == 200:
                return self._clean_text(response.json().get('response', '').strip())
        except Exception as e:
            print(f"Direct summarize error: {e}")
        return self._fallback_summarize(article)
    
    def _fallback_summarize(self, article: Dict) -> str:
        '''Simple fallback if Qwen fails.'''
        content = article.get('content', article.get('description', ''))
        sentences = re.split(r'[.!?]', content)
        summary = '. '.join(s.strip() for s in sentences[:12] if s.strip())
        return self._clean_text(summary + '.' if summary else article['title'])
    
    def _clean_text(self, text: str) -> str:
        '''Clean and normalize text output from LLM.'''
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        prefixes = ["Đây là", "Tóm tắt:", "Đoạn văn", "Dưới đây", "Kết quả:", "Bài tin:"]
        for prefix in prefixes:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip().lstrip(':').strip()
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        while re.search(r'(\d+)\.\s*(\d{3})', text):
            text = re.sub(r'(\d+)\.\s*(\d{3})', r'\1\2', text)
        text = re.sub(r',([^\s])', r', \1', text)
        text = re.sub(r'([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ])([A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ])', r'\1 \2', text)
        text = re.sub(r'([nN])([kK]hởi)', r'\1 \2', text)
        text = re.sub(r'(án|ến|ông|ình|ất|ệt|ực)([a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]{2,})', r'\1 \2', text)
        text = re.sub(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', lambda m: f"{'mùng' if int(m.group(1))<=10 else 'ngày'} {m.group(1)} tháng {m.group(2)} năm {m.group(3)}", text)
        text = re.sub(r'\b(\d{1,2})/(\d{1,2})\b', lambda m: f"{'mùng' if int(m.group(1))<=10 else 'ngày'} {m.group(1)} tháng {m.group(2)}", text)
        text = re.sub(r'\s+', ' ', text).strip()
        if text and text[-1] not in '.!?':
            last = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
            text = text[:last+1] if last > len(text)*0.7 else text + '.'
        return text
    
    def correct_text(self, text: str) -> str:
        '''
        Correct Vietnamese spelling and diacritics.
        
        Args:
            text: Text to correct
            
        Returns:
            Corrected text
        '''
        if not text or len(text.strip()) == 0:
            return text
        words = text.split()
        max_words = int(160 * 0.75)
        corrected_chunks = []
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i+max_words])
            try:
                inputs = self.tokenizer(chunk, return_tensors="pt", truncation=True, max_length=160).to(self.device)
                with torch.no_grad():
                    outputs = self.corrector_model.generate(**inputs, num_beams=10, max_new_tokens=160, early_stopping=True)
                corrected_chunks.append(self.tokenizer.decode(outputs[0], skip_special_tokens=True))
            except Exception as e:
                print(f"Correction failed: {e}")
                corrected_chunks.append(chunk)
        return ' '.join(corrected_chunks)
    
    def refine_text(self, text: str) -> str:
        '''
        Refine text using Qwen3:4B for grammar and style improvements.
        
        Args:
            text: Text to refine
            
        Returns:
            Refined text
        '''
        prompt = f"""Chỉnh sửa văn bản tin tức sau:

QUY TẮC:
1. Sửa lỗi ngữ pháp và chính tả
2. Mỗi từ PHẢI cách nhau bằng dấu cách
3. Số viết liền: 1.890 → 1890
4. Ngày viết chữ: 8/1 → mùng 8 tháng 1
5. Giữ nguyên nội dung
6. Kết thúc bằng câu hoàn chỉnh

Văn bản: "{text}"

Văn bản đã sửa:"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.ollama_model, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.2, "num_predict": 2000}},
                timeout=120
            )
            if response.status_code == 200:
                refined = response.json().get('response', '').strip()
                if refined and 0.5 < len(refined)/len(text) < 1.5:
                    return self._clean_text(refined)
        except Exception as e:
            print(f"Refine error: {e}")
        return text
