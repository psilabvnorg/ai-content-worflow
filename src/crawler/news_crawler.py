"""News Crawler Module - Scrapes Vietnamese news sites"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import os
from urllib.parse import urljoin, urlparse

class NewsCrawler:
    def __init__(self, output_dir: str = "output/images"):
        self.output_dir = output_dir
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        os.makedirs(output_dir, exist_ok=True)
    
    def crawl_vnexpress(self, url: str) -> Dict:
        """Crawl article from VnExpress"""
        response = requests.get(url, headers=self.headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('h1', class_='title-detail')
        title_text = title.get_text(strip=True) if title else ""
        
        # Extract description
        desc = soup.find('p', class_='description')
        description = desc.get_text(strip=True) if desc else ""
        
        # Extract content
        content_div = soup.find('article', class_='fck_detail')
        paragraphs = content_div.find_all('p', class_='Normal') if content_div else []
        content = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        # Extract images
        images = []
        if content_div:
            img_tags = content_div.find_all('img')
            for idx, img in enumerate(img_tags[:8]):  # Max 8 images
                img_url = img.get('data-src') or img.get('src')
                if img_url:
                    img_path = self._download_image(img_url, f"vnexpress_{idx}")
                    if img_path:
                        images.append(img_path)
        
        return {
            'title': title_text,
            'description': description,
            'content': content,
            'images': images,
            'source': 'VnExpress',
            'url': url
        }
    
    def crawl_tienphong(self, url: str) -> Dict:
        """Crawl article from Tien Phong"""
        response = requests.get(url, headers=self.headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('h1', class_='article-title')
        title_text = title.get_text(strip=True) if title else ""
        
        # Extract description
        desc = soup.find('h2', class_='article-sapo')
        description = desc.get_text(strip=True) if desc else ""
        
        # Extract content
        content_div = soup.find('div', class_='article-body')
        paragraphs = content_div.find_all('p') if content_div else []
        content = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        # Extract images
        images = []
        if content_div:
            img_tags = content_div.find_all('img')
            for idx, img in enumerate(img_tags[:8]):
                img_url = img.get('data-src') or img.get('src')
                if img_url:
                    img_path = self._download_image(img_url, f"tienphong_{idx}")
                    if img_path:
                        images.append(img_path)
        
        return {
            'title': title_text,
            'description': description,
            'content': content,
            'images': images,
            'source': 'Tien Phong',
            'url': url
        }
    
    def crawl_article(self, url: str) -> Dict:
        """Auto-detect and crawl article from URL"""
        domain = urlparse(url).netloc
        
        if 'vnexpress' in domain:
            return self.crawl_vnexpress(url)
        elif 'tienphong' in domain:
            return self.crawl_tienphong(url)
        else:
            raise ValueError(f"Unsupported news site: {domain}")
    
    def _download_image(self, img_url: str, prefix: str) -> str:
        """Download image and return local path"""
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
