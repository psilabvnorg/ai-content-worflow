"""Subtitle Aligner - Uses Qwen3:4b to align subtitles with original script"""
import requests
import json
import pysrt

class SubtitleAligner:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "qwen2.5:4b"
        
        # Verify model availability
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                # Find qwen model
                qwen_models = [name for name in model_names if 'qwen' in name.lower()]
                if qwen_models:
                    self.model = qwen_models[0]  # Use first qwen model found
                    print(f"   Using Ollama model: {self.model}")
                else:
                    print(f"   ⚠ No Qwen model found. Available: {model_names}")
                    print(f"   Install with: ollama pull qwen2.5:4b")
        except Exception as e:
            print(f"   ⚠ Cannot verify Ollama models: {e}")
    
    def align_subtitles(self, subtitle_path: str, original_script: str) -> str:
        """
        Align subtitles with original script using Qwen3:4b
        Keeps timeline, replaces text with aligned script
        """
        print(f"   Loading subtitles from: {subtitle_path}")
        subs = pysrt.open(subtitle_path, encoding='utf-8')
        
        # Extract subtitle text and timings
        subtitle_segments = []
        for sub in subs:
            subtitle_segments.append({
                'index': sub.index,
                'start': sub.start,
                'end': sub.end,
                'text': sub.text
            })
        
        # Combine all subtitle text
        whisper_text = ' '.join([seg['text'] for seg in subtitle_segments])
        
        print(f"   Original script length: {len(original_script)} chars")
        print(f"   Whisper transcript length: {len(whisper_text)} chars")
        print(f"   Number of subtitle segments: {len(subtitle_segments)}")
        
        # Use Qwen3:4b to align the texts
        print(f"   Calling Qwen3:4b to align texts...")
        aligned_segments = self._align_with_qwen(
            original_script=original_script,
            whisper_text=whisper_text,
            num_segments=len(subtitle_segments)
        )
        
        # Replace subtitle text with aligned text
        for i, sub in enumerate(subs):
            if i < len(aligned_segments):
                sub.text = aligned_segments[i]
        
        # Save aligned subtitles
        subs.save(subtitle_path, encoding='utf-8')
        print(f"   ✓ Subtitles aligned and saved")
        
        return subtitle_path
    
    def _align_with_qwen(self, original_script: str, whisper_text: str, num_segments: int) -> list:
        """Use Qwen3:4b to split original script into segments matching subtitle count"""
        
        prompt = f"""You are a subtitle alignment assistant. Your task is to split the original script into exactly {num_segments} segments that match the timing of the Whisper-generated subtitles.

Original Script (what should be displayed):
{original_script}

Whisper Transcript (for timing reference):
{whisper_text}

Instructions:
1. Split the original script into EXACTLY {num_segments} segments
2. Each segment should roughly correspond to the timing of the Whisper segments
3. Keep the original script text intact - do not change wording
4. Make natural breaks at sentence or phrase boundaries
5. Return ONLY a JSON array of strings, nothing else

Example output format:
["First segment text", "Second segment text", "Third segment text"]

Return the JSON array now:"""

        try:
            # Try chat endpoint first
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 2000
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('message', {}).get('content', '').strip()
                
                # Debug: show what we got
                if len(response_text) < 500:
                    print(f"   Debug - Qwen response: {response_text[:200]}")
                
                # Extract JSON array from response - be more robust
                # Try to find the JSON array
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    
                    try:
                        segments = json.loads(json_str)
                        
                        # Validate we got the right number of segments
                        if isinstance(segments, list) and len(segments) == num_segments:
                            print(f"   ✓ Qwen3:4b aligned {len(segments)} segments")
                            return segments
                        else:
                            print(f"   ⚠ Qwen3:4b returned {len(segments)} segments, expected {num_segments}")
                            return self._simple_split(original_script, num_segments)
                    except json.JSONDecodeError as e:
                        print(f"   ⚠ JSON parse error: {e}")
                        print(f"   Debug - JSON string: {json_str[:200]}...")
                        # Try to clean up the JSON
                        # Sometimes models add extra text after the array
                        lines = json_str.split('\n')
                        for i in range(len(lines), 0, -1):
                            try:
                                test_json = '\n'.join(lines[:i])
                                if test_json.endswith(']'):
                                    segments = json.loads(test_json)
                                    if isinstance(segments, list) and len(segments) == num_segments:
                                        print(f"   ✓ Qwen3:4b aligned {len(segments)} segments (after cleanup)")
                                        return segments
                            except:
                                continue
                        
                        print(f"   ⚠ Could not parse JSON after cleanup")
                        return self._simple_split(original_script, num_segments)
                else:
                    print(f"   ⚠ Could not find JSON array in response")
                    return self._simple_split(original_script, num_segments)
            else:
                print(f"   ⚠ Qwen3:4b API error: {response.status_code}")
                return self._simple_split(original_script, num_segments)
                
        except Exception as e:
            print(f"   ⚠ Error calling Qwen3:4b: {e}")
            return self._simple_split(original_script, num_segments)
    
    def _simple_split(self, text: str, num_segments: int) -> list:
        """Fallback: Simple split if Qwen3:4b fails"""
        print(f"   Using fallback: simple split")
        words = text.split()
        words_per_segment = max(1, len(words) // num_segments)
        
        segments = []
        for i in range(num_segments):
            start_idx = i * words_per_segment
            if i == num_segments - 1:
                # Last segment gets remaining words
                segment_words = words[start_idx:]
            else:
                segment_words = words[start_idx:start_idx + words_per_segment]
            
            segments.append(' '.join(segment_words))
        
        return segments
