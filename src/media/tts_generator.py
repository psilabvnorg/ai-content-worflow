"""TTS Generator Module - Vietnamese (NGHI-TTS) and English (edge-tts)"""
import os
import asyncio
import edge_tts
import onnxruntime as ort
import numpy as np
import wave
import json
import subprocess

class TTSGenerator:
    def __init__(self, language: str = "vietnamese", model_path: str = None):
        self.language = language
        self.model_path = model_path
        
        print(f"[DEBUG] TTSGenerator init: language={language}, model_path={model_path}")
        
        if language == "vietnamese" and model_path and os.path.exists(model_path):
            # Load NGHI-TTS ONNX model
            try:
                print(f"Loading NGHI-TTS model: {model_path}")
                self.session = ort.InferenceSession(model_path)
                config_path = model_path.replace('.onnx', '.onnx.json')
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"✓ Loaded Vietnamese TTS model: {os.path.basename(model_path)}")
                print(f"   Sample rate: {self.config['audio']['sample_rate']} Hz")
            except Exception as e:
                print(f"Warning: Failed to load ONNX model: {e}")
                print("Falling back to edge-tts")
                self.session = None
        else:
            self.session = None
            if language == "vietnamese":
                print(f"[DEBUG] Not loading NGHI-TTS: model_path={model_path}, exists={os.path.exists(model_path) if model_path else False}")
                print("Using edge-tts for TTS generation (Northern accent)")
    
    async def generate_async(self, text: str, output_path: str) -> str:
        """Generate speech audio file"""
        print(f"[DEBUG] generate_async: session={self.session is not None}, language={self.language}")
        if self.language == "vietnamese" and self.session:
            return self._generate_vietnamese_onnx(text, output_path)
        else:
            return await self._generate_edge_tts(text, output_path)
    
    def generate(self, text: str, output_path: str) -> str:
        """Synchronous wrapper for generate_async"""
        return asyncio.run(self.generate_async(text, output_path))
    
    def _phonemize_text(self, text: str) -> str:
        """Convert Vietnamese text to phonemes using espeak"""
        try:
            # Use espeak-ng for phonemization
            result = subprocess.run(
                ['espeak-ng', '-v', 'vi', '-q', '--ipa', text],
                capture_output=True,
                text=True,
                check=True
            )
            phonemes = result.stdout.strip()
            return phonemes
        except subprocess.CalledProcessError as e:
            print(f"Warning: espeak-ng failed: {e}")
            return text
        except FileNotFoundError:
            print("Warning: espeak-ng not found. Install with: sudo apt-get install espeak-ng")
            return text
    
    def _generate_vietnamese_onnx(self, text: str, output_path: str) -> str:
        """Generate Vietnamese speech using NGHI-TTS ONNX model"""
        try:
            print("Generating audio with NGHI-TTS...")
            
            # Phonemize text
            phonemes = self._phonemize_text(text)
            print(f"   Phonemized: {phonemes[:100]}...")
            
            # Convert phonemes to IDs
            phoneme_ids = self._phonemes_to_ids(phonemes)
            
            # Prepare input for ONNX model
            input_ids = np.array([phoneme_ids], dtype=np.int64)
            input_lengths = np.array([len(phoneme_ids)], dtype=np.int64)
            scales = np.array([
                self.config['inference']['noise_scale'],
                self.config['inference']['length_scale'],
                self.config['inference']['noise_w']
            ], dtype=np.float32)
            
            # Run inference
            outputs = self.session.run(
                None,
                {
                    'input': input_ids,
                    'input_lengths': input_lengths,
                    'scales': scales
                }
            )
            
            audio = outputs[0].squeeze()
            
            # Save as WAV file
            sample_rate = self.config['audio']['sample_rate']
            self._save_wav(audio, output_path, sample_rate)
            
            print(f"✓ Generated audio: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error generating with ONNX: {e}")
            import traceback
            traceback.print_exc()
            print("Falling back to edge-tts...")
            return asyncio.run(self._generate_edge_tts(text, output_path))
    
    def _phonemes_to_ids(self, phonemes: str) -> list:
        """Convert phoneme string to IDs using phoneme_id_map"""
        phoneme_map = self.config.get('phoneme_id_map', {})
        ids = []
        
        # Add start token
        if '^' in phoneme_map:
            ids.extend(phoneme_map['^'])
        
        # Convert each character
        for char in phonemes:
            if char in phoneme_map:
                ids.extend(phoneme_map[char])
            elif ' ' in phoneme_map:
                ids.extend(phoneme_map[' '])
        
        # Add end token
        if '$' in phoneme_map:
            ids.extend(phoneme_map['$'])
        
        return ids
    
    def _save_wav(self, audio: np.ndarray, output_path: str, sample_rate: int):
        """Save audio array as WAV file, convert to MP3 if needed"""
        # Normalize audio to int16 range
        audio = np.clip(audio, -1.0, 1.0)
        audio = (audio * 32767).astype(np.int16)
        
        # Check if output should be MP3
        if output_path.endswith('.mp3'):
            # Save as temporary WAV first
            temp_wav = output_path.replace('.mp3', '_temp.wav')
            with wave.open(temp_wav, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio.tobytes())
            
            # Convert WAV to MP3 using ffmpeg
            try:
                subprocess.run(
                    ['ffmpeg', '-i', temp_wav, '-codec:a', 'libmp3lame', '-qscale:a', '2', '-y', output_path],
                    capture_output=True,
                    check=True
                )
                # Remove temporary WAV
                os.remove(temp_wav)
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to convert to MP3: {e}")
                # Rename WAV to MP3 as fallback
                os.rename(temp_wav, output_path)
        else:
            # Save as WAV
            with wave.open(output_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio.tobytes())
    
    async def _generate_edge_tts(self, text: str, output_path: str) -> str:
        """Generate speech using Microsoft Edge TTS with SSML breaks"""
        # Vietnamese voices:
        # - vi-VN-NamMinhNeural (male, Southern accent)
        # - vi-VN-HoaiMyNeural (female, Northern accent)
        # English male voices: en-US-GuyNeural (male)
        
        if self.language == "vietnamese":
            # Use HoaiMy for Northern accent (female voice)
            # Note: Edge TTS doesn't have a male Northern voice
            # HoaiMy is the closest to Northern accent
            voice = "vi-VN-HoaiMyNeural"
            print("Using Northern Vietnamese accent (HoaiMy - female)")
        else:
            voice = "en-US-GuyNeural"
        
        # Convert break markers to SSML breaks
        # Replace "... " with proper pause (700ms for intro)
        # Replace " ..." with proper pause (700ms for outro)
        text_with_breaks = text.replace("... ", '<break time="700ms"/> ')
        text_with_breaks = text_with_breaks.replace(" ... ", ' <break time="700ms"/> ')
        
        # If text contains SSML breaks, wrap in SSML
        if '<break' in text_with_breaks:
            print("   Using SSML breaks for natural pacing (700ms pauses)")
            # Edge TTS will handle SSML automatically
            communicate = edge_tts.Communicate(text_with_breaks, voice)
        else:
            communicate = edge_tts.Communicate(text, voice)
        
        await communicate.save(output_path)
        
        print(f"Generated audio: {output_path}")
        return output_path
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds"""
        try:
            with wave.open(audio_path, 'rb') as audio:
                frames = audio.getnframes()
                rate = audio.getframerate()
                duration = frames / float(rate)
                return duration
        except:
            # Fallback for non-WAV files
            import subprocess
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 
                 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                 audio_path],
                capture_output=True, text=True
            )
            return float(result.stdout.strip())
