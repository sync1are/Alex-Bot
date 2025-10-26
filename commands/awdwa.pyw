import time
import pyautogui
import re

class WebSearch:
    def __init__(self):
        # Set pyautogui safety net
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

    def extract_search_query(self, text: str) -> str:
        """Extract search query from the command, preserving original case"""
        # Common phrases to remove
        phrases_to_remove = [
            "search for",
            "search",
            "look up",
            "lookup",
            "find",
            "google",
            "web search",
            "can you",
            "could you",
            "please",
            "on the web",
            "on google",
            "online"
        ]
        
        # Work with lowercase for removal but keep original for return
        original = text
        text_lower = text.lower()
        
        # Remove common phrases
        for phrase in phrases_to_remove:
            text_lower = text_lower.replace(phrase, "")
            
        # Clean up whitespace
        text_lower = re.sub(r'\s+', ' ', text_lower).strip()
        
        if not text_lower:
            return ""
            
        # Try to find the cleaned text in the original to preserve case
        m = re.search(re.escape(text_lower), original.lower())
        if m:
            start, end = m.span()
            # Map to original text to preserve casing
            return original[start:end].strip()
        return text_lower

    def search_web(self, query: str) -> str:
        """
        Search the web using Windows search with ? prefix
        """
        try:
            # Press Windows key
            pyautogui.press('win')
            time.sleep(0.4)
            
            # Type ? followed by the search query
            search_text = f"?{query}"
            pyautogui.write(search_text)
            time.sleep(0.5)
            
            # Press Enter to execute the search
            pyautogui.press('enter')
            
            return f"Searching the web for: {query}"
        except Exception as e:
            return f"Error while trying to search: {str(e)}"

    def handle_command(self, text: str) -> str:
        """Handle web search commands"""
        query = self.extract_search_query(text)
        if query:
            return self.search_web(query)
        return "I couldn't understand what to search for. Please try again."

# Create instance for the command system
web_search = WebSearch()