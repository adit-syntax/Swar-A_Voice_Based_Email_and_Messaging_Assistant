import speech_recognition as sr
import threading
import time
import subprocess
import sys
import os

# Subprocess-based TTS to avoid blocking main thread or COM issues
_current_process = None

def speak(text):
    """
    Spawns a separate process to speak the text. Non-blocking.
    """
    global _current_process
    if not text: return
    
    # Stop previous if any
    stop_speaking()
    
    try:
        # We use Popen so it runs in background and doesn't block
        script_path = os.path.join(os.path.dirname(__file__), "speak.py")
        
        # Write text to a temp file to avoid command line length limits
        # Use a fixed temp file name so we don't spam files
        temp_file = os.path.join(os.path.dirname(__file__), "temp_speech.txt")
        try:
             with open(temp_file, "w", encoding="utf-8") as f:
                 f.write(text)
        except Exception as e:
             print(f"Error writing temp speech file: {e}")
             return

        print(f"Assistant Speaking (Subprocess): [Content of {temp_file}]")
        _current_process = subprocess.Popen([sys.executable, script_path, temp_file])
    except Exception as e:
        print(f"Speech Subprocess Error: {e}")

def stop_speaking():
    """
    Terminates the current speech process immediately.
    """
    global _current_process
    if _current_process:
        print("DEBUG: Terminating speech process...")
        try:
            _current_process.terminate()
            _current_process = None
        except Exception as e:
            print(f"Error terminating process: {e}")

def is_speaking():
    """
    Returns True if the assistant is currently speaking (subprocess active).
    """
    global _current_process
    if _current_process and _current_process.poll() is None:
        return True
    return False

def listen(timeout=5, phrase_time_limit=5, adjust_noise=True, energy_threshold=None):
    r = sr.Recognizer()
    if energy_threshold:
        r.energy_threshold = energy_threshold
    with sr.Microphone() as source:
        print("Listening...")
        # Fast adjust
        # Fast adjust - reduced to 0.1s to speed up response loop
        if adjust_noise:
            r.adjust_for_ambient_noise(source, duration=0.1)
        
        # Optimization: Stop listening sooner after silence
        r.pause_threshold = 0.5  # Default is 0.8
        r.non_speaking_duration = 0.4 # Default is 0.5
        try:
            # If speaking, we might hear ourselves. 
            # Ideally we pause recognized audio if it matches outgoing TTS? Too complex.
            # We rely on user saying "STOP" loud enough or during pause.
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            print("Recognizing...")
            text = r.recognize_google(audio)
            print(f"User said: {text}")
            return text.lower()
        except Exception:
            return None
