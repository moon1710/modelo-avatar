import pyttsx3
import pyaudio
import json
from vosk import Model as VoskModel, KaldiRecognizer
from langchain_ollama import OllamaLLM

# Inicializar el modelo Llama desde Ollama, apuntando al servidor local.
model = OllamaLLM(model="llama3.2", base_url="http://localhost:11434")

# Inicializar el sintetizador de voz
engine = pyttsx3.init()
voices = engine.getProperty('voices')

# Mostrar las voces disponibles para depuración
print("Voces disponibles:")
for index, voice in enumerate(voices):
    print(f"Índice {index}: {voice.name} ({voice.id})")

# Seleccionar una voz válida:
if len(voices) > 3:
    engine.setProperty('voice', voices[3].id)
else:
    engine.setProperty('voice', voices[0].id)

engine.setProperty('rate', 150)   # Ajusta la velocidad de la voz
engine.setProperty('volume', 0.9)   # Ajusta el volumen

# Configurar Vosk para el reconocimiento de voz en español
# Asegúrate de que la carpeta "modelo_vosk_es" esté en el mismo directorio que este script
vosk_model = VoskModel("modelo_vosk_es")
sample_rate = 16000  # Frecuencia de muestreo requerida por el modelo
recognizer_vosk = KaldiRecognizer(vosk_model, sample_rate)

def escuchar_usuario():
    """
    Captura la entrada de audio del usuario utilizando Vosk (offline).
    Se usa un bucle para capturar audio hasta detectar un resultado completo.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=8000)
    stream.start_stream()
    print("Escuchando con Vosk...")

    texto = ""
    # Se lee continuamente hasta que se detecte una frase completa
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if recognizer_vosk.AcceptWaveform(data):
            result = recognizer_vosk.Result()
            result_dict = json.loads(result)
            texto = result_dict.get("text", "")
            break
        else:
            # Si deseas ver resultados parciales, puedes imprimirlos (opcional)
            # partial_result = recognizer_vosk.PartialResult()
            # result_dict = json.loads(partial_result)
            # print(f"Usuario (parcial): {result_dict.get('partial', '')}")
            pass

    stream.stop_stream()
    stream.close()
    p.terminate()
    print(f"Usuario: {texto}")
    return texto

def responder_con_voz(respuesta):
    """Genera audio a partir de la respuesta de texto."""
    print(f"Bot (Habib): {respuesta}")
    engine.say(respuesta)
    engine.runAndWait()

# Contexto del chatbot de Habib Burguiba en español
contexto = (
    "Eres Habib Burguiba, el influyente líder y fundador de la Túnez moderna. "
    "Reconocido por tu visión progresista y tus reformas que transformaron la nación, "
    "responde con sabiduría, claridad y un tono respetuoso. "
    "Mantén tus respuestas concisas, directas y llenas de conocimiento. "
    "Responde en español."
)

def generar_respuesta(pregunta):
    """Genera una respuesta utilizando el modelo Ollama."""
    prompt = f"{contexto}\nUsuario: {pregunta}\nHabib:"
    respuesta = model.invoke(prompt)
    return respuesta.strip()

def main():
    print("¡Chatbot activado como Habib Burguiba! Di 'salir' para terminar la conversación.")
    while True:
        entrada = escuchar_usuario()
        if entrada:
            if entrada.lower() == "salir":
                print("Terminando la conversación. ¡Hasta luego!")
                responder_con_voz("¡Hasta luego! Que la sabiduría y el progreso te acompañen.")
                break
            respuesta = generar_respuesta(entrada)
            responder_con_voz(respuesta)

if __name__ == "__main__":
    main()
