#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​‌​​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​​​‌​​‌​​​​‌‌‌​‌​‌​‌‌​​​‌​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
# discord_bot.py
from discord.ext import commands
from discord_bot_core import get_ai_response
from Voice.voice_handler import voice_handler
import discord

TOKEN = "MTQzMDkxMTE3MzAyMDA5NDYwNA.GWfjs1.hJWlhwkl2TgvsqKPPCe7AQM4SA1LO2dlKIwoXE"

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")


@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")
    print(f"📊 Connected to {len(bot.guilds)} server(s)")
    print("🤖 Synclare Discord Bot is ready!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.content.startswith("!"):
        command_name = message.content[1:].split()[0].lower() if len(message.content) > 1 else ""
        
        # List of actual commands (removed 'listen')
        command_list = ["help", 'ping', 'join', 'leave', 'speak', 'ask']
        if command_name in command_list:
            await bot.process_commands(message)
            return
        
        # Everything else goes to AI
        user_input = message.content[1:].strip()
        if not user_input:
            return
        
        status_msg = await message.channel.send("🔍 Processing...")
        
        try:
            # Get AI response
            response = get_ai_response(user_input)
            await status_msg.delete()
            
            # Send text response
            if len(response) > 2000:
                for i in range(0, len(response), 2000):
                    await message.channel.send(response[i:i+2000])
            else:
                await message.channel.send(response)
            
            # If bot is in voice channel, also speak the response
            if message.guild.voice_client is not None:
                # Truncate for voice
                words = response.split()
                response_voice = ' '.join(words[:200]) if len(words) > 200 else response
                
                await message.channel.send("🗣️ *Speaking response in voice...*")
                await voice_handler.speak(message, response_voice)
        
        except Exception as e:
            await status_msg.edit(content=f"⚠️ Error: {str(e)}")


@bot.command(name="help")
async def help_command(ctx):
    help_text = """
**🧠 Synclare AI Discord Bot**

**Text Commands:**
• `!<message>` - Chat with AI
• `!search for <query>` - Web search
• `!help` - Show this message
• `!ping` - Check bot latency

**Voice Commands:**
• `!join` - Join your voice channel
• `!leave` - Leave voice channel
• `!speak <text>` - Speak text in voice
• `!ask <question>` - Ask AI and hear response

💡 **Tip:** When bot is in voice, any text command gets spoken automatically!
    """
    await ctx.send(help_text)


@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! {latency}ms")


@bot.command(name="join")
async def join_voice(ctx):
    """Bot joins your voice channel"""
    await voice_handler.join_channel(ctx)


@bot.command(name="leave")
async def leave_voice(ctx):
    """Bot leaves voice channel"""
    await voice_handler.leave_channel(ctx)


@bot.command(name="speak")
async def speak(ctx, *, message: str):
    """Bot speaks your message"""
    await ctx.send(f"🗣️ Speaking: *{message[:100]}...*")
    await voice_handler.speak(ctx, message)


@bot.command(name="ask")
async def ask_voice(ctx, *, question: str):
    """Ask AI and get voice response"""
    if ctx.voice_client is None:
        await ctx.send("❌ I'm not in a voice channel! Use `!join` first.")
        return
    
    status_msg = await ctx.send("🤔 Thinking...")
    
    try:
        # Get AI response
        response = get_ai_response(question)
        
        # Truncate for voice
        words = response.split()
        response_voice = ' '.join(words[:200]) if len(words) > 200 else response
        
        # Show in chat
        truncated_chat = response[:500] + "..." if len(response) > 500 else response
        await status_msg.edit(content=f"💬 **Q:** {question[:100]}...\n\n**A:** {truncated_chat}")
        
        # Speak response
        await voice_handler.speak(ctx, response_voice)
    
    except Exception as e:
        await status_msg.edit(content=f"⚠️ Error: {str(e)}")


if __name__ == "__main__":
    bot.run(TOKEN)
