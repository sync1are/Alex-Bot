#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​‌​​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​​​‌​​‌​​​​‌‌‌​‌​‌​‌‌​​​‌​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
# Voice/voice_handler.py (WORKING VERSION - NO SINKS)
from gtts import gTTS
import asyncio
import discord
import os
import tempfile

class VoiceHandler:
    def __init__(self):
        self.voice_clients = {}
    
    async def join_channel(self, ctx):
        """Bot joins the voice channel"""
        if ctx.author.voice is None:
            await ctx.send("❌ You're not in a voice channel!")
            return None
        
        channel = ctx.author.voice.channel
        
        if ctx.voice_client is not None:
            if ctx.voice_client.channel.id == channel.id:
                await ctx.send("✅ Already in your voice channel!")
                return ctx.voice_client
            else:
                await ctx.voice_client.move_to(channel)
                await ctx.send(f"✅ Moved to {channel.name}!")
                return ctx.voice_client
        
        voice_client = await channel.connect()
        self.voice_clients[ctx.guild.id] = voice_client
        await ctx.send(f"✅ Joined {channel.name}!")
        return voice_client
    
    async def leave_channel(self, ctx):
        """Bot leaves the voice channel"""
        voice_client = ctx.voice_client
        if voice_client is None:
            await ctx.send("❌ I'm not in a voice channel!")
            return
        
        await voice_client.disconnect()
        if ctx.guild.id in self.voice_clients:
            del self.voice_clients[ctx.guild.id]
        
        await ctx.send("👋 Left voice channel!")
    
    async def speak(self, ctx, text: str):
        """Convert text to speech and play it"""
        # Handle both ctx and message objects
        if hasattr(ctx, "voice_client"):
            voice_client = ctx.voice_client
        elif hasattr(ctx, 'guild'):
            voice_client = ctx.guild.voice_client
        else:
            return
        
        if voice_client is None:
            return
        
        if voice_client.is_playing():
            voice_client.stop()
            await asyncio.sleep(0.05)
        
        try:
            # Create temp file
 with tempfile.NamedTemporaryFile(suffix = ".mp3", delete = False) as temp_file:
                temp_path = temp_file.name
            
            # Generate TTS
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_path)
            
            # Play audio
            audio_source = discord.FFmpegPCMAudio(temp_path)
            
            def cleanup(error):
                if error:
                    print(f"Playback error: {error}")
                try:
                    os.unlink(temp_path)
                except:
                    pass
            
 voice_client.play(audio_source, after = cleanup)
            
            # Wait for playback to finish
            while voice_client.is_playing():
                await asyncio.sleep(0.1)
        
        except Exception as e:
            print(f"❌ TTS Error: {e}")

# Global instance
voice_handler = VoiceHandler()
