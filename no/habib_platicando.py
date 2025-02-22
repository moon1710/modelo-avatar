import threading
import tkinter as tk
from PIL import Image, ImageTk
import pyttsx3
import speech_recognition as sr
import keyboard
from langchain_ollama import OllamaLLM

# Variables globales para el estado de la voz y el parpadeo del avatar
is_speaking = False
toggle = False

# ---------------------------
# Configuración del Avatar (Tkinter)
# ---------------------------
root = tk.Tk()
root.title("Avatar")

# Cargar imágenes del avatar
try:
    avatar_closed_img = Image.open("avatar_closed.png")
    avatar_open_img = Image.open("avatar_open.png")
except Exception as e:
    print("Error al cargar las imágenes del avatar:", e)
    exit(1)

# Redimensionar las imágenes (opcional)
avatar_closed_img = avatar_closed_img.resize((300, 300), Image.Resampling.LANCZOS)
avatar_open_img = avatar_open_img.resize((300, 300), Image.Resampling.LANCZOS)

avatar_closed = ImageTk.PhotoImage(avatar_closed_img)
avatar_open = ImageTk.PhotoImage(avatar_open_img)

# Label para mostrar el avatar
avatar_label = tk.Label(root, image=avatar_closed)
avatar_label.pack()

def update_avatar():
    """Actualiza la imagen del avatar para simular movimiento de boca."""
    global is_speaking, toggle
    if is_speaking:
        # Alterna entre la imagen con boca abierta y cerrada
        if toggle:
            avatar_label.config(image=avatar_open)
        else:
            avatar_label.config(image=avatar_closed)
        toggle = not toggle
    else:
        avatar_label.config(image=avatar_closed)
    # Vuelve a llamar esta función cada 200 ms
    root.after(200, update_avatar)

# Inicia la actualización del avatar
update_avatar()

# ---------------------------
# Configuración del TTS (pyttsx3)
# ---------------------------
# Initialize the text-to-speech engine
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id) 
engine.setProperty('rate', 150)  # Ajusta la velocidad de la voz
engine.setProperty('volume', 0.9)  # Ajusta el volumen

# ---------------------------
# Configuración del reconocimiento de voz
# ---------------------------
recognizer = sr.Recognizer()

# ---------------------------
# Inicializar el modelo Llama desde Ollama
# ---------------------------
model = OllamaLLM(model="llama3.2")

# ---------------------------
# Contexto base del chatbot (en inglés)
# ---------------------------
context = (
    "You are Habib Burguiba, an independent leader and the first president of Tunisia (1957-1987). "
    "Respond in a didactic tone, aiming to convince your audience of the ability to understand modern concepts. "
    "Speak formally, give short answers only 5 lines, but ensure clarity and comprehension."
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
    response = model(prompt)
    return response.strip()

def speak_response(response):
    """Reproduce la respuesta en audio y activa la animación del avatar."""
    global is_speaking
    def run_tts():
        global is_speaking
        engine.say(response)
        engine.runAndWait()
        is_speaking = False  # Finaliza la animación al terminar el audio
    is_speaking = True
    print(f"Bot (Habib): {response}")
    tts_thread = threading.Thread(target=run_tts)
    tts_thread.start()

def conversation_loop():
    """Bucle principal del chatbot. Espera la tecla 'M' para escuchar y procesa la conversación."""
    print("Chatbot activated as Habib!")
    print("Press 'M' to start listening. Say 'exit' to end the conversation.")
    while True:
        print("Waiting for key press 'M'...")
        keyboard.wait('m')  # Bloquea hasta que se presione la tecla 'M'
        user_input = listen_user()
        if user_input:
            if user_input.lower() == "exit":
                print("Ending conversation. Goodbye!")
                speak_response("Goodbye, have a great day.")
                break
            response = generate_response(user_input)
            speak_response(response)

# Ejecutar el bucle de conversación en un hilo separado
conv_thread = threading.Thread(target=conversation_loop)
conv_thread.start()

# Iniciar el loop principal de Tkinter
root.mainloop()
