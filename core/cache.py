#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​‌​​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​​​‌​​‌​​​​‌‌‌​‌​‌​‌‌​​​‌​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
import hashlib
import json
import os
import time

BASE_DIR = os.path.dirname(__file__)
DEFAULT_CACHE_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", ".cache"))
FALLBACK_CACHE_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "cache_dir"))

def _choose_cache_dir():
    # If default exists and is a directory -> use it
    if os.path.exists(DEFAULT_CACHE_DIR):
        if os.path.isdir(DEFAULT_CACHE_DIR):
            return DEFAULT_CACHE_DIR
        # It's a file (conflict) — use fallback instead of deleting user file
        print(f"Warning: cache path {DEFAULT_CACHE_DIR} exists and is a file. Using fallback: {FALLBACK_CACHE_DIR}")
        return FALLBACK_CACHE_DIR

    # Create default; if race or permission issue, fall back
    try:
 os.makedirs(DEFAULT_CACHE_DIR, exist_ok = True)
        return DEFAULT_CACHE_DIR
    except Exception:
        return FALLBACK_CACHE_DIR

CACHE_DIR = _choose_cache_dir()
os.makedirs(CACHE_DIR, exist_ok = True)

def _key_to_path(key: str) -> str:
    name = hashlib.sha1(key.encode("utf-8")).hexdigest() + ".json"
    return os.path.join(CACHE_DIR, name)

def get(key: str):
    path = _key_to_path(key)
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        expires = obj.get("expires_at")
        if expires and time.time() > expires:
            try:
                os.remove(path)
            except Exception:
                pass
            return None
        return obj.get("value")
    except Exception:
        return None

def set(key: str, value, ttl: int | None = None) -> bool:
    path = _key_to_path(key)
    obj = {"value": value}
    if ttl:
        obj["expires_at"] = time.time() + int(ttl)
    try:
        with open(path, "w", encoding="utf-8") as f:
 json.dump(obj, f, ensure_ascii = False)
        return True
    except Exception:
        return False
