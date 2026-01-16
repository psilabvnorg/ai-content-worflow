"""TTS Generator Module - Vietnamese (VieNeu-TTS) with high quality voice synthesis"""
import os
import wave
import subprocess

class TTSGenerator:
    def __init__(self, language: str = "vietnamese", voice: str = "binh"):
        self.language = language
        self.tts = None
        self.sample_rate = 24000  # VieNeu-TTS outputs 24kHz audio
        self.current_voice = None
        self.voice_name = voice if voice else "binh"  # Default to Binh (male Northern)
        
        # Available voices reference
        self.available_voices = {
            # Male Northern (default)
            "binh": "Bình (nam miền Bắc)",
            "tuyen": "Tuyên (nam miền Bắc)",
            # Male Southern
            "nguyen": "Nguyên (nam miền Nam)",
            "son": "Sơn (nam miền Nam)",
            "vinh": "Vĩnh (nam miền Nam)",
            # Female Northern
            "huong": "Hương (nữ miền Bắc)",
            "ly": "Ly (nữ miền Bắc)",
            "ngoc": "Ngọc (nữ miền Bắc)",
            # Female Southern
            "doan": "Đoan (nữ miền Nam)",
            "dung": "Dung (nữ miền Nam)",
        }
        
        print(f"   Voice setting: {self.voice_name} (male Northern)")
        
        if language == "vietnamese":
            self._init_vieneu_tts()
    
    def _init_vieneu_tts(self):
        """Initialize VieNeu-TTS for high-quality Vietnamese speech with GPU support"""
        try:
            print("[TTS] ========== VieNeu-TTS Initialization ==========", flush=True)
            
            from vieneu import Vieneu
            import torch
            
            print("[TTS] ✓ vieneu module imported", flush=True)
            
            # Check GPU availability
            has_cuda = torch.cuda.is_available()
            if has_cuda:
                gpu_name = torch.cuda.get_device_name(0)
                print(f"[TTS] ✓ GPU detected: {gpu_name}", flush=True)
                print(f"[TTS] ✓ CUDA version: {torch.version.cuda}", flush=True)
            else:
                print("[TTS] ⚠ No GPU, using CPU (slower)", flush=True)
            
            local_model_path = "models/VieNeu-TTS"
            
            print(f"[TTS] Model path: {local_model_path}", flush=True)
            print(f"[TTS] Model exists: {os.path.exists(local_model_path)}", flush=True)
            
            if has_cuda:
                device = "cuda"
                if os.path.exists(local_model_path):
                    print(f"[TTS] Loading local model from: {local_model_path}", flush=True)
                    self.tts = Vieneu(
                        backbone_repo=local_model_path,
                        backbone_device=device,
                        codec_device=device
                    )
                    print("[TTS] ✓ Local model loaded", flush=True)
                else:
                    print("[TTS] Loading HuggingFace model: pnnbao-ump/VieNeu-TTS-0.3B", flush=True)
                    self.tts = Vieneu(
                        backbone_repo="pnnbao-ump/VieNeu-TTS-0.3B",
                        backbone_device=device,
                        codec_device=device
                    )
                    print("[TTS] ✓ HuggingFace model loaded", flush=True)
            else:
                print("[TTS] Loading CPU model: pnnbao-ump/VieNeu-TTS-0.3B-q8-gguf", flush=True)
                self.tts = Vieneu(backbone_repo="pnnbao-ump/VieNeu-TTS-0.3B-q8-gguf")
                print("[TTS] ✓ CPU model loaded", flush=True)
            
            # List available preset voices
            print("[TTS] Listing available voices...", flush=True)
            voices_list = self.tts.list_preset_voices()
            print(f"[TTS] Raw voices list: {voices_list}", flush=True)
            
            # voices_list is a list of tuples: [(display_name, short_name), ...]
            # Extract just the short names for easier matching
            available_voices = [v[1] if isinstance(v, tuple) else v for v in voices_list]
            print(f"[TTS] Available voice keys: {available_voices}", flush=True)
            
            # Select voice
            if self.voice_name:
                voice_key = self.voice_name.lower()
                voice_map = {
                    "binh": "Binh", "bình": "Binh",
                    "tuyen": "Tuyen", "tuyên": "Tuyen",
                    "nguyen": "Nguyen", "nguyên": "Nguyen",
                    "son": "Son", "sơn": "Son",
                    "vinh": "Vinh", "vĩnh": "Vinh",
                    "huong": "Huong", "hương": "Huong",
                    "ly": "Ly",
                    "ngoc": "Ngoc", "ngọc": "Ngoc",
                    "doan": "Doan", "đoan": "Doan",
                    "dung": "Dung",
                }
                target_voice = voice_map.get(voice_key, self.voice_name.capitalize())
                
                if target_voice in available_voices:
                    self.current_voice = self.tts.get_preset_voice(target_voice)
                    print(f"[TTS] ✓ Selected voice: {target_voice}", flush=True)
                else:
                    print(f"[TTS] ⚠ Voice '{self.voice_name}' not found, using default", flush=True)
                    for v in ["Binh", "Tuyen"]:
                        if v in available_voices:
                            self.current_voice = self.tts.get_preset_voice(v)
                            print(f"[TTS] ✓ Selected voice: {v} (default male Northern)", flush=True)
                            break
            else:
                default_voices = ["Binh", "Tuyen"]
                for voice_name in default_voices:
                    if voice_name in available_voices:
                        self.current_voice = self.tts.get_preset_voice(voice_name)
                        print(f"[TTS] ✓ Selected voice: {voice_name} (default male Northern)", flush=True)
                        break
            
            if self.current_voice is None and available_voices:
                self.current_voice = self.tts.get_preset_voice(available_voices[0])
                print(f"[TTS] ✓ Selected voice: {available_voices[0]} (fallback)", flush=True)
            
            mode = "GPU" if has_cuda else "CPU"
            print(f"[TTS] ✓✓✓ VieNeu-TTS READY (24kHz, {mode} mode) ✓✓✓", flush=True)
            print("[TTS] ==============================================", flush=True)
            
        except ImportError as e:
            print(f"[TTS] ✗✗✗ IMPORT ERROR ✗✗✗", flush=True)
            print(f"[TTS] vieneu not installed: {e}", flush=True)
            print("[TTS] Install with: pip install vieneu", flush=True)
            print("[TTS] Also requires: espeak-ng (sudo apt install espeak-ng)", flush=True)
            self.tts = None
            
        except Exception as e:
            print(f"[TTS] ✗✗✗ INITIALIZATION ERROR ✗✗✗", flush=True)
            print(f"[TTS] Error type: {type(e).__name__}", flush=True)
            print(f"[TTS] Error message: {e}", flush=True)
            import traceback
            print("[TTS] Traceback:", flush=True)
            traceback.print_exc()
            self.tts = None
    
    def generate(self, text: str, output_path: str) -> str:
        """Generate speech audio file"""
        print(f"[TTS] Generating audio: {output_path}", flush=True)
        print(f"[TTS] VieNeu-TTS available: {self.tts is not None}", flush=True)
        
        if self.language == "vietnamese" and self.tts is not None:
            print("[TTS] Using VieNeu-TTS (preferred)", flush=True)
            return self._generate_vieneu_tts(text, output_path)
        else:
            print("[TTS] VieNeu-TTS not available, BLOCKING edge-tts fallback", flush=True)
            raise RuntimeError("[TTS] VieNeu-TTS not initialized - cannot generate audio. Fix VieNeu-TTS initialization.")
            return asyncio.run(self._generate_edge_tts(text, output_path))
    
    def _generate_vieneu_tts(self, text: str, output_path: str) -> str:
        """Generate Vietnamese speech using VieNeu-TTS"""
        try:
            import soundfile as sf
            
            print("Generating audio with VieNeu-TTS (high quality)...")
            
            # Clean text - remove SSML-like markers
            clean_text = text.replace("... ", ". ").replace(" ... ", ". ")
            
            # Generate audio with quality settings
            # Lower temperature = more stable/consistent output
            # Higher temperature = more expressive but less stable
            audio = self.tts.infer(
                text=clean_text,
                voice=self.current_voice,
                temperature=0.8,  # Balanced for news reading
                top_k=50
            )
            
            # Save audio
            if output_path.endswith('.mp3'):
                # Save as temp WAV then convert to MP3
                temp_wav = output_path.replace('.mp3', '_temp.wav')
                sf.write(temp_wav, audio, self.sample_rate)
                
                try:
                    subprocess.run(
                        ['ffmpeg', '-i', temp_wav, '-codec:a', 'libmp3lame',
                         '-qscale:a', '2', '-y', output_path],
                        capture_output=True,
                        check=True
                    )
                    os.remove(temp_wav)
                except subprocess.CalledProcessError as e:
                    print(f"Warning: Failed to convert to MP3: {e}")
                    os.rename(temp_wav, output_path)
            else:
                sf.write(output_path, audio, self.sample_rate)
            
            print(f"✓ Generated audio: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error generating with VieNeu-TTS: {e}")
            import traceback
            traceback.print_exc()
            print("Falling back to edge-tts...")
            import asyncio
            return asyncio.run(self._generate_edge_tts(text, output_path))
    
    def set_voice(self, voice_name: str):
        """Change the voice preset"""
        if self.tts is None:
            print("⚠ VieNeu-TTS not initialized")
            return
        
        try:
            available_voices = self.tts.list_preset_voices()
            if voice_name in available_voices:
                self.current_voice = self.tts.get_preset_voice(voice_name)
                print(f"✓ Voice changed to: {voice_name}")
            else:
                print(f"⚠ Voice '{voice_name}' not found. Available: {available_voices}")
        except Exception as e:
            print(f"⚠ Error changing voice: {e}")
    
    def clone_voice(self, audio_path: str, transcript: str, voice_name: str = "CustomVoice"):
        """Clone a voice from reference audio"""
        if self.tts is None:
            print("⚠ VieNeu-TTS not initialized")
            return None
        
        try:
            print(f"Cloning voice from: {audio_path}")
            custom_voice = self.tts.clone_voice(
                audio_path=audio_path,
                text=transcript,
                name=voice_name
            )
            self.current_voice = custom_voice
            print(f"✓ Voice cloned and set as: {voice_name}")
            return custom_voice
        except Exception as e:
            print(f"⚠ Error cloning voice: {e}")
            return None
    
    async def _generate_edge_tts(self, text: str, output_path: str) -> str:
        """Generate speech using Microsoft Edge TTS (fallback)"""
        import edge_tts
        
        if self.language == "vietnamese":
            # Use male voice for fallback (NamMinh - Southern male)
            # Note: Edge TTS doesn't have Northern male, NamMinh is the only male option
            voice = "vi-VN-NamMinhNeural"
            print("Using edge-tts fallback (NamMinh - Vietnamese male)")
        else:
            voice = "en-US-GuyNeural"
        
        # Handle SSML breaks
        text_with_breaks = text.replace("... ", '<break time="700ms"/> ')
        text_with_breaks = text_with_breaks.replace(" ... ", ' <break time="700ms"/> ')
        
        if '<break' in text_with_breaks:
            print("   Using SSML breaks for natural pacing")
            communicate = edge_tts.Communicate(text_with_breaks, voice)
        else:
            communicate = edge_tts.Communicate(text, voice)
        
        await communicate.save(output_path)
        print(f"Generated audio: {output_path}")
        return output_path
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds"""
        try:
            import soundfile as sf
            data, samplerate = sf.read(audio_path)
            return len(data) / samplerate
        except:
            try:
                with wave.open(audio_path, 'rb') as audio:
                    frames = audio.getnframes()
                    rate = audio.getframerate()
                    return frames / float(rate)
            except:
                # Fallback for MP3 files
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries',
                     'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                     audio_path],
                    capture_output=True, text=True
                )
                return float(result.stdout.strip())
    
    def close(self):
        """Clean up resources"""
        if self.tts is not None:
            try:
                self.tts.close()
            except:
                pass
