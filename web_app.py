# =========================================================
# Synclare AI Web + Console Unified Interface
# =========================================================

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import sys, os

# Local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.intent import resolve_intent
from core.llm import query_llm, clear_history
from commands import spotify
from commands.app_opening import AppOpening
# from commands.search_web import WebSearch
from commands.web_lookup import web_lookup
from Discord.discord_bot_core import get_ai_response
from Voice.voice_cli import voice


# =========================================================
# Flask App Setup
# =========================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'synclare-secret-key-change-this-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

app_handler = AppOpening()


# =========================================================
# Web Routes
# =========================================================
@app.route('/')
def index():
    """Serve main chat interface"""
    return render_template('chat.html')


# =========================================================
# SocketIO Events
# =========================================================
@socketio.on('connect')
def handle_connect():
    print('✅ Client connected')
    emit('status', {'message': 'Connected to Synclare AI'})


@socketio.on('disconnect')
def handle_disconnect():
    print('❌ Client disconnected')


@socketio.on('user_message')
def handle_message(data):
    """Handle incoming messages from the web interface"""
    try:
        user_input = data.get('message', '').strip()
        if not user_input:
            emit('error', {'message': 'Message cannot be empty'})
            return

        print(f'💬 User: {user_input}')

        # CLEAR COMMAND
        if user_input.lower() == 'clear':
            clear_history()
            emit('bot_response', {'message': '🔄 Conversation history cleared!', 'type': 'system'})
            return

        # INTENT DETECTION
        intent = resolve_intent(user_input)
        response = None

        if intent == "spotify":
            try:
                spotify.handle_spotify_command(user_input)
                response = "🎵 Spotify command executed."
            except Exception as e:
                response = f"⚠️ Spotify error: {e}"

        elif intent == "app_opening":
            try:
                response = app_handler.handle_command(user_input)
            except Exception as e:
                response = f"⚠️ App opening error: {e}"

        elif intent == "web_search":
            try:
                response = web_lookup.handle_command(user_input)
            except Exception as e:
                response = f"⚠️ Web search error: {e}"

        elif intent == "question":
            try:
                response = web_lookup.handle_command(user_input)
            except Exception as e:
                response = f"⚠️ Question error: {e}"

        else:
            # Default: Query the LLM
            response = query_llm(user_input, preset="sarcastic", temperature=0.7, max_tokens=512)

        # SPEAK RESPONSE (optional for console)
        voice.speak(response)
        print(f"🤖 Synclare: {response[:100]}...")

        # Send to browser
        emit('bot_response', {'message': response, 'type': 'bot'})

    except Exception as e:
        print(f"⚠️ Error: {e}")
        emit('error', {'message': f'Sorry, I encountered an error: {str(e)}'})


@socketio.on('clear_chat')
def handle_clear():
    clear_history()
    print('🗑️ Chat cleared')
    emit('bot_response', {'message': '🔄 Conversation cleared!', 'type': 'system'})


# =========================================================
# Console Interface (Optional)
# =========================================================
def console_mode():
    """Fallback console interface for local testing"""
    print("🧠 Synclare AI – Unified Console Mode")
    print("Type 'clear' to reset conversation or 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ['exit', 'quit']:
            print("👋 Goodbye!")
            break

        if user_input.lower() == 'clear':
            clear_history()
            print("🔄 Conversation cleared!")
            continue

        intent = resolve_intent(user_input)
        response = None

        try:
            if intent == "spotify":
                spotify.handle_spotify_command(user_input)
                response = "🎵 Spotify command executed."

            elif intent == "app_opening":
                response = app_handler.handle_command(user_input)

            elif intent == "web_search":
                response = web_lookup.handle_command(user_input)

            elif intent == "question":
                response = web_lookup.handle_command(user_input)

            else:
                response = query_llm(user_input, preset="sarcastic", temperature=0.7, max_tokens=512)

            print(f"Synclare: {response}\n")
            voice.speak(response)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            voice.speak("Sorry, I encountered an error.")


# =========================================================
# Entry Point
# =========================================================
if __name__ == '__main__':
    print("=" * 60)
    print("🌐 Starting Synclare Web Interface...")
    print("📱 Open http://localhost:5000 in your browser")
    print("🎤 Voice features work best in Chrome, Edge, or Safari")
    print("💻 Type 'python web_app.py console' for CLI-only mode")
    print("=" * 60)

    # Console Mode (if argument passed)
    if len(sys.argv) > 1 and sys.argv[1].lower() == "console":
        console_mode()
    else:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
