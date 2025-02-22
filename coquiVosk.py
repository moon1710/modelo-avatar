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

# ---------------------------
# Configuración de la ventana y video idle (Tkinter + OpenCV)
# ---------------------------
root = tk.Tk()
root.title("Chatbot with Idle Video")

# Inicializa Coqui TTS con una voz masculina (funciona offline)
tts = TTS("tts_models/en/vctk/vits")

# Ruta del video idle
video_path = "./assets/idle_video.mp4"
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print(f"Error: Could not open video {video_path}")
    exit(1)

# Label para mostrar el video
video_label = tk.Label(root)
video_label.pack()

def update_frame():
    ret, frame = cap.read()
    if ret:
        # Convertir BGR a RGB
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(cv2image)
        pil_image = pil_image.resize((300, 300), Image.Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=pil_image)
        video_label.imgtk = imgtk
        video_label.config(image=imgtk)
    else:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    video_label.after(30, update_frame)

update_frame()

# ---------------------------
# Configuración del reconocimiento de voz (Vosk)
# ---------------------------
vosk_model_path = "modelo_vosk_en"  # Ruta de tu modelo descargado
model = Model(vosk_model_path)
recognizer = KaldiRecognizer(model, 16000)

# Inicializa el micrófono con PyAudio
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
    "You are Habib Burguiba, an independent leader and the first president of Tunisia (1957-1987). "
    "Respond in a didactic tone, aiming to convince your audience of the ability to understand modern concepts. "
    "Speak formally, give short answers (only 5 lines) and ensure clarity and comprehension."
)

def generate_response(question):
    """Genera una respuesta usando el modelo Ollama (funciona offline)."""
    prompt = f"{context}\nUser: {question}\nHabib:"
    response = model.invoke(prompt)
    return response.strip()

# ---------------------------
# Función para sintetizar voz (Coqui TTS - offline)
# ---------------------------
def speak_response(response):
    """Reproduce la respuesta en audio usando Coqui TTS (100% offline)."""
    def run_tts():
        output_audio_path = "response.wav"
        print(f"Bot (Habib): {response}")
        
        # Generar el audio con voz masculina
        tts.tts_to_file(text=response, speaker="p236", file_path=output_audio_path)

        # Reproducir el archivo de audio generado
        wave_obj = sa.WaveObject.from_wave_file(output_audio_path)
        play_obj = wave_obj.play()
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
