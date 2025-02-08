import pyttsx3
import speech_recognition as sr
from langchain_ollama import OllamaLLM
import platform

# Initialize the Llama model from Ollama
model = OllamaLLM(model="llama3.2")

# Initialize the speech synthesizer
engine = pyttsx3.init()
voices = engine.getProperty('voices')

# Display available voices for debugging
print("Available voices:")
for index, voice in enumerate(voices):
    print(f"Index {index}: {voice.name} ({voice.id})")

# Attempt to select an English voice:
selected_voice = None

# First, try to select a male English voice if available
for voice in voices:
    if "english" in voice.name.lower():
        if any(male_key in voice.name.lower() for male_key in ["david", "alex", "daniel"]):
            selected_voice = voice
            break

# If no male English voice is found, select any English voice
if selected_voice is None:
    for voice in voices:
        if "english" in voice.name.lower():
            selected_voice = voice
            break

if selected_voice is not None:
    engine.setProperty('voice', selected_voice.id)
    print(f"Selected voice: {selected_voice.name}")
else:
    engine.setProperty('voice', voices[0].id)
    print(f"No English voice found. Using default voice: {voices[0].name}")

engine.setProperty('rate', 150)   # Adjust the speech rate
engine.setProperty('volume', 0.9)   # Adjust the volume

# Initialize the speech recognizer
recognizer = sr.Recognizer()

# Base instruction for the Habib Burguiba chatbot context (in English)
context = (
    "You are Habib Burguiba, the influential founding father of modern Tunisia. "
    "Renowned for your wisdom and progressive leadership, you guided Tunisia through transformative reforms. "
    "Respond with measured insight, clarity, and respect. "
    "Keep your answers concise, direct, and thoughtful. "
    "Answer in English."
)

def listen_to_user():
    """Captures audio input from the user using PocketSphinx (offline)."""
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            # Wait up to 5 seconds for input
            audio = recognizer.listen(source, timeout=5)
            # Offline speech recognition with PocketSphinx
            text = recognizer.recognize_sphinx(audio)
            print(f"User: {text}")
            return text
        except sr.WaitTimeoutError:
            print("Timeout: no audio input detected.")
            return None
        except sr.UnknownValueError:
            print("Audio not understood. Please repeat.")
            return None
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return None

def speak_response(response):
    """Generates audio from the text response."""
    print(f"Bot (Habib): {response}")
    engine.say(response)
    engine.runAndWait()

def generate_response(question):
    """Generates a response using the Ollama model."""
    prompt = f"{context}\nUser: {question}\nHabib:"
    response = model.invoke(prompt)  # Using invoke to avoid deprecation warnings
    return response.strip()

def main():
    print("Habib Chatbot activated! Say 'exit' to end the conversation.")
    while True:
        user_input = listen_to_user()
        if user_input:
            if user_input.lower() == "exit":
                print("Ending conversation. Goodbye!")
                speak_response("Goodbye! May progress and wisdom guide you.")
                break
            response = generate_response(user_input)
            speak_response(response)

if __name__ == "__main__":
    main()
