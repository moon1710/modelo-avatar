import threading
import tkinter as tk
import cv2
from PIL import Image, ImageTk
import keyboard
from langchain_ollama import OllamaLLM
from TTS.api import TTS
import simpleaudio as sa
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import time
from g2p_en import G2p

# ---------------------------
# Configuración de la ventana y video idle (Tkinter + OpenCV)
# ---------------------------
root = tk.Tk()
root.title("Chatbot with Lipsync")

# Inicializa Coqui TTS con una voz masculina (funciona offline)
tts = TTS("tts_models/en/vctk/vits")

# Cargar imágenes para lipsync
frames = {
    "neutral": Image.open("./assets/fonemas/neutral.png"),
    "a": Image.open("./assets/fonemas/a.png"),
    "e": Image.open("./assets/fonemas/e.png"),
    "i": Image.open("./assets/fonemas/i.png"),
    "o": Image.open("./assets/fonemas/o.png"),
    "u": Image.open("./assets/fonemas/u.png"),
    "m": Image.open("./assets/fonemas/m.png"),
}

video_label = tk.Label(root)
video_label.pack()

def update_frame(image_key):
    """Cambia la imagen según el fonema detectado"""
    if image_key not in frames:
        image_key = "neutral"
    print(f"🔵 Cambiando imagen a: {image_key}")  
    pil_image = frames[image_key].resize((300, 300), Image.Resampling.LANCZOS)
    imgtk = ImageTk.PhotoImage(image=pil_image)
    video_label.imgtk = imgtk
    video_label.config(image=imgtk)

update_frame("neutral")

# ---------------------------
# Configuración del reconocimiento de voz (Vosk)
# ---------------------------
vosk_model_path = "modelo_vosk_en"
vosk_model = Model(vosk_model_path)
recognizer = KaldiRecognizer(vosk_model, 16000)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()

import queue

audio_queue = queue.Queue()

def listen_user():
    """Captura la entrada de audio del usuario usando Vosk (offline)."""
    print("Listening...")
    try:
        data = stream.read(4000, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").strip()
            if text:
                print(f"User: {text}")
                return text
    except Exception as e:
        print(f"Error in listen_user(): {e}")
    return None

# ---------------------------
# Inicialización del modelo Llama desde Ollama (offline)
# ---------------------------
model = OllamaLLM(model="llama3.2")

context = (
    "Respond as Habib Bourguiba, Tunisia’s first president, in a formal and didactic tone. "
    "Give clear, convincing answers in only one or two sentences."
)

def generate_response(question):
    """Genera una respuesta usando el modelo Ollama (funciona offline)."""
    prompt = f"{context}\nUser: {question}\nHabib:"
    response = model.invoke(prompt)
    return response.strip()

# ---------------------------
# 🔥 Extraer fonemas con G2P (sin eSpeak)
# ---------------------------
g2p = G2p()

def extract_phonemes(text):
    """Convierte texto en fonemas usando G2P (sin eSpeak)."""
    phonemes = g2p(text)
    phonemes = [p for p in phonemes if p.isalpha()]  # Elimina símbolos raros
    phoneme_str = " ".join(phonemes)
    print(f"📢 Fonemas extraídos: {phoneme_str}")
    return phoneme_str

# 🔥 **Mapeo de fonemas a visemas**
phoneme_to_viseme = {
    "p": "viseme_p", "b": "viseme_p", "m": "viseme_m",
    "f": "viseme_f", "v": "viseme_f",
    "t": "viseme_t", "d": "viseme_t", "s": "viseme_s", "z": "viseme_s",
    "k": "viseme_k", "g": "viseme_k", "ŋ": "viseme_k",
    "ʃ": "viseme_sh", "ʒ": "viseme_sh",
    "i": "viseme_i", "ɪ": "viseme_i", "e": "viseme_e", "ɛ": "viseme_e",
    "a": "viseme_a", "ɑ": "viseme_a", "ɔ": "viseme_o", "o": "viseme_o",
    "u": "viseme_u", "ʊ": "viseme_u",
    "n": "viseme_n", "l": "viseme_l", "r": "viseme_r",
}

# ---------------------------
# 🔥 Lipsync con animación de boca
# ---------------------------
def lipsync_animation(phonemes, duration=2.5):
    """Mueve los labios según los fonemas detectados"""
    phoneme_list = phonemes.split(" ")
    total_time = duration / max(len(phoneme_list), 1)

    for phoneme in phoneme_list:
        viseme = phoneme_to_viseme.get(phoneme, "neutral")
        print(f"🟢 Fonema detectado: {phoneme} -> Cambiando a visema: {viseme}")  
        update_frame(viseme)
        time.sleep(total_time)

    update_frame("neutral")  

# ---------------------------
# Función para sintetizar voz y hacer lipsync
# ---------------------------
def speak_response(response):
    """Reproduce la respuesta en audio y hace lipsync sincronizado"""
    def run_tts():
        output_audio_path = "response.wav"
        print(f"Bot (Habib): {response}")
        
        phonemes = extract_phonemes(response)

        # **Ejecutar lipsync en un hilo separado**
        lipsync_thread = threading.Thread(target=lipsync_animation, args=(phonemes, 3))
        lipsync_thread.start()

        # **Generar audio con Coqui TTS**
        tts.tts_to_file(text=response, speaker="p236", file_path=output_audio_path)

        # **Reproducir audio**
        wave_obj = sa.WaveObject.from_wave_file(output_audio_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()

    tts_thread = threading.Thread(target=run_tts)
    tts_thread.start()

# ---------------------------
# Bucle de conversación
# ---------------------------
def conversation_loop():
    """Bucle principal del chatbot en un hilo separado."""
    print("Chatbot activated as Habib! (OFFLINE MODE)")
    print("Press 'M' to start listening. Say 'exit' to end the conversation.")

    while True:
        print("Waiting for key press 'M'...")
        keyboard.wait('m')

        user_thread = threading.Thread(target=process_user_input)
        user_thread.start()
# Ejecutar el bucle de conversación en un hilo separado
conv_thread = threading.Thread(target=conversation_loop, daemon=True)
conv_thread.start()

def process_user_input():
    """Procesa la entrada de usuario en un hilo separado."""
    user_input = listen_user()
    if user_input:
        if user_input.lower() == "exit":
            print("Ending conversation. Goodbye!")
            speak_response("Goodbye, have a great day.")
            return
        response = generate_response(user_input)
        speak_response(response)

# Iniciar el loop principal de Tkinter
root.mainloop()
