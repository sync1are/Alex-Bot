#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​‌​​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​​​‌​​‌​​​​‌‌‌​‌​‌​‌‌​​​‌​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
import re

def resolve_intent(user_input: str) -> str:
    """
    Detect whether user input is a Spotify/music command, 
    a system command, or general chat.
    """
    text = user_input.lower()

    # Broader Spotify intent detection
    play_keywords = ["play", "pause", "next", "previous", "prev", "song", "music"]
    if any(word in text for word in play_keywords):
        # If sentence contains both 'play' and a likely song reference
        if re.search(r"\bplay\b", text):
            return "spotify"
        # if user mentions skip, pause, or next
        if any(word in text for word in ["pause", "next", "skip", "previous", "prev"]):
            return "spotify"
            
    # Web search intent detection
    search_phrases = ["search", "look up", "lookup", "find", "google", "search for"]
    search_patterns = [
        r"\b(search|google|find|lookup)\b",
        r"can you (search|find|look up)",
        r"could you (search|find|look up)",
        r"please (search|find|look up)",
        r"(search|find|look up).*please",
        r"(search|find|look up).*on (google|web|internet)",
        r"what is",
        r"who is",
        r"how to"
    ]
    
    # Add web search intent detection
    search_triggers = [
        "search for", "look up", "find info about", "tell me about",
        "what is", "who is", "what are", "how to", "why does",
        "when did", "where is",
    ]
    
    text_lower = text.lower()
    if any(trigger in text_lower for trigger in search_triggers):
        return "web_search"
        
    # Check for web search intent
    if any(re.search(pattern, text) for pattern in search_patterns):
        return "web_search"
    
    # App opening intent detection with natural language support
    open_phrases = ["open", "launch", "start", "run"]
    opening_patterns = [
        r"\b(open|launch|start|run)\b",
        r"can you (open|launch|start|run)",
        r"could you (open|launch|start|run)",
        r"please (open|launch|start|run)",
        r"(open|launch|start|run).*please",
    ]
    
    # Check for any app opening intent using regex patterns
    if any(re.search(pattern, text) for pattern in opening_patterns):
        return "app_opening"
        
    # Additional check for direct open phrases
    if any(phrase in text for phrase in open_phrases):
        return "app_opening"

    # Default: general conversation
    return "chat"
