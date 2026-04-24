#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
# main.py
from commands import spotify
from commands.app_opening import AppOpening
from core.intent import resolve_intent
from core.llm import query_llm, clear_history  # 🆕 Import clear_history
# from commands.search_web import WebSearch
from commands.web_lookup import web_lookup
from Discord.discord_bot_core import get_ai_response

from Voice.voice_cli import voice

def main():
    # Initialize command handlers
    app_handler = AppOpening()
    # web_handler = WebSearch()
    print("🧠 Synclare AI – Phase 2 Prototype (Memory Context and Conversation History)")
    print("Type commands like:")
    print("or chat normally with the AI.\n")
    print("\n🔊 Voice: Andrew (Deep Male)\n")
    
    while True:
        user_input = input("You: ").strip()
        
        # 🆕 MODIFIED: Clear conversation history
        if user_input.lower() == "clear":
            clear_history()  # Now calls the proper function from llm.py
            print("🔄 Conversation cleared!")
            continue
            
        if not user_input:
            continue
            
        if user_input.lower() in ["exit", "quit"]:
            break

        # Decide what kind of input this is
        intent = resolve_intent(user_input)
        
        if intent == "spotify":
            # Send command to the Spotify control module
            try:
                spotify.handle_spotify_command(user_input)
            except Exception as e:
                print(f"⚠️ Spotify command error: {e}")

        elif intent == "app_opening":
            # Handle app opening commands
            try:
                response = app_handler.handle_command(user_input)
                print(f"🚀 {response}")
            except Exception as e:
                print(f"⚠️ App opening error: {e}")
                
        elif intent == "web_search":
            # Handle web search commands
            try:
                answer = web_lookup.handle_command(user_input)
                print(f"🔍 Web Search Results:\n{answer}")
            except Exception as e:
                print(f"⚠️ Web search error: {e}")

        elif intent == "question":
            # Handle question commands
            try:
                response = web_lookup.handle_command(user_input)
                print(f"💡 {response}")
            except Exception as e:
                print(f"⚠️ Question error: {e}")

        else:
            # Chat fallback → query local LLM (Gemma or Phi-2 via Ollama)
            try:
 response = query_llm(user_input, preset = "sarcastic", temperature = 0.7, max_tokens = 512)
                print(f"Synclare: {response}\n")
                voice.speak(response)
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                print(error_msg)
                voice.speak("Sorry, I encountered an error.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                voice.speak("Goodbye!")
                break
            
if __name__ == "__main__":
    main()
