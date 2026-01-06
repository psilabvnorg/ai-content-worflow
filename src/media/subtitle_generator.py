"""Subtitle Generator Module - Creates synchronized subtitles"""
import pysrt

class SubtitleGenerator:
    def __init__(self):
        self.subs = pysrt.SubRipFile()
    
    def generate_from_script(self, script: str, audio_duration: float, output_path: str) -> str:
        """Generate SRT subtitles from script text"""
        words = script.split()
        total_words = len(words)
        
        # Calculate timing per word
        time_per_word = audio_duration / total_words
        
        # Create subtitle chunks (5-7 words per subtitle)
        words_per_sub = 6
        current_time = 0
        
        for i in range(0, total_words, words_per_sub):
            chunk = ' '.join(words[i:i + words_per_sub])
            start_time = current_time
            end_time = current_time + (time_per_word * min(words_per_sub, total_words - i))
            
            # Convert seconds to SubRipTime format (hours, minutes, seconds, milliseconds)
            start_hours = int(start_time // 3600)
            start_minutes = int((start_time % 3600) // 60)
            start_seconds = int(start_time % 60)
            start_millis = int((start_time % 1) * 1000)
            
            end_hours = int(end_time // 3600)
            end_minutes = int((end_time % 3600) // 60)
            end_seconds = int(end_time % 60)
            end_millis = int((end_time % 1) * 1000)
            
            sub = pysrt.SubRipItem(
                index=len(self.subs) + 1,
                start={'hours': start_hours, 'minutes': start_minutes, 
                       'seconds': start_seconds, 'milliseconds': start_millis},
                end={'hours': end_hours, 'minutes': end_minutes, 
                     'seconds': end_seconds, 'milliseconds': end_millis},
                text=chunk
            )
            self.subs.append(sub)
            current_time = end_time
        
        # Save SRT file
        self.subs.save(output_path, encoding='utf-8')
        print(f"Generated subtitles: {output_path}")
        return output_path
    
    def get_subtitles(self) -> pysrt.SubRipFile:
        """Return subtitle object for video overlay"""
        return self.subs
