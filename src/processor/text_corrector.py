"""Text Corrector Module - Corrects Vietnamese spelling and diacritics"""
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os

class TextCorrector:
    def __init__(self, model_path: str = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Use local model if available
        if model_path and os.path.exists(model_path):
            model_name = model_path
            print(f"Loading text correction model: {model_path}")
        elif os.path.exists("models/protonx-legal-tc"):
            model_name = "models/protonx-legal-tc"
            print(f"Loading local text correction model: {model_name}")
        else:
            model_name = "protonx-models/protonx-legal-tc"
            print(f"Downloading text correction model: {model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)
        self.model.eval()
        
        self.max_tokens = 160  # Model's max context length
        
        print(f"✓ Text correction model loaded on {self.device}")
    
    def correct_text(self, text: str, aggressive: bool = False) -> str:
        """Correct Vietnamese text spelling and diacritics
        
        Args:
            text: Text to correct
            aggressive: If True, applies more aggressive correction (double-pass, higher beam search)
        """
        if not text or len(text.strip()) == 0:
            return text
        
        # Split long text into chunks (max 160 tokens)
        # Approximate: 1 token ≈ 0.75 words for Vietnamese
        words = text.split()
        max_words_per_chunk = int(self.max_tokens * 0.75)
        
        corrected_chunks = []
        
        for i in range(0, len(words), max_words_per_chunk):
            chunk_words = words[i:i + max_words_per_chunk]
            chunk_text = ' '.join(chunk_words)
            
            # Correct this chunk
            corrected_chunk = self._correct_chunk(chunk_text, aggressive=aggressive)
            corrected_chunks.append(corrected_chunk)
        
        # Join all corrected chunks
        corrected_text = ' '.join(corrected_chunks)
        return corrected_text
    
    def _correct_chunk(self, text: str, aggressive: bool = False) -> str:
        """Correct a single chunk of text"""
        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=self.max_tokens
            ).to(self.device)
            
            # Generate correction with more aggressive parameters
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    num_beams=15 if aggressive else 10,  # More beam search for aggressive mode
                    num_return_sequences=1,
                    max_new_tokens=self.max_tokens,
                    early_stopping=True,
                    return_dict_in_generate=True,
                    output_scores=True,
                    temperature=0.7 if aggressive else 1.0,  # Lower temperature for more conservative corrections
                    do_sample=False
                )
            
            # Decode
            sequences = outputs.sequences
            corrected = self.tokenizer.decode(sequences[0], skip_special_tokens=True)
            
            # If aggressive mode, apply correction twice
            if aggressive and corrected != text:
                # Second pass correction
                inputs2 = self.tokenizer(
                    corrected,
                    return_tensors="pt",
                    truncation=True,
                    max_length=self.max_tokens
                ).to(self.device)
                
                with torch.no_grad():
                    outputs2 = self.model.generate(
                        **inputs2,
                        num_beams=15,
                        num_return_sequences=1,
                        max_new_tokens=self.max_tokens,
                        early_stopping=True
                    )
                
                corrected = self.tokenizer.decode(outputs2[0], skip_special_tokens=True)
            
            return corrected
            
        except Exception as e:
            print(f"Warning: Text correction failed for chunk: {e}")
            return text
    
    def correct_script(self, script_dict: dict) -> dict:
        """Correct only the body of the script"""
        print("Correcting script body with ProtonX text correction model...")
        
        # Only correct the body
        if 'body' in script_dict:
            original_body = script_dict['body']
            script_dict['body'] = self.correct_text(script_dict['body'])
            if original_body != script_dict['body']:
                print(f"   Body corrected (showing first 100 chars)")
                print(f"   Before: {original_body[:100]}...")
                print(f"   After:  {script_dict['body'][:100]}...")
        
        print(f"✓ Body corrected")
        return script_dict
