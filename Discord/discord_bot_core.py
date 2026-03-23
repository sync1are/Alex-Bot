#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​‌​​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​​​‌​​‌​​​​‌‌‌​‌​‌​‌‌​​​‌​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
# discord_bot_core.py
from commands import spotify
from commands.app_opening import AppOpening
from commands.web_lookup import web_lookup
from core.intent import resolve_intent
from core.llm import query_llm


def get_ai_response(user_input: str) -> str:
    """
    Process user input and return AI response
    Used by Discord bot
    """
    app_handler = AppOpening()
    
    try:
        intent = resolve_intent(user_input)
        
        if intent == "spotify":
            spotify.handle_spotify_command(user_input)
            return "✅ Spotify command processed!"
        
        elif intent == "app_opening":
            response = app_handler.handle_command(user_input)
            return f"🚀 {response}"
        
        elif intent == "web_search":
            answer = web_lookup.handle_command(user_input)
            return f"🔍 Web Search Results:\n{answer}"
        
        elif intent == "question":
            response = web_lookup.handle_command(user_input)
            return f"💡 {response}"
        
        else:
            # Chat fallback
            response = query_llm(user_input)
            return f"Synclare: {response}"
    
    except Exception as e:
        return f"⚠️ Error: {str(e)}"
