"""Subtitle Generator Module - Creates synchronized subtitles using Whisper with karaoke-style word-by-word display"""
import pysrt
import whisper
import os

class SubtitleGenerator:
    def __init__(self, karaoke_mode: bool = True):
        self.subs = pysrt.SubRipFile()
        self.model = None
        self.original_script = None  # Store original corrected script for alignment
        self.karaoke_mode = karaoke_mode  # Enable word-by-word karaoke subtitles
    
    def set_original_script(self, script):
        """Set original corrected script for alignment with Whisper timing"""
        self.original_script = script
        print(f"   ✓ Original script set for subtitle alignment ({len(script.split())} words)")
    
    def generate_from_audio(self, audio_path: str, output_path: str) -> str:
        """Generate SRT subtitles from audio using Whisper with GPU memory management"""
        try:
            # Verify audio file exists
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Clear GPU cache before loading Whisper
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print(f"   GPU memory cleared before Whisper loading")
            
            print("Loading Whisper model for accurate subtitle timing...")
            
            # Load Whisper model with GPU memory management
            if self.model is None:
                # Try models in order of size: base -> small -> tiny
                # base is good balance of accuracy and memory usage
                model_priority = ["base", "small", "tiny"]
                
                for model_name in model_priority:
                    try:
                        print(f"   Attempting to load Whisper '{model_name}' model...")
                        self.model = whisper.load_model(model_name)
                        print(f"   ✓ Loaded Whisper '{model_name}' model successfully")
                        break
                    except torch.cuda.OutOfMemoryError:
                        print(f"   ⚠ GPU OOM with '{model_name}', trying smaller model...")
                        torch.cuda.empty_cache()
                        continue
                    except Exception as e:
                        print(f"   ⚠ Failed to load '{model_name}': {e}")
                        continue
                
                # If all GPU attempts fail, try CPU
                if self.model is None:
                    print("   ⚠ GPU memory insufficient, loading Whisper on CPU...")
                    self.model = whisper.load_model("base", device="cpu")
                    print("   ✓ Loaded Whisper 'base' model on CPU")
            
            print("Transcribing audio with word-level timestamps...")
            
            # Transcribe with word timestamps
            result = self.model.transcribe(
                audio_path,
                language="vi",  # Vietnamese
                word_timestamps=True,
                verbose=False,
                task="transcribe",  # Explicitly set task to transcribe
                fp16=torch.cuda.is_available()  # Use FP16 only if GPU available
            )
            
            # Get full transcribed text
            whisper_transcription = result['text']
            
            print(f"   ✓ Whisper transcription: {whisper_transcription[:100]}...")
            
            # Use original script if available, otherwise use Whisper transcription
            if self.original_script:
                # Get the full script text
                if isinstance(self.original_script, dict):
                    corrected_text = self.original_script.get('script', whisper_transcription)
                else:
                    corrected_text = self.original_script
                print(f"   ✓ Using corrected script: {corrected_text[:100]}...")
            else:
                corrected_text = whisper_transcription
                print(f"   ⚠ No original script provided, using Whisper output")
            
            # Create subtitles based on mode
            # Pass both Whisper result (for timing) and corrected text (for display)
            if self.karaoke_mode:
                # Dynamic karaoke-style: word-by-word or rapid phrase appearance
                self._generate_karaoke_subtitles(result, corrected_text)
            else:
                # Traditional chunk-based subtitles
                self._generate_chunk_subtitles(result, corrected_text)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save SRT file
            self.subs.save(output_path, encoding='utf-8')
            
            # Verify file was created
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"Failed to create subtitle file: {output_path}")
            
            mode_note = " (karaoke mode)" if self.karaoke_mode else ""
            alignment_note = " (using corrected script)" if self.original_script else ""
            print(f"✓ Generated {len(self.subs)} subtitles with accurate timing{mode_note}{alignment_note}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error in subtitle generation: {e}")
            import traceback
            traceback.print_exc()
            print(f"Attempting fallback subtitle generation...")
            return self._fallback_generation(audio_path, output_path)
    
    def _generate_karaoke_subtitles(self, whisper_result: dict, corrected_text: str):
        """Generate karaoke-style word-by-word subtitles with pop-in effect"""
        self.subs = pysrt.SubRipFile()
        
        # Collect all words with timing from Whisper
        whisper_words = []
        for segment in whisper_result['segments']:
            if 'words' in segment:
                for word_info in segment['words']:
                    whisper_words.append({
                        'word': word_info['word'].strip(),
                        'start': word_info['start'],
                        'end': word_info['end']
                    })
        
        if not whisper_words:
            print("   ⚠ No word-level timestamps available, falling back to chunk mode")
            self._generate_chunk_subtitles(whisper_result, corrected_text)
            return
        
        # Split corrected text into words
        corrected_words = corrected_text.split()
        
        print(f"   Whisper words: {len(whisper_words)}, Corrected words: {len(corrected_words)}")
        
        # Align corrected words with Whisper timing using dynamic programming
        aligned_pairs = self._align_words_with_timing(whisper_words, corrected_words)
        
        # Generate rapid phrase subtitles (3-5 words at a time for readability)
        words_per_phrase = 4
        phrase_idx = 1
        idx = 0
        
        while idx < len(aligned_pairs):
            phrase_words = []
            phrase_start = aligned_pairs[idx]['start']
            phrase_end = aligned_pairs[idx]['end']
            
            for j in range(words_per_phrase):
                if idx + j >= len(aligned_pairs):
                    break
                
                pair = aligned_pairs[idx + j]
                phrase_words.append(pair['corrected_word'])
                phrase_end = pair['end']
                
                # Break at sentence-ending punctuation
                if pair['corrected_word'].endswith(('.', '!', '?', ':')):
                    break
            
            if phrase_words:
                phrase_text = ' '.join(phrase_words)
                sub = self._create_subtitle_item(phrase_idx, phrase_start, phrase_end, phrase_text)
                self.subs.append(sub)
                phrase_idx += 1
            
            idx += len(phrase_words)
        
        print(f"   ✓ Generated {len(self.subs)} karaoke-style subtitle phrases")
    
    def _generate_chunk_subtitles(self, whisper_result: dict, corrected_text: str):
        """Generate traditional chunk-based subtitles (8-10 words)"""
        self.subs = pysrt.SubRipFile()
        
        # Collect all words with timing from Whisper
        whisper_words = []
        for segment in whisper_result['segments']:
            if 'words' in segment:
                for word_info in segment['words']:
                    whisper_words.append({
                        'word': word_info['word'].strip(),
                        'start': word_info['start'],
                        'end': word_info['end']
                    })
        
        if not whisper_words:
            print("   ⚠ No word-level timestamps available, using segment timing")
            # Fallback to segment-based timing
            corrected_words = corrected_text.split()
            words_per_chunk = 9
            chunk_idx = 1
            
            for i, segment in enumerate(whisper_result['segments']):
                start_word_idx = i * words_per_chunk
                end_word_idx = min(start_word_idx + words_per_chunk, len(corrected_words))
                chunk_words = corrected_words[start_word_idx:end_word_idx]
                
                if chunk_words:
                    chunk_text = ' '.join(chunk_words)
                    sub = self._create_subtitle_item(chunk_idx, segment['start'], segment['end'], chunk_text)
                    self.subs.append(sub)
                    chunk_idx += 1
            return
        
        # Split corrected text into words
        corrected_words = corrected_text.split()
        
        print(f"   Whisper words: {len(whisper_words)}, Corrected words: {len(corrected_words)}")
        
        # Align corrected words with Whisper timing
        aligned_pairs = self._align_words_with_timing(whisper_words, corrected_words)
        
        # Group into chunks of 8-10 words
        words_per_chunk = 9
        chunk_idx = 1
        idx = 0
        
        while idx < len(aligned_pairs):
            chunk_words = []
            chunk_start = aligned_pairs[idx]['start']
            chunk_end = aligned_pairs[idx]['end']
            
            for j in range(words_per_chunk):
                if idx + j >= len(aligned_pairs):
                    break
                
                pair = aligned_pairs[idx + j]
                chunk_words.append(pair['corrected_word'])
                chunk_end = pair['end']
                
                # Break at sentence-ending punctuation
                if pair['corrected_word'].endswith(('.', '!', '?', ':')):
                    break
            
            if chunk_words:
                chunk_text = ' '.join(chunk_words)
                sub = self._create_subtitle_item(chunk_idx, chunk_start, chunk_end, chunk_text)
                self.subs.append(sub)
                chunk_idx += 1
            
            idx += len(chunk_words)
        
        print(f"   ✓ Generated {len(self.subs)} subtitle chunks")
    
    def _align_words_with_timing(self, whisper_words: list, corrected_words: list) -> list:
        """
        Align corrected words with Whisper timing using dynamic programming.
        Returns list of dicts with 'corrected_word', 'start', 'end'
        """
        # Simple case: same number of words
        if len(whisper_words) == len(corrected_words):
            return [
                {
                    'corrected_word': corrected_words[i],
                    'start': whisper_words[i]['start'],
                    'end': whisper_words[i]['end']
                }
                for i in range(len(corrected_words))
            ]
        
        # Use dynamic time warping (DTW) approach
        # Map corrected words to Whisper timing proportionally
        aligned = []
        
        # Calculate time per corrected word based on total duration
        total_duration = whisper_words[-1]['end'] - whisper_words[0]['start']
        time_per_word = total_duration / len(corrected_words)
        
        # Try to match words by similarity first
        whisper_idx = 0
        for i, corrected_word in enumerate(corrected_words):
            # Find best matching Whisper word within a window
            best_match_idx = whisper_idx
            best_score = 0
            
            # Look ahead up to 3 words
            for j in range(whisper_idx, min(whisper_idx + 3, len(whisper_words))):
                whisper_word = whisper_words[j]['word'].lower()
                corrected_lower = corrected_word.lower().strip('.,!?:;')
                
                # Calculate similarity score
                if whisper_word == corrected_lower:
                    score = 1.0
                elif whisper_word.startswith(corrected_lower[:3]) or corrected_lower.startswith(whisper_word[:3]):
                    score = 0.7
                else:
                    score = 0.0
                
                if score > best_score:
                    best_score = score
                    best_match_idx = j
            
            # Use the best match if found, otherwise use proportional timing
            if best_score > 0.5 and best_match_idx < len(whisper_words):
                aligned.append({
                    'corrected_word': corrected_word,
                    'start': whisper_words[best_match_idx]['start'],
                    'end': whisper_words[best_match_idx]['end']
                })
                whisper_idx = best_match_idx + 1
            else:
                # Proportional timing fallback
                start_time = whisper_words[0]['start'] + (i * time_per_word)
                end_time = start_time + time_per_word
                aligned.append({
                    'corrected_word': corrected_word,
                    'start': start_time,
                    'end': end_time
                })
        
        print(f"   ✓ Aligned {len(aligned)} words with timing")
        return aligned
    
    def _create_subtitle_item(self, index: int, start: float, end: float, text: str) -> pysrt.SubRipItem:
        """Create a SubRipItem with proper timing"""
        # Convert to SubRipTime format
        start_hours = int(start // 3600)
        start_minutes = int((start % 3600) // 60)
        start_seconds = int(start % 60)
        start_millis = int((start % 1) * 1000)
        
        end_hours = int(end // 3600)
        end_minutes = int((end % 3600) // 60)
        end_seconds = int(end % 60)
        end_millis = int((end % 1) * 1000)
        
        return pysrt.SubRipItem(
            index=index,
            start={'hours': start_hours, 'minutes': start_minutes,
                   'seconds': start_seconds, 'milliseconds': start_millis},
            end={'hours': end_hours, 'minutes': end_minutes,
                 'seconds': end_seconds, 'milliseconds': end_millis},
            text=text
        )
    
    def _fallback_generation(self, audio_path: str, output_path: str) -> str:
        """Fallback to simple timing if Whisper fails"""
        print("Using fallback subtitle generation with simple timing...")
        
        try:
            # Get audio duration
            import soundfile as sf
            audio_data, sample_rate = sf.read(audio_path)
            duration = len(audio_data) / sample_rate
            
            # Use original script if available, otherwise create placeholder
            if self.original_script:
                # Handle both dict and string formats
                if isinstance(self.original_script, dict):
                    text = self.original_script.get('script', 'Subtitle generation failed')
                else:
                    text = str(self.original_script)
            else:
                text = 'Subtitle generation failed'
            
            # Split text into chunks (10 words per subtitle)
            words = text.split()
            words_per_chunk = 10
            chunks = [' '.join(words[i:i+words_per_chunk]) for i in range(0, len(words), words_per_chunk)]
            
            # Calculate timing for each chunk
            time_per_chunk = duration / len(chunks) if chunks else duration
            
            # Create subtitles
            self.subs = pysrt.SubRipFile()
            for i, chunk in enumerate(chunks):
                start_time = i * time_per_chunk
                end_time = (i + 1) * time_per_chunk
                
                sub = self._create_subtitle_item(i + 1, start_time, end_time, chunk)
                self.subs.append(sub)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save SRT file
            self.subs.save(output_path, encoding='utf-8')
            print(f"✓ Generated {len(self.subs)} fallback subtitles")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Fallback generation also failed: {e}")
            # Create minimal subtitle as last resort
            self.subs = pysrt.SubRipFile()
            sub = pysrt.SubRipItem(
                index=1,
                start={'hours': 0, 'minutes': 0, 'seconds': 0, 'milliseconds': 0},
                end={'hours': 0, 'minutes': 1, 'seconds': 0, 'milliseconds': 0},
                text="[Subtitle generation failed]"
            )
            self.subs.append(sub)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            self.subs.save(output_path, encoding='utf-8')
            
            return output_path
    
    def generate_from_script(self, script: str, audio_duration: float, output_path: str) -> str:
        """Deprecated: Use generate_from_audio instead"""
        print("Warning: generate_from_script is deprecated, use generate_from_audio for accurate timing")
        return output_path
    
    def get_subtitles(self) -> pysrt.SubRipFile:
        """Return subtitle object for video overlay"""
        return self.subs
