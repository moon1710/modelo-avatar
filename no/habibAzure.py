import threading
import tkinter as tk
import cv2
from PIL import Image, ImageTk
import speech_recognition as sr
import keyboard
import azure.cognitiveservices.speech as speechsdk
from langchain_ollama import OllamaLLM

# ---------------------------
# Configuración de la ventana y video idle (Tkinter + OpenCV)
# ---------------------------
root = tk.Tk()
root.title("Chatbot with Idle Video")

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
        # Convertir a imagen PIL
        pil_image = Image.fromarray(cv2image)
        # Redimensionar la imagen (opcional)
        pil_image = pil_image.resize((300, 300), Image.Resampling.LANCZOS)
        # Convertir a PhotoImage
        imgtk = ImageTk.PhotoImage(image=pil_image)
        # Guardar la referencia para evitar que se elimine
        video_label.imgtk = imgtk
        video_label.config(image=imgtk)
    else:
        # Si se terminó el video, reinicia al inicio
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    # Programar la actualización en aproximadamente 30ms (~33 fps)
    video_label.after(30, update_frame)

update_frame()

# ---------------------------
# Configuración del reconocimiento de voz (speech_recognition)
# ---------------------------
recognizer = sr.Recognizer()

# ---------------------------
# Configuración de Azure TTS
# ---------------------------
# Reemplaza estos valores con tus credenciales de Azure
AZURE_SPEECH_KEY = "EcKQFvWR21ytClVMWGFMxSplUazeOoUPrFzF0MbbMt0hH8l7D6wdJQQJ99BBACYeBjFXJ3w3AAAYACOG4HTQ"
AZURE_SERVICE_REGION = "eastus"

speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SERVICE_REGION)
# Selecciona una voz masculina en inglés (por ejemplo, "en-US-GuyNeural")
speech_config.speech_synthesis_voice_name = "en-US-GuyNeural"
speech_config.speech_synthesis_output_format = speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

def speak_response(response):
    """Reproduce la respuesta en audio usando Azure TTS creando un sintetizador nuevo en cada llamada."""
    def run_tts():
        # Crear una nueva configuración y sintetizador para cada llamada
        speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SERVICE_REGION)
        speech_config.speech_synthesis_voice_name = "en-US-GuyNeural"  # Voz masculina en inglés
        speech_config.speech_synthesis_output_format = speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        result = synthesizer.speak_text_async(response).get()
        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Error synthesizing speech:", result.error_details)
    print(f"Bot (Habib): {response}")
    tts_thread = threading.Thread(target=run_tts)
    tts_thread.start()


# ---------------------------
# Inicialización del modelo Llama desde Ollama
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

def listen_user():
    """Captura la entrada de audio del usuario."""
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio, language="en-US")
            print(f"User: {text}")
            return text
        except sr.UnknownValueError:
            print("Audio not understood. Please repeat.")
            return None
        except sr.RequestError as e:
            print(f"Error with the voice recognition service: {e}")
            return None

def generate_response(question):
    """Genera una respuesta usando el modelo Ollama."""
    prompt = f"{context}\nUser: {question}\nHabib:"
    # Nota: se muestra una advertencia de deprecación; para el futuro se recomienda usar model.invoke(prompt)
    response = model(prompt)
    return response.strip()

def conversation_loop():
    """Bucle principal del chatbot. Espera la tecla 'M' para escuchar y procesa la conversación."""
    print("Chatbot activated as Habib!")
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

# Ejecutar el bucle de conversación en un hilo separado (daemon para que se cierre junto con la aplicación)
conv_thread = threading.Thread(target=conversation_loop, daemon=True)
conv_thread.start()

# Iniciar el loop principal de Tkinter
root.mainloop()
