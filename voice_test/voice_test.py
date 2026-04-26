#​‌​‌​​‌‌​‌‌‌‌​​‌​‌‌​‌‌‌​​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​​‌​‌‌‌​​‌​​‌‌​​‌​‌​‌​‌‌‌‌‌​‌​​​​​‌​‌‌​‌‌​​​‌‌​​‌​‌​‌‌‌‌​​​​‌​​​​‌​​‌‌​‌‌‌‌​‌‌‌​‌​​​‌​‌‌‌‌‌​‌​​​‌‌‌​‌‌​‌​​‌​‌‌‌​‌​​​‌​​‌​​​​‌‌‌​‌​‌​‌‌​​​‌​​‌​‌‌‌‌‌​​‌‌​​‌​​​‌‌​​​​​​‌‌​​‌​​​‌‌​‌​‌
#!/usr/bin/env python3
"""
Ultra-Low-Latency Real-Time Speech Translation Pipeline - FIXED VERSION
Target: <1.0s median end-to-end latency

Installation:
-------------
pip install faster-whisper webrtcvad pyaudio transformers torch pyttsx3

Usage:
------
python speech_translation_pipeline.py --src-lang en --tgt-lang de --model-size base
"""
from collections import deque
from typing import Optional, Dict, Any
import argparse
import numpy as np
import pyttsx3
import queue
import threading
import time

# Core dependencies
from faster_whisper import WhisperModel
from transformers import MarianMTModel, MarianTokenizer
import pyaudio
import webrtcvad

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

# ======================== CONFIGURATION ========================
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_MS = 30
VAD_AGGR = 2
CHUNK_MIN_MS = 200  # Increased from 150
CHUNK_TARGET_MS = 900  # Increased from 800
QUEUE_SIZE = 8
TIMEOUT = 0.1

# ======================== EVENT SCHEMA ========================

def make_event(event_type: str, seq: int, lang_src: str, lang_tgt: str,
               text: Optional[str] = None, audio: Optional[bytes] = None,
               is_final: bool = False, ts_start: Optional[int] = None,
               ts_end: Optional[int] = None) -> Dict[str, Any]:
    return {
        "type": event_type,
        "seq": seq,
        "lang_src": lang_src,
        "lang_tgt": lang_tgt,
        "text": text,
        "audio": audio,
        "is_final": is_final,
        "timestamps": {"start_ms": ts_start, "end_ms": ts_end}
    }

# ======================== THREAD-SAFE TTS MANAGER ========================
class TTSManager:
    """Thread-safe TTS manager with acoustic echo cancellation gating"""
    def __init__(self):
        self.engine = None
        self.tts_queue = queue.Queue()
        self.stop_event = threading.Event()
        self._speaking = threading.Event()  # NEW: AEC gate
        self.worker_thread = None
        
        if HAS_PYTTSX3:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 160)
                self.worker_thread = threading.Thread(target=self._worker, daemon=True)
                self.worker_thread.start()
            except Exception as e:
                print(f"[TTS Manager] Failed to init: {e}")
                self.engine = None
    
    def _worker(self):
        """Worker thread that processes TTS requests sequentially"""
        while not self.stop_event.is_set():
            try:
                text = self.tts_queue.get(timeout=0.1)
                if text and self.engine:
                    try:
                        self._speaking.set()  # Block mic input
                        self.engine.say(text)
                        self.engine.runAndWait()
                    except Exception as e:
                        print(f"[TTS Manager] Speak error: {e}")
                    finally:
                        time.sleep(0.3)  # Extra delay for acoustics
                        self._speaking.clear()  # Unblock mic
            except queue.Empty:
                continue
    
    def speak(self, text: str):
        """Add text to TTS queue (non-blocking)"""
        if self.engine:
            try:
                self.tts_queue.put(text, block=False)
            except queue.Full:
                pass
    
    def is_speaking(self) -> bool:
        """Check if TTS is currently active"""
        return self._speaking.is_set()
    
    def stop(self):
        """Stop the TTS worker"""
        self.stop_event.set()
        if self.worker_thread:
            self.worker_thread.join(timeout=1)

# Global TTS manager
tts_manager = None

# ======================== VAD CHUNKER ========================
class VADChunker(threading.Thread):
    def __init__(self, q_out: queue.Queue, stop_event: threading.Event,
                 lang_src: str = "auto"):
        super().__init__(name="VADChunker")
        self.q_out = q_out
        self.stop_event = stop_event
        self.lang_src = lang_src
        self.vad = webrtcvad.Vad(VAD_AGGR)
        self.frame_bytes = int(SAMPLE_RATE * FRAME_MS / 1000) * 2
        
    def run(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=CHANNELS,
                       rate=SAMPLE_RATE, input=True,
                       frames_per_buffer=self.frame_bytes // 2)
        
        chunk_buffer = b''
        chunk_start_ms = 0
        ts_ms = 0
        in_speech = False
        silence_frames = 0
        
        print("[VAD] Listening... Speak into your microphone.")
        
        try:
            while not self.stop_event.is_set():
                frame = stream.read(self.frame_bytes // 2, exception_on_overflow=False)
                
                # AEC-LITE GATING: Skip mic input while TTS is speaking
                if tts_manager and tts_manager.is_speaking():
                    ts_ms += FRAME_MS
                    # Reset speech detection during TTS
                    if in_speech and len(chunk_buffer) >= CHUNK_MIN_MS * SAMPLE_RATE * 2 // 1000:
                        chunk_len_ms = len(chunk_buffer) // 2 * 1000 // SAMPLE_RATE
                        try:
                            self.q_out.put((chunk_start_ms, ts_ms, chunk_buffer, self.lang_src),
 timeout = TIMEOUT)
                        except queue.Full:
                            pass
                    in_speech = False
                    chunk_buffer = b''
                    silence_frames = 0
                    continue
                
                is_speech = self.vad.is_speech(frame, SAMPLE_RATE)
                
                if is_speech:
                    if not in_speech:
                        chunk_start_ms = ts_ms
                        chunk_buffer = b''
                        in_speech = True
                        silence_frames = 0
                    chunk_buffer += frame
                else:
                    silence_frames = silence_frames + 1
                    if in_speech:
                        chunk_buffer += frame
                        # Longer silence threshold (14 frames = 420ms)
                        if silence_frames > 14:
                            chunk_len_ms = len(chunk_buffer) // 2 * 1000 // SAMPLE_RATE
                            if chunk_len_ms >= CHUNK_MIN_MS:
                                try:
                                    self.q_out.put((chunk_start_ms, ts_ms, 
                                                   chunk_buffer, self.lang_src),
                                                  timeout=TIMEOUT)
                                except queue.Full:
                                    print("[VAD] Queue full, dropping chunk")
                            in_speech = False
                            chunk_buffer = b''
                            silence_frames = 0
                
                ts_ms = ts_ms + FRAME_MS
                
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("[VAD] Stopped")

# ======================== STT WORKER ========================
class STTWorker(threading.Thread):
    def __init__(self, q_in: queue.Queue, q_out: queue.Queue,
                 stop_event: threading.Event, model_size: str = "base",
                 device: str = "cuda", compute_type: str = "int8"):
        super().__init__(name="STTWorker")
        self.q_in = q_in
        self.q_out = q_out
        self.stop_event = stop_event
        self.seq = 0
        
        print(f"[STT] Loading Whisper model '{model_size}' on {device}...")
        self.model = WhisperModel(model_size, device=device, 
                                  compute_type=compute_type)
        dummy = np.zeros(16000, dtype=np.float32)
        _ = list(self.model.transcribe(dummy, beam_size=1))
        print("[STT] Model loaded and warmed up")
        
    def run(self):
        while not self.stop_event.is_set():
            try:
                ts_start, ts_end, audio_bytes, lang_src = self.q_in.get(timeout=TIMEOUT)
            except queue.Empty:
                continue
            
            t0 = time.time()
            
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            
            segments, info = self.model.transcribe(
                audio_float32,
                beam_size=1,
                language=None if lang_src == "auto" else lang_src,
                vad_filter=False
            )
            
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            
            final_text = " ".join(text_parts).strip()
            detected_lang = info.language
            
            # Skip empty transcriptions
            if not final_text:
                continue
            
            # Add punctuation if missing
            if final_text and final_text[-1] not in ".!?":
                final_text += "."
            
            elapsed = (time.time() - t0) * 1000
            print(f"[STT] ({elapsed:.0f}ms) {detected_lang}: {final_text}")
            
            evt = make_event("final_transcript", self.seq, detected_lang, 
                           detected_lang, text=final_text, is_final=True,
                           ts_start=ts_start, ts_end=ts_end)
            
            try:
                self.q_out.put(evt, timeout=TIMEOUT)
            except queue.Full:
                print("[STT] Output queue full")
            
            self.seq = seq + 1

# ======================== TRANSLATION WORKER ========================
class TranslationWorker(threading.Thread):
    def __init__(self, q_in: queue.Queue, q_out: queue.Queue,
                 stop_event: threading.Event, tgt_lang: str = "de"):
        super().__init__(name="TranslationWorker")
        self.q_in = q_in
        self.q_out = q_out
        self.stop_event = stop_event
        self.tgt_lang = tgt_lang
        self.context_window = deque(maxlen=1)  # Reduced from 2
        self.last_translated = {}  # Dedupe cache
        
        print(f"[MT] Loading translation model for target: {tgt_lang}...")
        model_name = f"Helsinki-NLP/opus-mt-en-{tgt_lang}"
        try:
            self.tokenizer = MarianTokenizer.from_pretrained(model_name)
            self.model = MarianMTModel.from_pretrained(model_name)
            self.model.eval()
            print(f"[MT] Model loaded: {model_name}")
        except Exception as e:
            print(f"[MT] Failed to load model: {e}")
            self.model = None
        
    def run(self):
        while not self.stop_event.is_set():
            try:
                evt = self.q_in.get(timeout=TIMEOUT)
            except queue.Empty:
                continue
            
            if evt["type"] != "final_transcript":
                continue
            
            t0 = time.time()
            
            src_text = evt["text"]
            if not src_text:
                continue
            
            # Deduplicate identical consecutive texts
            seq = evt["seq"]
            if self.last_translated.get(seq) == src_text:
                continue
            self.last_translated[seq] = src_text
            
            # Short context (last 150 chars only)
            context = " ".join(self.context_window)[-150:]
            input_text = f"{context} {src_text}".strip() if context else src_text
            
            if self.model is None:
                translated = src_text
            else:
                try:
                    inputs = self.tokenizer([input_text], return_tensors="pt", 
                                           padding=True, truncation=True, max_length=512)
                    outputs = self.model.generate(**inputs, max_length=512, 
                                                 num_beams=3)  # Increased beam
                    translated = self.tokenizer.decode(outputs[0], 
                                                      skip_special_tokens=True)
                except Exception as e:
                    print(f"[MT] Translation error: {e}")
                    translated = src_text
            
            self.context_window.append(src_text)
            
            elapsed = (time.time() - t0) * 1000
            print(f"[MT] ({elapsed:.0f}ms) -> {translated}")
            
            trans_evt = make_event("final_translation", evt["seq"], 
                                 evt["lang_src"], self.tgt_lang,
                                 text=translated, is_final=True,
                                 ts_start=evt["timestamps"]["start_ms"],
                                 ts_end=evt["timestamps"]["end_ms"])
            
            try:
                self.q_out.put(trans_evt, timeout=TIMEOUT)
            except queue.Full:
                print("[MT] Output queue full")

# ======================== TTS WORKER ========================
class TTSWorker(threading.Thread):
    """Speaks the final translated text"""
    def __init__(self, q_in: queue.Queue, stop_event: threading.Event):
        super().__init__(name="TTSWorker")
        self.q_in = q_in
        self.stop_event = stop_event
        
    def run(self):
        while not self.stop_event.is_set():
            try:
                evt = self.q_in.get(timeout=TIMEOUT)
            except queue.Empty:
                continue
            
            if evt["type"] != "final_translation":
                continue
            
            text = evt["text"]
            if not text or not tts_manager:
                continue
            
            t0 = time.time()
            
            try:
                tts_manager.speak(text)
                elapsed = (time.time() - t0) * 1000
                print(f"[TTS] ({elapsed:.0f}ms) Speaking: {text}")
            except Exception as e:
                print(f"[TTS] Synthesis error: {e}")
        
        print("[TTS] Stopped")

# ======================== MAIN PIPELINE ========================
def main():
    global tts_manager
    
    parser = argparse.ArgumentParser(description="Real-time speech translation")
    parser.add_argument("--src-lang", default="en",
                       help="Source language (en, de, es, etc.) Use 'auto' for detection")
    parser.add_argument("--tgt-lang", default="de",
                       help="Target language code")
    parser.add_argument("--model-size", default="base",
                       choices=["tiny", "base", "small", "medium"])
    parser.add_argument("--device", default="cpu",
                       choices=["cuda", "cpu"])
    parser.add_argument("--compute-type", default="int8",
                       choices=["int8", "fp16", "float32"])
    parser.add_argument("--duration", type=int, default=60,
                       help="Run duration in seconds (0=infinite)")
    
    args = parser.parse_args()
    
    if not HAS_PYTTSX3:
        print("Error: pyttsx3 not found. Install with: pip install pyttsx3")
        return 1
    
    # Initialize global TTS manager
    tts_manager = TTSManager()
    
    print("="*60)
    print("Real-Time Speech Translation Pipeline - FIXED")
    print("="*60)
    print(f"Source: {args.src_lang} -> Target: {args.tgt_lang}")
    print(f"Model: {args.model_size} on {args.device} ({args.compute_type})")
    print("Acoustic Echo Cancellation: ENABLED")
    print("="*60)
    
    stop_event = threading.Event()
    
    vad2stt = queue.Queue(maxsize=QUEUE_SIZE)
    stt2mt = queue.Queue(maxsize=QUEUE_SIZE)
    mt2tts = queue.Queue(maxsize=QUEUE_SIZE)
    
    workers = []
    
    try:
        vad = VADChunker(vad2stt, stop_event, args.src_lang)
        stt = STTWorker(vad2stt, stt2mt, stop_event, 
                       args.model_size, args.device, args.compute_type)
        mt = TranslationWorker(stt2mt, mt2tts, stop_event, args.tgt_lang)
        tts = TTSWorker(mt2tts, stop_event)
        
        workers = [vad, stt, mt, tts]
        
        for w in workers:
            w.start()
        
        if args.duration > 0:
            print(f"\nRunning for {args.duration} seconds...")
            print("Press Ctrl+C to stop early\n")
            time.sleep(args.duration)
        else:
            print("\nRunning indefinitely. Press Ctrl+C to stop\n")
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\n[MAIN] Stopping pipeline...")
    finally:
        stop_event.set()
        for w in workers:
            w.join(timeout=2)
        if tts_manager:
            tts_manager.stop()
        print("[MAIN] Pipeline stopped")

if __name__ == "__main__":
    main()