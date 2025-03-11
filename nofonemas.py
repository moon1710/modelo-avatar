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


# ---------------------------
# Configuración de la ventana y video idle (Tkinter + OpenCV)
# ---------------------------
root = tk.Tk()
root.title("Chatbot with Lipsync")

# Inicializa Coqui TTS con una voz masculina (funciona offline)
tts = TTS("tts_models/en/vctk/vits")
# Cargar imágenes para lipsync
frames = {
    "neutral": Image.open("./imgs/neutral_enh.png"),
    "a": Image.open("./imgs/a_enh.png"),
    "e": Image.open("./imgs/e_enh.png"),
    "i": Image.open("./imgs/i_enh.png"),
    "o": Image.open("./imgs/o_enh.png"),
    "u": Image.open("./imgs/u_enh.png"),
    "m": Image.open("./imgs/m_enh.png"),
    "f": Image.open("./imgs/f_enh.png"),
    "s": Image.open("./imgs/s_enh.png"),
    "t": Image.open("./imgs/t_enh.png"),
    "l": Image.open("./imgs/l_enh.png"),
    "r": Image.open("./imgs/r_enh.png"),
    "n": Image.open("./imgs/n_enh.png"),
    "k": Image.open("./imgs/k_enh.png"),
    "h": Image.open("./imgs/h_enh.png")
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
    "Respond as Habib Bourguiba, Tunisia's first president. Use a formal and dignified tone. "
    "Keep your answers brief and to the point - use only one short sentence when possible. "
    "Be concise but authoritative in your responses. Avoid lengthy explanations or historical details "
    "unless specifically asked. Speak as a respected leader addressing the people."
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
    """Convierte texto en fonemas usando eSpeak-NG y mejora la limpieza."""
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

        # 🔹 **Eliminar espacios innecesarios y caracteres fuera de IPA**
        phonemes_cleaned = re.findall(r"[a-zɪʊɔæəʃʒŋθð]+", phonemes_cleaned)

        # 🔹 **Eliminar fonemas duplicados (ejemplo: "ðð" → "ð")**
        phonemes_cleaned = [re.sub(r"(\w)\1+", r"\1", phoneme) for phoneme in phonemes_cleaned]

        phonemes_final = " ".join(phonemes_cleaned)
        print(f"📢 Fonemas normalizados: {phonemes_final}")
        return phonemes_final

    except Exception as e:
        print(f"❌ Error al extraer fonemas: {e}")
        return "neutral"

# 🔹 **Mapeo de duración de visemas**
viseme_durations = {
    "m": 0.6, "p": 0.6, "b": 0.6,
    "f": 0.5, "v": 0.5,
    "t": 0.4, "d": 0.4, "s": 0.3, "z": 0.3,
    "k": 0.4, "g": 0.4,
    "i": 0.5, "e": 0.5, "a": 0.6, "o": 0.6, "u": 0.6,
    "n": 0.5, "l": 0.5, "r": 0.5,
    "neutral": 0.2
}


letter_to_viseme = {
    "a": "a", "e": "e", "i": "i", "o": "o", "u": "u",  # Vocales abiertas
    "m": "m", "p": "m", "b": "m",  # Labiales cerrados
    # Otras consonantes se reemplazan con "m"
    "f": "m", "v": "m",  # Labiodentales
    "s": "m", "z": "m", "t": "m", "d": "m",  # Sonidos con dientes juntos
    "l": "m", "r": "m", "n": "m",  # Sonidos líquidos/nasales
    "w": "m", "y": "m",  # Semivocales
    "c": "m", "k": "m", "g": "m", "x": "m",  # Sonidos velares
    "h": "m", "j": "m", "q": "m"  # Agregando más sonidos
}

# ---------------------------
# 🔥 Lipsync con animación de boca
# ---------------------------
import random

def text_to_visemes(text):
    """Convierte texto en una lista de visemas según las letras."""
    text = text.lower()
    visemes = [letter_to_viseme.get(char, "neutral") for char in text if char.isalpha()]
    return visemes

def lipsync_animation(text, duration):
    viseme_list = text_to_visemes(text)
    if not viseme_list:
        update_frame("neutral")
        return

    base_durations = [viseme_durations.get(viseme, 0.4) for viseme in viseme_list]
    total_base_duration = sum(base_durations)
    scale_factor = duration / total_base_duration if total_base_duration > 0 else 1

    def update_viseme_frame(i, start_time):
        if i < len(viseme_list):
            viseme = viseme_list[i]
            base_duration = base_durations[i]
            scaled_duration = base_duration * scale_factor
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Si la próxima duración sobrepasa el audio, ajusta el tiempo
            if elapsed + scaled_duration > duration:
                scaled_duration = duration - elapsed
            
            update_frame(viseme)
            root.after(int(scaled_duration * 1000), update_viseme_frame, i + 1, start_time)
        else:
            update_frame("neutral")

    start_time = time.time()
    update_viseme_frame(0, start_time)


def speak_response(response):
    def run_tts():
        output_audio_path = "response.wav"
        print(f"Bot (Habib): {response}")

        # 🔹 **Generar audio con Coqui TTS**
        tts.tts_to_file(text=response, speaker="p236", file_path=output_audio_path)

        # 🔹 **Calcular duración con wave**
        audio_duration = get_wav_duration(output_audio_path)

        # 🔹 **Reproducir audio**
        wave_obj = sa.WaveObject.from_wave_file(output_audio_path)
        play_obj = wave_obj.play()

        # 🔹 **Lanzar lipsync con la duración real del audio**
        lipsync_animation(response, duration=audio_duration)

        # 🔹 **Esperar a que termine el audio**
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
