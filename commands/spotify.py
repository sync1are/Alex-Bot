#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​‌​​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​​​‌​​‌​​​​‌‌‌​‌​‌​‌‌​​​‌​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
import re
from .spotify_controls import play_song, next_track, previous_track, play_pause

def handle_spotify_command(command: str):
    text = command.lower().strip()

    if "next" in text or "skip" in text:
        next_track()
        return

    if "prev" in text or "previous" in text:
        previous_track()
        return

    if "pause" in text or "stop" in text:
        play_pause()
        return

    # Strict play detection
    # Pattern: play "song name" by "artist name" OR play song name by artist name
    pattern = r'play\s+"?([^"]+?)"?(?:\s+by\s+"?([^"]+?)"?)?$'
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        song_name, artist_name = match.groups()
        song_name = song_name.strip() if song_name else None
        artist_name = artist_name.strip() if artist_name else None
        if song_name:
            play_song(song_name, artist_name)
            return

    print("❓ Couldn't figure out what song you meant — try again!")
