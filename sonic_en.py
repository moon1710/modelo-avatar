import os
os.environ["VOSK_LOG_LEVEL"] = "0"  # Suprime logs de Vosk

import pyttsx3
import time
import pyaudio
import json
from langchain_ollama import OllamaLLM
from vosk import Model as VoskModel, KaldiRecognizer, SetLogLevel

SetLogLevel(0)

# Inicializar el modelo de lenguaje (asegúrate de que Ollama esté corriendo y tenga "llama3.2")
model = OllamaLLM(model="llama3.2")

# Inicializar el sintetizador de voz
engine = pyttsx3.init()
voices = engine.getProperty('voices')

# Seleccionar una voz en inglés natural (buscando "english" en el nombre)
english_voice = None
for voice in voices:
    if "english" in voice.name.lower():
        english_voice = voice
        break

if english_voice:
    engine.setProperty('voice', english_voice.id)
    print(f"Using voice: {english_voice.name}")
else:
    engine.setProperty('voice', voices[0].id)

engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

# Función de reconocimiento con Vosk (tiempo máximo de 4 segundos)
def listen_user_vosk():
    # Actualiza la ruta si tu modelo está en otro directorio o con otro nombre
    vosk_model = VoskModel("modelo_vosk_en")
    sample_rate = 16000
    recognizer = KaldiRecognizer(vosk_model, sample_rate)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=4000)
    stream.start_stream()
    
    print("Listening... Please speak in English.")
    start_time = time.time()
    result_text = ""
    # Escuchar hasta 4 segundos para dar margen a la frase
    while time.time() - start_time < 4:
        data = stream.read(4000, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = recognizer.Result()
            res_dict = json.loads(result)
            result_text = res_dict.get("text", "").strip()
            if result_text:
                break
        else:
            # (Opcional) Imprime resultados parciales para debug
            partial = recognizer.PartialResult()
            res_dict = json.loads(partial)
            partial_text = res_dict.get("partial", "").strip()
            if partial_text:
                print("Interim:", partial_text)
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    if result_text:
        print("User:", result_text)
    else:
        print("No speech detected. Try again.")
    return result_text

# Seleccionar la función de reconocimiento (Vosk recomendado)
listen_func = listen_user_vosk

# Contexto para el chatbot en inglés
context = (
    "You are Sonic, the Blue Hedgehog, famous for your speed and relaxed attitude. "
    "Respond with a dynamic tone, full of energy and optimism, always ready for action. "
    "Keep your answers short, direct, and enthusiastic. "
    "Show a friendly and confident personality, and never lose your adventurous spirit. "
    "Answer in English."
)

def respond_with_voice(response):
    print("Bot (Sonic):", response)
    engine.say(response)
    engine.runAndWait()

def generate_response(question):
    prompt = f"{context}\nUser: {question}\nSonic:"
    response = model.invoke(prompt)
    return response.strip()

def main():
    print("Sonic Chatbot activated! Say 'bye' to end the conversation.")
    while True:
        user_input = listen_func()
        if user_input:
            if user_input.lower() == "bye":
                print("Ending conversation. Goodbye!")
                respond_with_voice("Goodbye! Keep on running!")
                break
            response = generate_response(user_input)
            respond_with_voice(response)

if __name__ == "__main__":
    main()
