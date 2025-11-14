💙 Pulsett Bot

Pulsett Bot es un asistente emocional desarrollado como proyecto académico.
Permite analizar mensajes de texto, audios y fotografías enviados por el usuario, ofreciendo respuestas empáticas basadas en:

Análisis de sentimiento del texto

Detección de emociones en imágenes

Transcripción y análisis emocional de mensajes de voz

Respuestas automáticas basadas en un dataset propio

Pulsett Bot se ejecuta en Telegram y utiliza técnicas básicas de IA para acompañar emocionalmente al usuario.

⭐ Características principales
🧠 1. Análisis de texto

Detecta estado emocional (positivo, negativo o neutral).

Recuerda la emoción anterior para generar respuestas más humanas.

Usa un dataset personalizado (responses_dataset.csv) para generar respuestas automáticas.

🎧 2. Transcripción y análisis de audios

Convierte audios .oga de Telegram en texto.

Utiliza Whisper (si está disponible) o SpeechRecognition (Google API).

Analiza el sentimiento del audio transcripto.

🖼️ 3. Análisis de imágenes

Detecta emociones en rostros enviados en fotografías.

Soporta: alegría, tristeza, enojo, sorpresa, miedo, disgusto y neutral.

🤖 4. Respuestas automáticas mejoradas

Generación de respuestas basadas en patrones definidos en un CSV.

Manejo más natural de conversaciones.

⏳ 5. Sistema de inactividad

Si el usuario no responde durante 2 minutos, el bot envía un mensaje de cierre automático empático.

🗂️ Estructura del proyecto
PulsettBot/
│── bot.py
│── README.md
│── requirements.txt
│── data/
│   └── responses_dataset.csv
│── modules/
│   ├── sentiment_analysis.py
│   ├── auto_responses.py
│   ├── speech_to_text.py
│   └── image_analysis.py
└── venv/  (entorno virtual)

⚙️ Tecnologías utilizadas

Python 3.10+

python-telegram-bot

Whisper (opcional)

SpeechRecognition

Transformers

Torch

Pillow

OpenCV

ffmpeg

🚀 Instrucciones para ejecutar el bot en cualquier computadora

Estas instrucciones fueron diseñadas especialmente para que cualquier persona (incluido el profesor) pueda ejecutar el proyecto sin problemas, incluso si no tiene configuraciones previas.

✔️ 1. Clonar el repositorio
git clone https://github.com/SantiDiaz2005/PulsettBot.git
cd PulsettBot

✔️ 2. Crear entorno virtual
python -m venv venv

✔️ 3. Activar entorno virtual
En Windows (CMD o PowerShell):
venv\Scripts\activate

En Git Bash:
source venv/Scripts/activate

En Linux / Mac:
source venv/bin/activate

✔️ 4. Instalar dependencias
pip install -r requirements.txt

✔️ 5. Instalar FFmpeg

El bot necesita FFmpeg para convertir audios de Telegram.

👉 Descargar:

https://www.gyan.dev/ffmpeg/builds/

Descargar ffmpeg-essentials_build.zip

Extraer la carpeta

Copiar la ruta del archivo:

.../ffmpeg-8.0-essentials_build/bin


Agregar esa ruta al PATH del sistema (Windows):

Abrir Editar variables de entorno

Ir a Path

Clic en Nuevo → pegar la ruta del bin

Guardar todo

✔️ 6. Configurar variable de entorno TELEGRAM_TOKEN

Crear un bot en Telegram usando @BotFather

Copiar el token (cadena larga con números y letras)

Configurarlo como variable de entorno:

En Windows:
setx TELEGRAM_TOKEN "AQUI_EL_TOKEN"

En Linux/Mac:
export TELEGRAM_TOKEN="AQUI_EL_TOKEN"


Reiniciar la terminal si es necesario.

✔️ 7. Ejecutar el bot
python bot.py


Si todo está bien, verás:

✅ Pulsett Bot iniciado. Presioná Ctrl+C para detener.


Abrir Telegram → buscar el bot → enviar mensajes.

🩵 Cómo usa IA el bot
✔ Sentimiento en Texto

Modelo clásico de clasificación → sentiment_analysis.py

✔ Auto-respuestas

Patrones predefinidos en CSV → auto_responses.py

✔ Audio

Intenta Whisper

Si no, usa SpeechRecognition

Conversión OGG → WAV con FFmpeg

✔ Imágenes

Usa un modelo de detección de rostros + clasificación de emociones.

🐞 Errores comunes y soluciones
❌ "TELEGRAM_TOKEN is None"

➡ No configuraste el token como variable de entorno.

❌ "ffmpeg: command not found"

➡ No agregaste FFmpeg al PATH.

❌ Audios sin transcribir

➡ Whisper no disponible → SpeechRecognition requiere internet.
➡ O el audio es muy corto.

❌ Error al instalar torch

➡ En Windows instalar versión compatible:

pip install torch --index-url https://download.pytorch.org/whl/cpu

👨‍💻 Autores

Santiago Díaz

ChatGPT como asistente tecnológico

Proyecto presentado para la materia Inteligencia Artificial.

🏁 Estado del proyecto

Versión final lista para entrega.
Código limpio, funcionando, probado y documentado.

📩 ¿Consultas?

Cualquier duda puede ejecutarse directamente con este README.