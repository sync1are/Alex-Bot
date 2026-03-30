#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​‌​​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​​​‌​​‌​​​​‌‌‌​‌​‌​‌‌​​​‌​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
from subprocess import Popen
import os
import pyautogui
import re
import time

class AppOpening:
    def __init__(self):
        # Define app variations and their corresponding executable paths
        self.app_aliases = {
            "chrome": ["chrome", "google chrome"],
            "notepad": ["notepad", "text editor"],
            "calculator": ["calculator", "calc"],
            "spotify": ["spotify", "spotify app"],
            "vscode": ["vscode", "vs code", "visual studio code"]
        }
        
        self.app_mappings = {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "spotify": r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
            "vscode": r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        }
        
        # Set pyautogui safety net
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

    def extract_app_name(self, text: str) -> str:
        """Extract the app name from the command"""
        # Preserve original casing where possible. We'll operate on a lowercase copy
        original = text
        t = text.lower()
        phrases_to_remove = [
            "can you", "could you", "please", "open", "launch",
            "start", "run", "the", "app", "program"
        ]
        for phrase in phrases_to_remove:
            t = t.replace(phrase, "")

        # Clean up and get the main app name (attempt to return original-cased fragment)
        t = re.sub(r'\s+', ' ', t).strip()
        if not t:
            return ""

        # Try to find the matching fragment in the original text to preserve casing
        m = re.search(re.escape(t), original, flags=re.IGNORECASE)
        if m:
            return original[m.start():m.end()].strip()
        return t

    def extract_explicit_search(self, text: str) -> str:
        """Detect explicit 'search for' patterns and return the exact name provided.

        Examples handled:
        - 'search for this app: Riot Client'
        - 'search for Riot Client'
        - 'search app:Photoshop'
        """
        text_lower = text.lower()
        # Patterns to look for
        patterns = [
            r'search for this app\s*:\s*(.+)',
            r'search for\s+(.+)',
            r"search app\s*:\s*(.+)",
            r'search\s+(.+)'
        ]
        for pat in patterns:
            m = re.search(pat, text_lower)
            if m:
                # extract the matched group from the original text to preserve casing
                # find span of group within the lowered text, then map to original
                start, end = m.start(1), m.end(1)
                # map indices by searching the group text in the original (case-insensitive)
                group_text = m.group(1).strip()
 m2 = re.search(re.escape(group_text), text, flags = re.IGNORECASE)
                if m2:
                    raw = text[m2.start():m2.end()].strip()
                else:
                    raw = group_text
                # Remove trailing punctuation
                raw = re.sub(r'[\.|\?|!]+$', '', raw).strip()
                return raw
        return ""

    def search_windows(self, app_name: str, prefix_app: bool = False) -> str:
        """Search for app using Windows search"""
        try:
            # Press Windows key to open the Start/search UI
            pyautogui.press('win')
            time.sleep(0.4)
            # Type the app name directly (optionally prefix with 'app:')
            to_type = f"app:{app_name}" if prefix_app else app_name
            pyautogui.write(to_type)
            time.sleep(0.6)

            # Press Enter to launch the top/first result
            pyautogui.press("enter")

            return f"Attempting to launch {app_name} through Windows search..."
        except Exception as e:
            return f"Error while trying to launch {app_name}: {str(e)}"

    def handle_command(self, text: str) -> str:
        """Handle natural language commands to open applications"""
        text = text.lower()
        
        # If user explicitly asked to search for an app, prefer that exact query
        explicit = self.extract_explicit_search(text)
        if explicit:
            return self.search_windows(explicit)

        # Try to find any app name or alias in the text
        for app_key, aliases in self.app_aliases.items():
            if any(alias in text for alias in aliases):
                return self.launch_app(app_key)

        # If app not found in predefined list, try Windows search using fuzzy extraction
        app_name = self.extract_app_name(text)
        if app_name:
            # If the fuzzy-extracted name doesn't match a known alias, prefix with 'app:'
            # so Windows searches the Apps section
            is_known = any(app_name.lower() in [a.lower() for a in aliases] for aliases in self.app_aliases.values())
 return self.search_windows(app_name, prefix_app = not is_known)

        return "I couldn't understand which application to open. Please try again."

    def launch_app(self, app_name: str) -> str:
        """Launch the specified application"""
        try:
            if app_name in self.app_mappings:
                # Expand environment variables in the path
                app_path = os.path.expandvars(self.app_mappings[app_name])
                if os.path.exists(app_path):
                    # Start process without capturing output to avoid encoding issues
                    Popen([app_path], shell=True, stdout=None, stderr=None, close_fds=True)
                    return f"Launching {app_name}..."
                return f"Cannot find {app_name} at {app_path}"
            return f"Application {app_name} is not in my list of known applications"
        except Exception as e:
            return f"Error launching {app_name}: {str(e)}"

# Create instance for the command system
app_opening = AppOpening()