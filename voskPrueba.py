import pyaudio
import json
from vosk import Model, KaldiRecognizer

# Ruta del modelo descargado (ajústala según dónde lo guardaste)
vosk_model_path = "modelo_vosk_en"

# Cargar el modelo
model = Model(vosk_model_path)
recognizer = KaldiRecognizer(model, 16000)

# Configurar PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()

print("🎤 Diga algo...")

while True:
    data = stream.read(4000, exception_on_overflow=False)
    if recognizer.AcceptWaveform(data):
        result = json.loads(recognizer.Result())
        print(f"🗣️ Texto reconocido: {result.get('text', '')}")
