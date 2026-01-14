"""Subtitle Aligner - Aligns Whisper output with original corrected script (supports word-level for karaoke)"""
from difflib import SequenceMatcher
import re

class SubtitleAligner:
    def __init__(self):
        self.similarity_threshold = 0.6  # 60% similarity to consider a match
    
    def align_subtitles_with_script(self, whisper_text: str, original_script: dict) -> str:
        """
        Compare Whisper transcription with original corrected script
        Replace incorrect Whisper text with correct script text
        
        Args:
            whisper_text: Full text from Whisper transcription
            original_script: Dict with 'intro', 'body', 'outro', 'script'
        
        Returns:
            Corrected text aligned with original script
        """
        if not original_script:
            return whisper_text
        
        print("\n🔍 Aligning subtitles with original corrected script...")
        
        # Get the original corrected script (ground truth)
        original_full = original_script.get('script', '')
        intro = original_script.get('intro', '')
        body = original_script.get('body', '')
        outro = original_script.get('outro', '')
        
        # Clean texts for comparison
        whisper_clean = self._clean_text(whisper_text)
        original_clean = self._clean_text(original_full)
        
        print(f"   Original script: {len(original_clean.split())} words")
        print(f"   Whisper output:  {len(whisper_clean.split())} words")
        
        # Use sequence matching to align texts
        aligned_text = self._align_with_sequence_matcher(
            whisper_text, original_full, intro, body, outro
        )
        
        return aligned_text
    
    def align_words_with_timing(self, whisper_words: list, original_script: dict) -> list:
        """
        Align individual words from Whisper with original script for karaoke mode
        
        Args:
            whisper_words: List of {'word': str, 'start': float, 'end': float}
            original_script: Dict with original corrected script
        
        Returns:
            List of aligned words with timing preserved
        """
        if not original_script:
            return whisper_words
        
        original_full = original_script.get('script', '')
        original_words = original_full.split()
        
        aligned_words = []
        original_idx = 0
        
        for w_info in whisper_words:
            whisper_word = w_info['word'].strip()
            
            # Find best matching word in original script (within a window)
            best_match = None
            best_ratio = 0
            best_idx = original_idx
            
            # Search within a window around current position
            window_start = max(0, original_idx - 3)
            window_end = min(len(original_words), original_idx + 5)
            
            for i in range(window_start, window_end):
                ratio = self._word_similarity(whisper_word, original_words[i])
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = original_words[i]
                    best_idx = i
            
            # Use original word if good match, otherwise keep Whisper word
            if best_ratio >= 0.7 and best_match:
                aligned_words.append({
                    'word': best_match,
                    'start': w_info['start'],
                    'end': w_info['end']
                })
                original_idx = best_idx + 1
            else:
                aligned_words.append(w_info)
                original_idx += 1
        
        return aligned_words
    
    def _word_similarity(self, word1: str, word2: str) -> float:
        """Calculate similarity between two words"""
        w1 = self._clean_text(word1)
        w2 = self._clean_text(word2)
        return SequenceMatcher(None, w1, w2).ratio()
    
    def _clean_text(self, text: str) -> str:
        """Clean text for comparison (lowercase, remove punctuation)"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _align_with_sequence_matcher(self, whisper_text: str, original_script: str,
                                     intro: str, body: str, outro: str) -> str:
        """Use sequence matching to align and correct Whisper output"""
        
        # Split into sentences for better alignment
        whisper_sentences = self._split_sentences(whisper_text)
        original_sentences = self._split_sentences(original_script)
        
        corrected_sentences = []
        
        for w_sent in whisper_sentences:
            best_match = None
            best_ratio = 0
            
            # Find best matching sentence in original script
            for o_sent in original_sentences:
                ratio = self._similarity(w_sent, o_sent)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = o_sent
            
            # If good match found, use original sentence
            if best_ratio >= self.similarity_threshold and best_match:
                corrected_sentences.append(best_match)
                print(f"   ✓ Matched ({best_ratio:.0%}): '{w_sent[:40]}...' → '{best_match[:40]}...'")
            else:
                # No good match, keep Whisper output but warn
                corrected_sentences.append(w_sent)
                if len(w_sent) > 10:  # Only warn for substantial text
                    print(f"   ⚠ No match ({best_ratio:.0%}): '{w_sent[:40]}...'")
        
        # Join corrected sentences
        corrected_text = ' '.join(corrected_sentences)
        
        # Ensure intro and outro are present
        corrected_text = self._ensure_intro_outro(corrected_text, intro, outro)
        
        return corrected_text
    
    def _split_sentences(self, text: str) -> list:
        """Split text into sentences"""
        # Split on sentence endings
        sentences = re.split(r'[.!?]+', text)
        # Clean and filter empty
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity ratio between two texts"""
        clean1 = self._clean_text(text1)
        clean2 = self._clean_text(text2)
        return SequenceMatcher(None, clean1, clean2).ratio()
    
    def _ensure_intro_outro(self, text: str, intro: str, outro: str) -> str:
        """Ensure intro and outro are present in text"""
        text_lower = text.lower()
        
        # Check intro
        if intro and intro.lower() not in text_lower:
            print(f"   ✓ Adding missing intro: {intro[:40]}...")
            text = f"{intro} {text}"
        
        # Check outro
        if outro and outro.lower() not in text_lower:
            print(f"   ✓ Adding missing outro: {outro[:40]}...")
            text = f"{text} {outro}"
        
        return text
    
    def align_subtitle_chunks(self, subtitle_chunks: list, original_script: dict) -> list:
        """
        Align individual subtitle chunks with original script
        
        Args:
            subtitle_chunks: List of (text, start, end) tuples
            original_script: Dict with original corrected script
        
        Returns:
            List of corrected (text, start, end) tuples
        """
        if not original_script:
            return subtitle_chunks
        
        print("\n🔍 Aligning subtitle chunks with original script...")
        
        original_full = original_script.get('script', '')
        original_words = original_full.split()
        
        corrected_chunks = []
        
        for chunk_text, start, end in subtitle_chunks:
            # Find best matching segment in original script
            chunk_words = chunk_text.split()
            best_match = self._find_best_word_sequence(chunk_words, original_words)
            
            if best_match:
                corrected_chunks.append((best_match, start, end))
                if best_match != chunk_text:
                    print(f"   ✓ Corrected: '{chunk_text[:30]}...' → '{best_match[:30]}...'")
            else:
                corrected_chunks.append((chunk_text, start, end))
        
        return corrected_chunks
    
    def _find_best_word_sequence(self, chunk_words: list, original_words: list) -> str:
        """Find best matching word sequence in original text"""
        chunk_len = len(chunk_words)
        best_match = None
        best_ratio = 0
        
        # Slide window through original words
        for i in range(len(original_words) - chunk_len + 1):
            window = original_words[i:i + chunk_len]
            window_text = ' '.join(window)
            chunk_text = ' '.join(chunk_words)
            
            ratio = self._similarity(chunk_text, window_text)
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = window_text
        
        # Return match if similarity is good enough
        if best_ratio >= self.similarity_threshold:
            return best_match
        
        return None
