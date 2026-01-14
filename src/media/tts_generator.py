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
            from vieneu import Vieneu
            import torch
            
            print("Loading VieNeu-TTS model...")
            
            # Check GPU availability
            has_cuda = torch.cuda.is_available()
            if has_cuda:
                gpu_name = torch.cuda.get_device_name(0)
                print(f"   GPU detected: {gpu_name}")
                print(f"   CUDA version: {torch.version.cuda}")
            else:
                print("   ⚠ No GPU detected, using CPU (slower)")
            
            # Model selection:
            # For GPU: Use PyTorch models (not GGUF) for proper GPU acceleration
            # - "pnnbao-ump/VieNeu-TTS" (0.5B, best quality)
            # - "pnnbao-ump/VieNeu-TTS-0.3B" (0.3B, faster, good quality)
            # For CPU: GGUF models are optimized
            # - "pnnbao-ump/VieNeu-TTS-0.3B-q8-gguf"
            # - "pnnbao-ump/VieNeu-TTS-0.3B-q4-gguf"
            
            local_model_path = "models/VieNeu-TTS"
            
            if has_cuda:
                # GPU mode: Use PyTorch model with CUDA device
                device = "cuda"
                if os.path.exists(local_model_path):
                    print(f"   Using local PyTorch model: {local_model_path}")
                    self.tts = Vieneu(
                        backbone_repo=local_model_path,
                        backbone_device=device,
                        codec_device=device
                    )
                else:
                    # Use 0.3B for faster GPU inference, still great quality
                    print("   Using HuggingFace model: pnnbao-ump/VieNeu-TTS-0.3B (GPU)")
                    self.tts = Vieneu(
                        backbone_repo="pnnbao-ump/VieNeu-TTS-0.3B",
                        backbone_device=device,
                        codec_device=device
                    )
                print(f"   ✓ Running on GPU: {gpu_name}")
            else:
                # CPU mode: Use quantized GGUF for better CPU performance
                print("   Using quantized model for CPU: pnnbao-ump/VieNeu-TTS-0.3B-q8-gguf")
                self.tts = Vieneu(backbone_repo="pnnbao-ump/VieNeu-TTS-0.3B-q8-gguf")
                print("   Running on CPU")
            
            # List available preset voices
            available_voices = self.tts.list_preset_voices()
            print(f"   Available voices: {available_voices}")
            
            # Select voice based on argument or default to male Northern
            if self.voice_name:
                # User specified a voice
                voice_key = self.voice_name.lower()
                # Map common names to actual voice names
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
                    print(f"   Selected voice: {target_voice}")
                else:
                    print(f"   ⚠ Voice '{self.voice_name}' not found, using default")
                    # Fall back to default male Northern
                    for v in ["Binh", "Tuyen"]:
                        if v in available_voices:
                            self.current_voice = self.tts.get_preset_voice(v)
                            print(f"   Selected voice: {v} (default male Northern)")
                            break
            else:
                # Default: male Northern accent (Binh or Tuyen)
                default_voices = ["Binh", "Tuyen"]
                for voice_name in default_voices:
                    if voice_name in available_voices:
                        self.current_voice = self.tts.get_preset_voice(voice_name)
                        print(f"   Selected voice: {voice_name} (default male Northern)")
                        break
            
            if self.current_voice is None and available_voices:
                self.current_voice = self.tts.get_preset_voice(available_voices[0])
                print(f"   Selected voice: {available_voices[0]} (fallback)")
            
            print(f"✓ VieNeu-TTS loaded (24kHz, {'GPU' if has_cuda else 'CPU'} mode)")
            
        except ImportError:
            print("⚠ vieneu not installed. Install with: pip install vieneu")
            print("  Also requires: espeak-ng (sudo apt install espeak-ng)")
            print("  Falling back to edge-tts...")
            self.tts = None
        except Exception as e:
            print(f"⚠ Failed to load VieNeu-TTS: {e}")
            print("  Falling back to edge-tts...")
            self.tts = None
    
    def generate(self, text: str, output_path: str) -> str:
        """Generate speech audio file"""
        if self.language == "vietnamese" and self.tts is not None:
            return self._generate_vieneu_tts(text, output_path)
        else:
            import asyncio
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
