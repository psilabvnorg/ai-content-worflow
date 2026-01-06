"""Content Summarizer Module - Summarizes news to 45-second script"""
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class ContentSummarizer:
    def __init__(self, language: str = "vietnamese"):
        self.language = language
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if language == "vietnamese":
            model_name = "VietAI/vit5-base-vietnews-summarization"
        else:
            model_name = "facebook/bart-large-cnn"
        
        print(f"Loading summarization model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)
    
    def summarize(self, article: dict, target_words: int = 120) -> str:
        """
        Summarize article to ~120 words (45 seconds at 2.5 words/sec)
        """
        # Combine title, description, and content
        full_text = f"{article['title']}. {article['description']}. {article['content']}"
        
        # Tokenize
        inputs = self.tokenizer(
            full_text,
            max_length=1024,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)
        
        # Generate summary
        with torch.no_grad():
            summary_ids = self.model.generate(
                inputs['input_ids'],
                max_length=target_words + 20,
                min_length=target_words - 20,
                num_beams=4,
                length_penalty=2.0,
                early_stopping=True
            )
        
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary
    
    def create_script(self, article: dict) -> dict:
        """Create TikTok script with intro, body, outro"""
        summary = self.summarize(article)
        
        # Structure for TikTok
        if self.language == "vietnamese":
            intro = f"Tin nóng: {article['title'][:50]}..."
            outro = "Theo dõi để cập nhật thêm tin tức!"
        else:
            intro = f"Breaking: {article['title'][:50]}..."
            outro = "Follow for more updates!"
        
        script = f"{intro} {summary} {outro}"
        
        return {
            'script': script,
            'intro': intro,
            'body': summary,
            'outro': outro,
            'word_count': len(script.split())
        }
