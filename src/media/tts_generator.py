"""TTS Generator Module - Vietnamese (NGHI-TTS) and English (edge-tts)"""
import os
import asyncio
import edge_tts
import onnxruntime as ort
import numpy as np
import wave
import json

class TTSGenerator:
    def __init__(self, language: str = "vietnamese", model_path: str = None):
        self.language = language
        self.model_path = model_path
        
        if language == "vietnamese" and model_path:
            # Load NGHI-TTS ONNX model
            self.session = ort.InferenceSession(model_path)
            config_path = model_path.replace('.onnx', '.onnx.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"Loaded Vietnamese TTS model: {model_path}")
        else:
            self.session = None
            print("Using edge-tts for TTS generation")
    
    async def generate_async(self, text: str, output_path: str) -> str:
        """Generate speech audio file"""
        if self.language == "vietnamese" and self.session:
            return self._generate_vietnamese_onnx(text, output_path)
        else:
            return await self._generate_edge_tts(text, output_path)
    
    def generate(self, text: str, output_path: str) -> str:
        """Synchronous wrapper for generate_async"""
        return asyncio.run(self.generate_async(text, output_path))
    
    def _generate_vietnamese_onnx(self, text: str, output_path: str) -> str:
        """Generate Vietnamese speech using NGHI-TTS ONNX model"""
        # Note: This is a simplified implementation
        # Full implementation requires phonemization and proper text processing
        # For production, integrate with piper-phonemize or use the full nghitts pipeline
        
        print("Warning: ONNX TTS requires phonemization. Using edge-tts fallback.")
        return asyncio.run(self._generate_edge_tts(text, output_path))
    
    async def _generate_edge_tts(self, text: str, output_path: str) -> str:
        """Generate speech using Microsoft Edge TTS"""
        # Vietnamese male voices: vi-VN-NamMinhNeural (male)
        # English male voices: en-US-GuyNeural (male)
        
        if self.language == "vietnamese":
            voice = "vi-VN-NamMinhNeural"
        else:
            voice = "en-US-GuyNeural"
        
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
