"""Content Summarizer Module - Summarizes news to 45-second script"""
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import os
import re
from .text_preprocessor import TextPreprocessor

class ContentSummarizer:
    def __init__(self, language: str = "vietnamese", model_path: str = None):
        self.language = language
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.preprocessor = TextPreprocessor()
        
        if language == "vietnamese":
            # Use local model if available, otherwise download
            if model_path and os.path.exists(model_path):
                model_name = model_path
                print(f"Loading local model: {model_path}")
            elif os.path.exists("models/vit5-large-vietnews-summarization"):
                model_name = "models/vit5-large-vietnews-summarization"
                print(f"Loading local LARGE model: {model_name}")
            elif os.path.exists("models/vit5-base-vietnews-summarization"):
                model_name = "models/vit5-base-vietnews-summarization"
                print(f"Loading local BASE model: {model_name}")
            else:
                model_name = "VietAI/vit5-large-vietnews-summarization"
                print(f"Downloading LARGE model: {model_name}")
        else:
            model_name = "facebook/bart-large-cnn"
            print(f"Loading model: {model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, 
            legacy=False,
            use_fast=True  # Use fast tokenizer for better handling
        )
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)
        
        # Set pad token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        print(f"✓ Model loaded on {self.device}")
    
    def summarize(self, article: dict, target_words: int = 180) -> str:
        """
        Summarize article to ~180 words (45-50 seconds at 3.5-4 words/sec)
        Optimized for ViT5 Vietnamese summarization model
        """
        # Combine title, description, and content
        full_text = f"{article['title']}. {article['description']}. {article['content']}"
        
        # Preprocess text (convert dates, clean text)
        full_text = self.preprocessor.preprocess(full_text)
        
        # For ViT5, add </s> at the end as per official documentation
        if self.language == "vietnamese":
            full_text = full_text + " </s>"
        
        # Tokenize
        inputs = self.tokenizer(
            full_text,
            max_length=1024,
            truncation=True,
            return_tensors="pt",
            padding=True
        ).to(self.device)
        
        # Generate summary with optimized parameters
        with torch.no_grad():
            if self.language == "vietnamese":
                # ViT5-specific parameters (based on official documentation)
                summary_ids = self.model.generate(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    max_length=256,
                    min_length=150,
                    num_beams=4,  # Reduced from 5 for stability
                    length_penalty=1.2,  # Adjusted for better output
                    no_repeat_ngram_size=3,
                    early_stopping=True,
                    temperature=0.9,  # Add temperature for better quality
                    do_sample=False,  # Deterministic output
                    top_k=50,
                    top_p=0.95
                )
            else:
                # BART parameters
                summary_ids = self.model.generate(
                    inputs['input_ids'],
                    max_length=target_words + 30,
                    min_length=target_words - 10,
                    num_beams=4,
                    length_penalty=2.0,
                    early_stopping=True
                )
        
        summary = self.tokenizer.decode(
            summary_ids[0], 
            skip_special_tokens=True, 
            clean_up_tokenization_spaces=True
        )
        
        # Post-process the summary to remove garbled text
        summary = self.preprocessor.clean_text(summary)
        
        # Additional aggressive cleaning for model artifacts
        # Remove standalone uppercase Vietnamese characters (common artifacts)
        summary = re.sub(r'\s+[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]\s+', ' ', summary)
        summary = re.sub(r'\.\s*[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]\s+', '. ', summary)
        
        # Remove sentences with too many garbled characters
        sentences = summary.split('.')
        clean_sentences = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) == 0:
                continue
            # Count uppercase Vietnamese characters
            uppercase_viet = len(re.findall(r'[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', sent))
            # If less than 15% uppercase, keep it
            if uppercase_viet / len(sent) < 0.15:
                clean_sentences.append(sent)
        
        summary = '. '.join(clean_sentences)
        summary = summary.strip()
        
        # Final cleanup
        summary = re.sub(r'\s+', ' ', summary)
        summary = re.sub(r'\s+([.,;:!?])', r'\1', summary)
        
        return summary
    
    def create_script(self, article: dict) -> dict:
        """Create TikTok script - returns ONLY the body summary (no intro/outro)"""
        summary = self.summarize(article)
        
        # Return ONLY the body summary
        # Intro and outro will be added AFTER text correction
        return {
            'body': summary,
            'word_count': len(summary.split()),
            'title': article['title']  # Keep title for later use
        }
