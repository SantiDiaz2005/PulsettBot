# bot.py
import os
import logging
import random
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from modules.sentiment_analysis import analyze_sentiment
from modules.auto_responses import get_autoresponder
from modules.speech_to_text import transcribe_audio
from modules.image_analysis import analyze_image

# -------------------------------
# CONFIGURACIÓN DE LOGS
# -------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token desde variables de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Dataset de auto-respuestas
auto_responder = get_autoresponder("data/responses_dataset.csv")

# -------------------------------
# RESPUESTAS BASE
# -------------------------------
WELCOME_MESSAGES = [
    "👋 ¡Hola! Soy Pulsett Bot 🤖. Estoy acá para acompañarte, ¿cómo te sentís hoy?",
    "🌈 ¡Bienvenido! Podemos charlar sobre lo que necesites 💬",
    "💙 ¡Hola! Me alegra verte por acá. Contame, ¿cómo va tu día?",
    "🤗 ¡Hola! Soy tu compañero emocional digital. Estoy para escucharte."
]

NEUTRAL_BASE = [
    "🙂 Gracias por compartir eso. Si querés hablar más, estoy acá.",
    "🧠 Entiendo. Contame si querés profundizar un poco.",
    "😌 Gracias por confiarme lo que sentís."
]

POSITIVE_BASE = [
    "🌟 Qué alegría leerte así. Disfrutá este buen momento 💪.",
    "😄 Me pone contento tu buena energía.",
    "✨ Me encanta leer eso. Seguí así 💙."
]

NEGATIVE_BASE = [
    "💙 Lamento que estés pasando por un momento difícil. Estoy con vos.",
    "😔 Entiendo cómo te sentís. Si querés hablar, te escucho.",
    "🤍 Gracias por compartirlo. No estás solo."
]

# -------------------------------
# COMANDOS
# -------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensaje inicial"""
    await update.message.reply_text(random.choice(WELCOME_MESSAGES))
    context.user_data["active"] = True
    asyncio.create_task(inactivity_timer(update, context))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 *Comandos disponibles:*\n\n"
        "/start - Iniciar conversación\n/help - Mostrar ayuda\n\n"
        "Podés enviarme texto, audio o imágenes 😊",
        parse_mode="Markdown"
    )

# -------------------------------
# MANEJADOR DE TEXTO
# -------------------------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_raw = update.message.text
    text = text_raw.lower().strip()

    # Detectar saludos
    SALUDOS = ["hola", "buenas", "hey", "holaa", "buen día", "buenas tardes", "buenas noches"]
    if any(text.startswith(s) for s in SALUDOS):
        await update.message.reply_text("👋 ¡Hola! ¿Cómo te sentís hoy?")
        context.user_data["last_emotion"] = "neutral"
        return

    # Análisis emocional
    sent = analyze_sentiment(text_raw)
    tone = sent["label"].lower()
    last_tone = context.user_data.get("last_emotion", None)

    reply = f"🔍 *Análisis de sentimiento:* {sent['label'].capitalize()}.\n\n"

    # Respuestas según emoción
    if tone == "negativo":
        if last_tone == "positivo":
            reply += "😔 Noto un cambio en tu ánimo. Si querés hablar, estoy acá."
        else:
            reply += random.choice(NEGATIVE_BASE)

    elif tone == "positivo":
        if last_tone == "negativo":
            reply += "💪 Me alegra mucho ver que te sentís mejor 🙌."
        else:
            reply += random.choice(POSITIVE_BASE)

    else:  # neutral
        auto_reply = auto_responder.predict_response(text_raw)
        if auto_reply:
            reply += auto_reply
        else:
            reply += random.choice(NEUTRAL_BASE)

    context.user_data["last_emotion"] = tone
    await update.message.reply_text(reply, parse_mode="Markdown")

# -------------------------------
# MANEJADOR DE AUDIO
# -------------------------------
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.voice.get_file()
    local_ogg = f"temp_{update.message.message_id}.oga"
    await file.download_to_drive(custom_path=local_ogg)

    await update.message.reply_text("🎧 Estoy escuchando tu mensaje... un momento ⏳")

    # Transcribir
    text = transcribe_audio(local_ogg)

    # Borrar archivo temporal
    if os.path.exists(local_ogg):
        os.remove(local_ogg)

    if not text or not text.strip():
        await update.message.reply_text(
            "😕 No pude entender tu audio. ¿Podés intentar de nuevo o escribirme cómo te sentís?"
        )
        return

    # Analizar sentimiento del texto transcrito
    sent = analyze_sentiment(text)
    tone = sent["label"].lower()

    reply = "🧠 *Análisis de tu mensaje de voz:*\n\n"

    if tone == "positivo":
        reply += random.choice(POSITIVE_BASE)
    elif tone == "negativo":
        reply += random.choice(NEGATIVE_BASE)
    else:
        reply += random.choice(NEUTRAL_BASE)

    await update.message.reply_text(reply, parse_mode="Markdown")

# -------------------------------
# MANEJADOR DE IMAGEN
# -------------------------------
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    local_jpg = f"temp_photo_{update.message.message_id}.jpg"
    await file.download_to_drive(custom_path=local_jpg)

    await update.message.reply_text("🖼️ Analizando la imagen... un momento ⚪")

    res = analyze_image(local_jpg)
    if os.path.exists(local_jpg):
        os.remove(local_jpg)

    emotion = res.get("emotion", "unknown").lower()

    reply_map = {
        "happy": "🙂 Parece una emoción positiva.",
        "sad": "💙 La imagen transmite tristeza. ¿Querés contarme qué pasó?",
        "angry": "😠 Veo enojo o frustración.",
        "surprise": "😮 Algo inesperado parece haber ocurrido.",
        "fear": "😰 La imagen muestra miedo o ansiedad.",
        "disgust": "🤢 Veo señales de disgusto.",
        "neutral": "😐 La expresión es bastante neutra."
    }

    reply = f"🖼️ *Análisis de imagen:*\nEmoción detectada: **{emotion.capitalize()}**\n\n"
    reply += reply_map.get(emotion, "🙂 No estoy completamente seguro de la emoción.")

    await update.message.reply_text(reply, parse_mode="Markdown")

# -------------------------------
# MENSAJE DE CIERRE AUTOMÁTICO
# -------------------------------
async def inactivity_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(120)
    if context.user_data.get("active", False):
        await update.message.reply_text(
            "💙 Gracias por charlar conmigo. Estoy acá cuando necesites hablar 🫂"
        )
        context.user_data["active"] = False

# -------------------------------
# MAIN
# -------------------------------
def main():
    if TELEGRAM_TOKEN is None:
        print("❌ ERROR: Falta la variable de entorno TELEGRAM_TOKEN.")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("✅ Pulsett Bot iniciado. Presioná Ctrl+C para detener.")
    app.run_polling()


if __name__ == "__main__":
    main()

