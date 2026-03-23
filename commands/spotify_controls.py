#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​‌​​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​​​‌​​‌​​​​‌‌‌​‌​‌​‌‌​​​‌​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
# spotify_controls.py - COMPLETE VERSION
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import subprocess
import time
import platform
import os

# Authenticate
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="61aad8cea3f2456c8e89d57d9c5ddedb",
    client_secret="017e51c7cb2e4c54a17d68108e4d17c1",
    redirect_uri="http://127.0.0.1:3000/callback",
    scope="user-read-playback-state,user-modify-playback-state,user-read-currently-playing"
))


def open_spotify():
    """Open Spotify application"""
    try:
        username = os.getenv('USERNAME')
        spotify_path = rf"C:\Users\{username}\AppData\Roaming\Spotify\Spotify.exe"
        
        if os.path.exists(spotify_path):
            os.startfile(spotify_path)
            print("🎵 Opening Spotify...")
            time.sleep(5)
            return True
        else:
            print(f"❌ Spotify not found at: {spotify_path}")
            return False
    except Exception as e:
        print(f"❌ Could not open Spotify: {e}")
        return False


def activate_device():
    """Make sure a Spotify device is active"""
    devices = sp.devices()
    
    if not devices['devices']:
        print("💡 No Spotify device found. Opening Spotify...")
        open_spotify()
        
        time.sleep(3)
        devices = sp.devices()
        
        if not devices['devices']:
            print("❌ Still no device found. Please make sure Spotify is installed.")
            return None
    
    device = devices['devices'][0]
    print(f"📱 Using device: {device['name']}")
    return device['id']


def play_song(song_name, artist_name=None):
    """Play a song"""
    try:
        device_id = activate_device()
        if not device_id:
            return False
        
        query = f"{song_name} artist:{artist_name}" if artist_name else song_name
        results = sp.search(q=query, type='track', limit=1)
        tracks = results['tracks']['items']
        
        if not tracks:
            print(f"❌ Song not found: {query}")
            return False
        
        track = tracks[0]
        sp.start_playback(device_id=device_id, uris=[track['uri']])
        print(f"🎶 Now playing: {track['name']} by {track['artists'][0]['name']}")
        return True
        
    except Exception as e:
        print(f"❌ Playback error: {e}")
        return False


def next_track():
    """Next track"""
    try:
        sp.next_track()
        print("⏭️ Next track")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def previous_track():
    """Previous track"""
    try:
        sp.previous_track()
        print("⏮️ Previous track")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def play_pause():
    """Toggle play/pause"""
    try:
        current = sp.current_playback()
        if current and current['is_playing']:
            sp.pause_playback()
            print("⏸️ Paused")
        else:
            device_id = activate_device()
            if device_id:
                sp.start_playback(device_id=device_id)
                print("▶️ Playing")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
