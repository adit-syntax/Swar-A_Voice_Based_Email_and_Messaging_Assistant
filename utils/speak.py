import pyttsx3
import sys
import os

def speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 145)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error in speech process: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_arg = " ".join(sys.argv[1:])
        
        # Check if input is a file path
        if os.path.exists(input_arg) and os.path.isfile(input_arg):
            try:
                with open(input_arg, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                print(f"Error reading speech file: {e}")
                text = "Error reading speech file."
        else:
            text = input_arg
            
        speak(text)
