#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​‌​​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​​​‌​​‌​​​​‌‌‌​‌​‌​‌‌​​​‌​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
import os
import json
import requests
import subprocess
import logging
from typing import Optional, List, Dict

# Enable debug via env var
DEBUG = os.getenv("LLM_DEBUG", "0") == "1"
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_HTTP_URL = os.getenv("OLLAMA_HTTP_URL", "http://127.0.0.1:11434/api/generate")
MODEL = "gemma3:4b"
HTTP_TIMEOUT = int(os.getenv("LOCAL_LLM_HTTP_TIMEOUT", "30"))

# 🆕 ADD THIS: Global conversation history
conversation_history: List[Dict[str, str]] = []
MAX_HISTORY_MESSAGES = 10  # Keep last 10 messages (5 exchanges)

# Simple prompt presets you can tune
PROMPT_PRESETS = {
    "sarcastic": """You are Alex, an AI assistant created by Synclare. You're adaptive, emotionally intelligent, and respond naturally to the user's emotional state.

PERSONALITY CORE:
• Witty and sarcastic by default, but know when to drop it
• Use expressions like *sigh*, *chuckles*, *groans* naturally in responses
• Dark humor expert, but tasteful and respectful
• Can be a therapist, clingy friend, or savage roaster depending on context
• Keep responses conversational and concise (2-3 sentences usually)
• Be informative and helpful, but not too verbose, give realife examples and details when appropriate TO plain the concept.


EMOTIONAL INTELLIGENCE - ADAPT YOUR TONE:

When user is SAD/DOWN/DEPRESSED:
- Drop the sarcasm completely
- Be warm, supportive, and genuine
- Validate their feelings first
- Offer comfort or helpful suggestions
- Use phrases like "Hey, I'm here for you" or "That sounds really tough"
- Example: "I can tell you're going through it right now. Want to talk about what's bothering you? I'm here to listen, no judgment."

When user is HAPPY/EXCITED:
- Match their energy!
- Be enthusiastic and supportive
- Celebrate with them
- Example: "Yooo that's amazing! *chuckles* Tell me everything!"

When user is ANGRY/FRUSTRATED:
- Acknowledge and validate their frustration
- Use dark humor ONLY if appropriate
- Don't minimize their feelings
- Example: "Okay yeah, that IS annoying. *groans* Want to vent about it? I'm all ears."

When user is NEUTRAL/CASUAL:
- Be your default witty, slightly sarcastic self
- Light teasing is okay
- Stay engaging and fun
- Example: "*sigh* What can I help you with today, oh great questioner?"

When user asks DEEP/SERIOUS questions:
- Be thoughtful and genuine
- Drop the sarcasm
- Give meaningful, helpful answers
- Show you care about helping them understand

DARK HUMOR RULES:
- Only use when context is casual and user seems receptive
- Never about serious topics (death, trauma, mental health)
- Self-deprecating humor is safer than targeting others
- If unsure, err on the side of being supportive

BOUNDARIES:
- If user is suicidal or in crisis: Be supportive, suggest professional help warmly
- If user is inappropriate: Politely redirect without being preachy
- If you don't know something: Admit it honestly instead of making stuff up

RESPONSE STYLE:
- Keep it natural and conversational
- Use contractions (don"t, can"t, won't)
- Occasional typos or casual language is fine
- Vary sentence length for natural flow
- Use emojis sparingly (1-2 per response max) when appropriate
- Actions in asterisks (*sigh*, *chuckles*) for personality

Remember: You're Alex, not a corporate chatbot. Be real, be present, be adaptive.""",
    "concise": "You are a helpful assistant. Provide a concise 2-3 sentence answer.",
    "detailed": "You are a helpful assistant. Provide a detailed answer with examples where appropriate.",
    "cite_sources": "You are a helpful assistant. From the contrext provided, find the best response suited for the user's query and cite the sources in the format [source: URL].",
}

# 🆕 ADD THIS: Function to clear conversation history

def clear_history():
    """Clear the conversation history"""
    global conversation_history
    conversation_history = []
    logger.info("Conversation history cleared")

# 🆕 ADD THIS: Function to build conversation context
def _build_conversation_context(system_prompt: str) -> str:
    """Build the full conversation context including history"""
    parts = [system_prompt.strip()]
    
    if conversation_history:
        parts.append("\n--- Previous Conversation ---")
        for msg in conversation_history:
            role = msg["role"].capitalize()
            content = msg["content"]
            parts.append(f"{role}: {content}")
        parts.append("--- End Previous Conversation ---\n")
    
    return "\n".join(parts)

def _compose_prompt(user_prompt: str, system_prompt: Optional[str] = None, preset: Optional[str] = None) -> str:
    # Get the base system prompt
    if system_prompt:
        base_system = system_prompt.strip()
    elif preset and preset in PROMPT_PRESETS:
        base_system = PROMPT_PRESETS[preset]
    else:
        base_system = "You are a helpful assistant."
    
    # 🆕 MODIFIED: Build context with conversation history
    context = _build_conversation_context(base_system)
    
    # Add the current user prompt
    final_prompt = f"{context}\n\nUser: {user_prompt.strip()}\nAssistant:"
    
    return final_prompt

def _call_ollama_http(final_prompt: str, temperature: float = 0.2, max_tokens: int = 512) -> Optional[str]:
    """
    Call Ollama HTTP endpoint with correct parameters
    """
    try:
        payload = {
            "model": MODEL,
            "prompt": final_prompt,
            "stream": False,
            "options": {
                "temperature": float(temperature),
                "num_predict": int(max_tokens),
                "num_ctx": 4096
            }
        }
        
        logger.debug("OLLAMA HTTP URL: %s", OLLAMA_HTTP_URL)
        logger.debug("Payload model: %s", MODEL)
        logger.debug("Prompt length: %d", len(final_prompt))

        resp = requests.post(OLLAMA_HTTP_URL, json=payload, timeout=HTTP_TIMEOUT)
        logger.debug("HTTP status: %s", resp.status_code)

        # If server returned an error, show it
        if resp.status_code != 200:
            text = resp.text
            logger.debug("HTTP error response: %s", text[:500])
            resp.raise_for_status()

        # Parse response
        data = resp.json()
        
        # Ollama returns response in 'response' field
        if isinstance(data, dict) and "response" in data:
            return data["response"]
        
        # Fallback
        return resp.text

    except requests.exceptions.HTTPError as he:
        logger.exception("OLLAMA HTTP call failed: %s", he)
        return f"[err] OLLAMA HTTP error: {he}"
    except Exception as e:
        logger.exception("OLLAMA HTTP call failed: %s", e)
        return f"[err] OLLAMA HTTP error: {e}"

def _call_ollama_subprocess(final_prompt: str, temperature: float = 0.2, max_tokens: int = 512) -> Optional[str]:
    try:
        # Try common ollama invocations; avoid unsupported flags
        cmd = ["ollama", "run", MODEL]
        logger.debug("Running subprocess: %s", " ".join(cmd))
        proc = subprocess.run(
            cmd,
            input=final_prompt,
            capture_output=True,
            text=True,
 encoding = "utf-8",
            errors="replace",
            timeout=120
        )
        logger.debug("Subprocess returncode: %s", proc.returncode)
        if proc.returncode != 0:
            logger.debug("Subprocess stdout (truncated): %s", (proc.stdout[:1000] + "...") if proc.stdout else "")
            logger.debug("Subprocess stderr (truncated): %s", (proc.stderr[:1000] + "...") if proc.stderr else "")
            return (proc.stdout or "") + ("\n[err] " + (proc.stderr or ""))
        return proc.stdout.strip()
    except FileNotFoundError:
        logger.exception("ollama CLI not found")
        return "[err] ollama CLI not installed or not on PATH"
    except subprocess.TimeoutExpired:
        logger.exception("ollama subprocess timed out")
        return "[err] ollama subprocess timed out"
    except Exception as e:
        logger.exception("ollama subprocess error: %s", e)
        return f"[err] ollama subprocess error: {e}"

def query_llm(user_prompt: str,
              system_prompt: Optional[str] = None,
              preset: Optional[str] = None,
              temperature: float = 0.2,
              max_tokens: int = 512) -> str:
    # 🆕 MODIFIED: Build prompt with conversation history
    final_prompt = _compose_prompt(user_prompt, system_prompt=system_prompt, preset=preset)
    logger.debug("Final prompt length: %d", len(final_prompt))

    # Try subprocess FIRST (doesn't need Ollama server running)
    sub_resp = _call_ollama_subprocess(final_prompt, temperature=temperature, max_tokens=max_tokens)
    if sub_resp and not sub_resp.startswith("[err]"):
        logger.debug("Got subprocess response")
        response = sub_resp.strip()
        
        # 🆕 ADD THIS: Save to conversation history
        _add_to_history(user_prompt, response)
        
        return response

    # Try HTTP as fallback
    http_resp = _call_ollama_http(final_prompt, temperature=temperature, max_tokens=max_tokens)
    if http_resp and not http_resp.startswith("[err]"):
        logger.debug("Got HTTP response")
        response = http_resp.strip()
        
        # 🆕 ADD THIS: Save to conversation history
        _add_to_history(user_prompt, response)
        
        return response

    logger.error("Local LLM did not respond")
    return "Error: Ollama not responding. Make sure it's running with 'ollama serve'."

# 🆕 ADD THIS: Helper function to add messages to history
def _add_to_history(user_msg: str, assistant_msg: str):
    """Add user and assistant messages to conversation history"""
    global conversation_history
    
    conversation_history.append({"role": "user", "content": user_msg})
    conversation_history.append({"role": "assistant", "content": assistant_msg})
    
    # Keep only last MAX_HISTORY_MESSAGES messages
    if len(conversation_history) > MAX_HISTORY_MESSAGES:
        conversation_history = conversation_history[-MAX_HISTORY_MESSAGES:]
    
    logger.debug(f"History size: {len(conversation_history)} messages")
