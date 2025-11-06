# 🤖 Pulsett Bot

### 🧘‍♀️ Asistente Inteligente de Bienestar Emocional

Pulsett Bot es un **asistente de Telegram impulsado por Inteligencia Artificial**, diseñado para acompañarte en tu **bienestar emocional**.  
Analiza tus emociones en tres dimensiones clave — **texto, voz e imágenes** — para ofrecerte respuestas empáticas, útiles y adaptadas a tu estado de ánimo.

---

## ✨ Descripción General

Pulsett Bot combina análisis de **Procesamiento de Lenguaje Natural (NLP)**, **reconocimiento de emociones en voz** y **visión por computadora** para ofrecer un apoyo integral.

Su misión es **proporcionar un espacio seguro y empático** donde los usuarios puedan expresarse y recibir orientación emocional automatizada pero humana.

---

## 💡 Características Clave

### 🎤 Análisis de Tono (Voz → Sentimiento)
- Transcribe notas de voz a texto con tecnología *speech-to-text*.
- Analiza la prosodia y el tono de la voz para detectar emociones como **alegría**, **tristeza**, **calma** o **estrés**.

### 🖼️ Interpretación Visual del Ánimo
- Procesa imágenes enviadas por el usuario.
- Detecta expresiones faciales o condiciones de luz para inferir el **estado emocional general** o el **contexto ambiental**.

### ✍️ Análisis Profundo de Texto
- Evalúa el sentimiento (positivo, negativo o neutral) en los mensajes escritos.
- Identifica la intención y contexto para brindar respuestas coherentes y naturales.

### 🫂 Respuestas Empáticas Personalizadas
- Utiliza un dataset propio con respuestas diseñadas para **acompañar emocionalmente al usuario**.
- Las respuestas se adaptan dinámicamente según el tipo de emoción detectada.

### 🔒 Privacidad Garantizada
- Pulsett Bot no almacena datos sensibles.
- Los análisis se realizan de forma **local y confidencial**, priorizando tu seguridad y bienestar.

---

## 🧠 Tecnologías Utilizadas

- **Lenguaje:** Python 3.10+
- **Librerías principales:**
  - `python-telegram-bot`
  - `textblob`, `nltk`, `transformers` → Análisis de texto
  - `speechrecognition`, `whisper` → Audio a texto
  - `opencv`, `deepface` → Análisis de imágenes
  - `pandas`, `scikit-learn` → Dataset y automatización de respuestas

---

## ⚙️ Instalación y Ejecución

### 1️⃣ Clonar el repositorio
```bash
git clone https://github.com/SantiDiaz2005/PulsettBot.git
cd PulsettBot
