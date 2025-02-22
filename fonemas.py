import threading
import tkinter as tk
import cv2
from PIL import Image, ImageTk
import keyboard
from langchain_ollama import OllamaLLM
from TTS.api import TTS
import simpleaudio as sa  # Para reproducir audio en Python
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import subprocess  # Para ejecutar eSpeak-NG y obtener fonemas
import time
import re
import wave
import itertools

def clean_phonemes(phonemes_text):
    lines = phonemes_text.split()  # cada chunk es un “fonema”
    cleaned_list = []

    for chunk in lines:
        # Quita acentos primarios y secundarios
        chunk = re.sub(r'[ˈˌ]', '', chunk)
        # Filtra caracteres que no estén en tu set
        chunk = re.sub(r'[^a-zA-Zɪʊɔæəʃʒŋθð]', '', chunk)

        if chunk.strip():
            cleaned_list.append(chunk)

    # Reúne los fonemas limpios
    return " ".join(cleaned_list)


def split_chunk_into_fonemas(chunk):
    chunk = re.sub(r"[ˈˌ]", "", chunk)  # Quitar acentos
    sub_fonemas = []
    
    i = 0
    while i < len(chunk):
        if i + 1 < len(chunk) and chunk[i:i+2] in phoneme_to_viseme:
            sub_fonemas.append(chunk[i:i+2])
            i += 2
        else:
            sub_fonemas.append(chunk[i])
            i += 1
    
    print(f"📌 Fonemas separados: {sub_fonemas}")  # 👀 Debug
    return sub_fonemas


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
    print(f"🔵 Cambiando imagen a: {image_key}")  # 👀 Debug
    pil_image = frames[image_key].resize((300, 300), Image.Resampling.LANCZOS)
    imgtk = ImageTk.PhotoImage(image=pil_image)
    video_label.imgtk = imgtk
    video_label.config(image=imgtk)


update_frame("neutral")

# ---------------------------
# Configuración del reconocimiento de voz (Vosk)
# ---------------------------
vosk_model_path = "modelo_vosk_en"
model = Model(vosk_model_path)
recognizer = KaldiRecognizer(model, 16000)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()

def listen_user():
    """Captura la entrada de audio del usuario usando Vosk (offline)."""
    print("Listening...")
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").strip()
            if text:
                print(f"User: {text}")
                return text
            else:
                print("No speech detected. Please try again.")

# ---------------------------
# Inicialización del modelo Llama desde Ollama (offline)
# ---------------------------
model = OllamaLLM(model="llama3.2")

# ---------------------------
# Contexto base del chatbot (en inglés)
# ---------------------------
context = (
    "Respond as Habib Bourguiba, Tunisia’s first president, in a formal and didactic tone. Give clear, convincing answers in only one or two sentences"
)

def get_wav_duration(filepath):
    with wave.open(filepath, 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration_in_seconds = frames / float(rate)
        return duration_in_seconds


def generate_response(question):
    """Genera una respuesta usando el modelo Ollama (funciona offline)."""
    prompt = f"{context}\nUser: {question}\nHabib:"
    response = model.invoke(prompt)
    return response.strip()

# ---------------------------
# 🔥 Función para extraer fonemas con eSpeak-NG
# ---------------------------
def extract_phonemes(text):
    """Convierte texto en fonemas usando eSpeak-NG y limpia la salida."""
    try:
        result = subprocess.run(
            ["espeak-ng", "-q", "--ipa", text],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if not result.stdout:
            print("⚠️ Advertencia: eSpeak-NG no devolvió fonemas.")
            return "neutral"

        phonemes_raw = result.stdout.strip().replace("\n", " ")
        print(f"📢 Fonemas crudos: {phonemes_raw}")

        # 🔹 **Eliminar acentos y caracteres extraños**
        phonemes_cleaned = re.sub(r"[ˈˌ]", "", phonemes_raw)

        # 🔹 **Dividir los fonemas compuestos correctamente**
        phonemes_split = re.findall(r"[a-zɪʊɔæəʃʒŋθð]+", phonemes_cleaned)

        phonemes_final = " ".join(phonemes_split)
        print(f"📢 Fonemas normalizados: {phonemes_final}")
        return phonemes_final

    except Exception as e:
        print(f"Error al extraer fonemas: {e}")
        return "neutral"


# 🔥 **Mapeo de fonemas a visemas**
phoneme_to_viseme = {
    "p": "m", "b": "m", "m": "m",
    "f": "f", "v": "f",
    "t": "t", "d": "t", "s": "s", "z": "s",
    "θ": "t", "ð": "t",
    "k": "k", "g": "k", "ŋ": "k",
    "ʃ": "sh", "ʒ": "sh", "h": "neutral",
    "i": "i", "ɪ": "i", "e": "e", "ɛ": "e",
    "a": "a", "ɑ": "a", "ɔ": "o", "o": "o",
    "u": "u", "ʊ": "u", "ə": "neutral",
    "n": "n", "l": "l", "r": "r",
    "w": "neutral", "j": "neutral",
    
    # 🔥 **Nuevos fonemas añadidos**
    "ɪə": "i", "eɪ": "e", "ɔɪ": "o",
    "aɪ": "a", "oʊ": "o", "uə": "u",
    "dʒ": "t", "tʃ": "t", "ʊə": "u"
}

# ---------------------------
# 🔥 Lipsync con animación de boca
# ---------------------------
def lipsync_animation(phonemes, duration=2):
    phoneme_list = phonemes.split(" ")
    total_time = duration / max(len(phoneme_list), 1)

    for phoneme in phoneme_list:
        viseme = phoneme_to_viseme.get(phoneme, "neutral")
        print(f"✅ Fonema '{phoneme}' -> Visema '{viseme}'")  # 👀 Debug
        
        update_frame(viseme)
        time.sleep(total_time)

    update_frame("neutral")

# ---------------------------
# Función para sintetizar voz y hacer lipsync
# ---------------------------
def speak_response(response):
    def run_tts():
        output_audio_path = "response.wav"
        print(f"Bot (Habib): {response}")

        # Extraer fonemas
        phonemes = extract_phonemes(response)
        phonemes = clean_phonemes(phonemes)

        # Generar audio con Coqui TTS
        tts.tts_to_file(text=response, speaker="p236", file_path=output_audio_path)

        # Calcular duración con wave
        audio_duration = get_wav_duration(output_audio_path)

        # Reproducir audio
        wave_obj = sa.WaveObject.from_wave_file(output_audio_path)
        play_obj = wave_obj.play()

        # Lanzar lipsync con la duración real del audio
        lipsync_animation(phonemes, duration=audio_duration)

        # Esperar a que termine el audio
        play_obj.wait_done()

    tts_thread = threading.Thread(target=run_tts)
    tts_thread.start()

# ---------------------------
# Bucle de conversación
# ---------------------------
def conversation_loop():
    """Bucle principal del chatbot. Espera la tecla 'M' para escuchar y procesa la conversación."""
    print("Chatbot activated as Habib! (OFFLINE MODE)")
    print("Press 'M' to start listening. Say 'exit' to end the conversation.")
    while True:
        print("Waiting for key press 'M'...")
        keyboard.wait('m')
        user_input = listen_user()
        if user_input:
            if user_input.lower() == "exit":
                print("Ending conversation. Goodbye!")
                speak_response("Goodbye, have a great day.")
                break
            response = generate_response(user_input)
            speak_response(response)

# Ejecutar el bucle de conversación en un hilo separado
conv_thread = threading.Thread(target=conversation_loop, daemon=True)
conv_thread.start()

# Iniciar el loop principal de Tkinter
root.mainloop()
