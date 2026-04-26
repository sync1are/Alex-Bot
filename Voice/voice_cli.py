#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​‌​​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​​​‌​​‌​​​​‌‌‌​‌​‌​‌‌​​​‌​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
# voice_cli.py - FIXED (PRESERVES EMPHASIZED WORDS)
import asyncio
import edge_tts
import os
import pygame
import re
import tempfile

class VoiceCLI:
    def __init__(self):
        pygame.mixer.init()
        self.voice = 'en-US-DavisNeural'
        print("✅ Voice ready: Davis")
    
    def clean_text_for_speech(self, text: str) -> str:
        """Clean text - keep emphasized words, remove actions"""
        
        # FIRST: Keep single emphasized words by removing just the asterisks
        # Match *word* (single word emphasis) and keep the word
        text = re.sub(r'\*(\w+)\*', r'\1', text)
        
        # THEN: Remove multi-word actions (like *rolls eyes*, *sigh*)
        # These have spaces or multiple words
        text = re.sub(r'\*[^*]+\*', '', text)
        
        # Remove emojis
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+",
 flags = re.UNICODE
        )
        text = emoji_pattern.sub('', text)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def speak(self, text: str):
        """Speak with natural voice"""
        clean_text = self.clean_text_for_speech(text)
        if clean_text.strip():
            asyncio.run(self._speak_async(clean_text))
    
    async def _speak_async(self, text: str):
        """Internal async speech"""
 with tempfile.NamedTemporaryFile(suffix = '.mp3', delete = False) as fp:
            temp_path = fp.name
        
        try:
 communicate = edge_tts.Communicate(text, self.voice, rate = "+12%")
            await communicate.save(temp_path)
            
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            pygame.mixer.music.unload()
            
        except Exception as e:
            print(f"[Voice error: {e}]")
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

voice = VoiceCLI()
