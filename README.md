# Chatbot Project

Este proyecto implementa un chatbot que utiliza síntesis y reconocimiento de voz junto con el modelo Ollama para generar respuestas. Se han desarrollado tres versiones del proyecto, cada una utilizando diferentes conjuntos de librerías para el reconocimiento de voz.

## Versiones

### Versión 1
**Imports:**
python
import pyttsx3
import speech_recognition as sr
from langchain_ollama import OllamaLLM
import platform

# Instalación
Clona el repositorio:
git clone 
cd chatbot-project

# Instala las dependencias:
pip install -r requirements.txt
Nota: Es posible que necesites instalar dependencias adicionales para pyaudio y vosk en tu sistema.

# Uso
Ejecuta el script deseado, por ejemplo:
python chatbot.py
El chatbot se iniciará y estará listo para interactuar mediante entrada y salida de voz.

# Contribuciones
Las contribuciones son bienvenidas. Si deseas mejorar o extender este proyecto, por favor crea un pull request o abre un issue en el repositorio.