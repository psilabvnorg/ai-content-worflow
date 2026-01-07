"""Subtitle Generator Module - Creates synchronized subtitles using Whisper"""
import pysrt
import whisper
import os
from .subtitle_aligner import SubtitleAligner

class SubtitleGenerator:
    def __init__(self):
        self.subs = pysrt.SubRipFile()
        self.model = None
        self.text_corrector = None
        self.original_script = None  # Store original script with intro/outro
        self.aligner = SubtitleAligner()  # Add subtitle aligner
        # Fixed phrases that should NOT be corrected
        self.protected_phrases = [
            "Tin nóng",
            "Theo dõi và follow kênh Tiktok của PSI để cập nhật thêm tin tức",
            "PSI"
        ]
    
    def set_text_corrector(self, corrector):
        """Set text corrector for post-processing Whisper output"""
        self.text_corrector = corrector
    
    def set_original_script(self, script_dict):
        """Set original script with intro/outro for reference"""
        self.original_script = script_dict
    
    def _should_correct_chunk(self, chunk_text: str) -> bool:
        """Check if chunk contains protected phrases that shouldn't be corrected"""
        chunk_lower = chunk_text.lower()
        for phrase in self.protected_phrases:
            if phrase.lower() in chunk_lower:
                return False
        return True
    
    def _ensure_intro_outro(self, transcribed_text: str) -> str:
        """Ensure intro and outro are present in transcribed text"""
        if not self.original_script:
            return transcribed_text
        
        intro = self.original_script.get('intro', '')
        outro = self.original_script.get('outro', '')
        
        # Check if intro is missing or garbled
        if intro and intro.lower() not in transcribed_text.lower():
            print(f"   ⚠ Intro missing in transcription, adding: {intro}")
            transcribed_text = f"{intro} {transcribed_text}"
        
        # Check if outro is missing or garbled
        if outro and outro.lower() not in transcribed_text.lower():
            print(f"   ⚠ Outro missing in transcription, adding: {outro}")
            transcribed_text = f"{transcribed_text} {outro}"
        
        return transcribed_text
    
    def generate_from_audio(self, audio_path: str, output_path: str) -> str:
        """Generate SRT subtitles from audio using Whisper for accurate timing"""
        try:
            print("Loading Whisper model for accurate subtitle timing...")
            
            # Load Whisper model (base is good balance of speed/accuracy)
            if self.model is None:
                self.model = whisper.load_model("base")
            
            print("Transcribing audio with word-level timestamps...")
            
            # Transcribe with word timestamps
            result = self.model.transcribe(
                audio_path,
                language="vi",  # Vietnamese
                word_timestamps=True,
                verbose=False
            )
            
            # Get full transcribed text
            full_transcription = result['text']
            
            print(f"   ✓ Whisper transcription: {full_transcription[:100]}...")
            
            # CRITICAL: Align Whisper output with original corrected script
            # This replaces incorrect Whisper transcriptions with correct text
            if self.original_script:
                full_transcription = self.aligner.align_subtitles_with_script(
                    full_transcription, 
                    self.original_script
                )
                print(f"   ✓ Aligned with original script: {full_transcription[:100]}...")
            else:
                # Fallback: ensure intro and outro are present
                full_transcription = self._ensure_intro_outro(full_transcription)

            
            print(f"   ✓ Transcription: {full_transcription[:100]}...")
            
            # Create subtitles from word-level timestamps
            self.subs = pysrt.SubRipFile()
            
            # Collect chunks with timing for later alignment
            temp_chunks = []
            
            # Group words into chunks of 8-10 words
            words_per_chunk = 9
            current_chunk = []
            chunk_start = None
            
            for segment in result['segments']:
                if 'words' in segment:
                    for word_info in segment['words']:
                        word = word_info['word'].strip()
                        start = word_info['start']
                        end = word_info['end']
                        
                        if chunk_start is None:
                            chunk_start = start
                        
                        current_chunk.append(word)
                        
                        # Create subtitle when we have enough words or at sentence end
                        if len(current_chunk) >= words_per_chunk or word.endswith(('.', '!', '?', ':')):
                            chunk_text = ' '.join(current_chunk)
                            temp_chunks.append((chunk_text, chunk_start, end))
                            
                            # Reset for next chunk
                            current_chunk = []
                            chunk_start = None
            
            # Add any remaining words
            if current_chunk and chunk_start is not None:
                chunk_text = ' '.join(current_chunk)
                end = result['segments'][-1]['end'] if result['segments'] else 0
                temp_chunks.append((chunk_text, chunk_start, end))
            
            # CRITICAL: Align chunks with original script
            # This replaces Whisper text with correct text from original script
            if self.original_script:
                print(f"\n🔍 Aligning {len(temp_chunks)} subtitle chunks with original script...")
                temp_chunks = self.aligner.align_subtitle_chunks(temp_chunks, self.original_script)
            
            # Create final subtitle items from aligned chunks
            for idx, (chunk_text, start, end) in enumerate(temp_chunks, 1):
                # Convert to SubRipTime format
                start_hours = int(start // 3600)
                start_minutes = int((start % 3600) // 60)
                start_seconds = int(start % 60)
                start_millis = int((start % 1) * 1000)
                
                end_hours = int(end // 3600)
                end_minutes = int((end % 3600) // 60)
                end_seconds = int(end % 60)
                end_millis = int((end % 1) * 1000)
                
                sub = pysrt.SubRipItem(
                    index=idx,
                    start={'hours': start_hours, 'minutes': start_minutes,
                           'seconds': start_seconds, 'milliseconds': start_millis},
                    end={'hours': end_hours, 'minutes': end_minutes,
                         'seconds': end_seconds, 'milliseconds': end_millis},
                    text=chunk_text
                )
                self.subs.append(sub)
            
            # Save SRT file
            self.subs.save(output_path, encoding='utf-8')
            alignment_note = " (aligned with original script)" if self.original_script else ""
            print(f"✓ Generated {len(self.subs)} subtitles with accurate timing{alignment_note}")
            return output_path
            
        except Exception as e:
            print(f"Warning: Whisper failed ({e}), falling back to text-based timing")
            return self._fallback_generation(audio_path, output_path)
    
    def _fallback_generation(self, audio_path: str, output_path: str) -> str:
        """Fallback to simple timing if Whisper fails"""
        # This shouldn't be called, but just in case
        print("Using fallback subtitle generation")
        return output_path
    
    def generate_from_script(self, script: str, audio_duration: float, output_path: str) -> str:
        """Deprecated: Use generate_from_audio instead"""
        print("Warning: generate_from_script is deprecated, use generate_from_audio for accurate timing")
        return output_path
    
    def get_subtitles(self) -> pysrt.SubRipFile:
        """Return subtitle object for video overlay"""
        return self.subs
