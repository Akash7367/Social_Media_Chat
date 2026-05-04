import speech_recognition as sr
import pyttsx3

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# Optional: Setup voice properties
# Set the speed of speech
engine.setProperty('rate', 150)
# Set the volume (0.0 to 1.0)
engine.setProperty('volume', 1.0)

# Optional: To change voice (0 for male, 1 for female usually depending on the system)
# voices = engine.getProperty('voices')
# engine.setProperty('voice', voices[1].id)

def speak(text):
    """
    Convert the given text to speech.
    """
    print(f"Assistant: {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    """
    Listen to user's voice and convert it into text.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nListening...")
        # Adjusting for ambient noise helps increase the accuracy
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        try:
            # Listen to the user's input
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            print("Recognizing...")
            
            # Using Google's free web speech API to recognize the audio
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text.lower()
            
        except sr.WaitTimeoutError:
            print("Timeout: I didn't hear anything.")
            return None
        except sr.UnknownValueError:
            print("Sorry, I could not understand the audio.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Speech Recognition service; {e}")
            return None

def main():
    speak("Hello! I am ready. You can speak now.")
    
    while True:
        command = listen()
        
        if command:
            # Example conditions based on the voice command
            if "exit" in command or "stop" in command or "quit" in command:
                speak("Goodbye! Have a great day.")
                break
            
            elif "hello" in command or "hi" in command:
                speak("Hello there! How are you?")
                
            elif "how are you" in command:
                speak("I am just a computer program, but I'm doing great! How can I help you?")
                
            else:
                # Default response mirroring the command
                speak(f"I heard you say: {command}")

if __name__ == "__main__":
    main()
