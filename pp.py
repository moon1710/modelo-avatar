from TTS.api import TTS

# Cargar modelo con múltiples hablantes
tts = TTS("tts_models/en/vctk/vits")

# Mostrar la lista de hablantes disponibles
print("Hablantes disponibles:", tts.speakers)

# Elegir un hablante masculino específico
tts.tts_to_file(text="Hello, I have a deep male voice!", speaker="p236", file_path="male_voice.wav")

print("¡Audio con voz masculina generado!")
