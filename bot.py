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
    ContextTypes,
    filters,
)

from modules.sentiment_analysis import analyze_sentiment
from modules.auto_responses import get_autoresponder
from modules.speech_to_text import transcribe_audio
from modules.image_analysis import analyze_image

# -------------------------------------------------------------------
# LOGGING
# -------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# CONFIGURACIÓN
# -------------------------------------------------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
auto_responder = get_autoresponder("data/responses_dataset.csv")

WELCOME_MESSAGES = [
    "👋 ¡Hola! Soy Pulsett Bot 🤖. Estoy acá para acompañarte, ¿cómo te sentís hoy?",
    "🌈 ¡Bienvenido! Soy Pulsett Bot. Podemos charlar sobre lo que necesites 💬",
    "💙 ¡Hola! Me alegra verte por acá. Contame, ¿cómo va tu día?",
    "🤗 ¡Hola! Soy tu compañero emocional digital. Estoy acá para escucharte.",
]

NEUTRAL_BASE = [
    "🙂 Gracias por compartir cómo te sentís. A veces no tenerlo del todo claro también está bien.",
    "🧠 Entiendo, y aprecio que lo compartas conmigo. Si querés charlar un poco más, estoy acá.",
    "😌 Gracias por contarme eso. Poner en palabras lo que sentimos ya es un gran paso.",
]

POSITIVE_BASE = [
    "🌟 Qué alegría leerte así. Me encanta saber que estás bien, seguí aprovechando ese estado de ánimo para recargar energía 💪.",
    "😄 Me pone muy contento ver tu buena energía. Disfrutá este momento y hacé algo que te haga sonreír.",
    "✨ Me encanta leer eso. Cada día con una sonrisa es una victoria, seguí así 💙.",
]

NEGATIVE_BASE = [
    "💙 Lamento que estés pasando por un momento difícil. A veces no estar bien también está bien, y hablar de lo que sentimos puede ayudar.",
    "😔 Entiendo cómo te sentís. No estás solo en esto; estoy acá para escucharte si querés contarme más.",
    "🤍 Gracias por confiarme lo que sentís. Recordá que cada emoción es válida, incluso las más duras.",
]

SALUDOS = ["hola", "buenas", "hey", "holaa", "buen día", "buenas tardes", "buenas noches"]


# -------------------------------------------------------------------
# COMANDOS
# -------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensaje inicial con bienvenida aleatoria."""
    message = random.choice(WELCOME_MESSAGES)
    await update.message.reply_text(message)
    context.user_data["active"] = True
    asyncio.create_task(inactivity_timer(update, context))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 *Comandos disponibles:*\n\n"
        "/start - Iniciar conversación\n"
        "/help  - Mostrar ayuda\n\n"
        "Podés enviarme texto, audio o imágenes para analizar 😊",
        parse_mode="Markdown",
    )


# -------------------------------------------------------------------
# MANEJADOR DE TEXTO
# -------------------------------------------------------------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_raw = update.message.text or ""
    text = text_raw.lower().strip()

    # Saludo explícito
    if any(text == s or text.startswith(s + " ") for s in SALUDOS):
        await update.message.reply_text(
            "👋 ¡Hola! Soy Pulsett Bot 🤖, tu compañero emocional. ¿Cómo te sentís hoy?"
        )
        context.user_data["last_emotion"] = "neutral"
        return

    # Análisis de sentimiento
    sent = analyze_sentiment(text_raw)
    tone = sent["label"].lower()
    last_tone = context.user_data.get("last_emotion")

    reply = f"🔍 *Análisis de sentimiento:* {sent['label'].capitalize()}.\n\n"

    if tone == "negativo":
        if any(pal in text for pal in ["solo", "sola", "soledad"]):
            reply += (
                "💙 Sentirse solo puede ser muy duro. Gracias por animarte a decirlo. "
                "No estás solo acá, podemos charlar todo lo que necesites."
            )
        elif last_tone == "positivo":
            reply += (
                "😔 Noto un cambio en tu ánimo. Está bien, todos tenemos altibajos. "
                "Si querés hablar de eso, te escucho 💬."
            )
        else:
            reply += random.choice(NEGATIVE_BASE)

    elif tone == "positivo":
        if last_tone == "negativo":
            reply += (
                "💪 Me alegra mucho ver que te sentís mejor. Es un paso importante hacia adelante, "
                "bien por vos 🙌."
            )
        else:
            reply += random.choice(POSITIVE_BASE)

    else:  # neutral
        auto_reply = (
            auto_responder.predict_response(text_raw)
            if auto_responder is not None
            else None
        )
        if auto_reply:
            reply += auto_reply
        else:
            reply += random.choice(NEUTRAL_BASE)

    context.user_data["last_emotion"] = tone
    await update.message.reply_text(reply, parse_mode="Markdown")


# -------------------------------------------------------------------
# MANEJADOR DE AUDIO
# -------------------------------------------------------------------
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.voice.get_file()
    local_ogg = f"temp_{update.message.message_id}.oga"
    await file.download_to_drive(custom_path=local_ogg)

    await update.message.reply_text(
        "🎧 Estoy escuchando tu mensaje... un momento por favor ⏳"
    )

    # Transcripción (puede fallar silenciosamente si no hay ffmpeg/whisper/etc.)
    text = transcribe_audio(local_ogg)

    if os.path.exists(local_ogg):
        os.remove(local_ogg)

    if not text or not text.strip():
        await update.message.reply_text(
            "😕 No logré entender tu audio. ¿Podrías intentar de nuevo o escribirme cómo te sentís?"
        )
        return

    sent = analyze_sentiment(text)
    tone = sent["label"].lower()
    auto_reply = (
        auto_responder.predict_response(text) if auto_responder is not None else None
    )

    reply = "🧠 *Análisis de tu mensaje de voz:*\n\n"

    if tone == "positivo":
        reply += random.choice(POSITIVE_BASE)
    elif tone == "negativo":
        reply += random.choice(NEGATIVE_BASE)
    else:
        reply += random.choice(NEUTRAL_BASE)

    if auto_reply:
        reply += f"\n\n🗣 {auto_reply}"

    await update.message.reply_text(reply, parse_mode="Markdown")


# -------------------------------------------------------------------
# MANEJADOR DE IMÁGENES
# -------------------------------------------------------------------
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    local_jpg = f"temp_photo_{update.message.message_id}.jpg"
    await file.download_to_drive(custom_path=local_jpg)

    await update.message.reply_text(
        "🖼️ Analizando la imagen... un momento por favor ⚪"
    )

    res = analyze_image(local_jpg)

    if os.path.exists(local_jpg):
        os.remove(local_jpg)

    emotion = res.get("emotion", "unknown").lower()

    reply_map = {
        "happy": "🙂 Parece que hay una emoción positiva en la imagen.",
        "sad": "💙 La imagen transmite tristeza. ¿Querés contarme qué pasó?",
        "angry": "😠 Veo enojo o frustración en la imagen.",
        "surprise": "😮 Algo inesperado parece estar ocurriendo.",
        "fear": "😰 La imagen expresa miedo o ansiedad.",
        "disgust": "🤢 Hay signos de disgusto o incomodidad.",
        "neutral": "😐 La expresión es bastante neutra.",
    }

    reply = (
        f"🖼️ *Análisis de imagen:*\n"
        f"Emoción detectada: *{emotion.capitalize()}*\n\n"
    )
    reply += reply_map.get(
        emotion,
        "🙂 Estoy analizando la imagen, pero no estoy completamente seguro de la emoción.",
    )

    await update.message.reply_text(reply, parse_mode="Markdown")


# -------------------------------------------------------------------
# MENSAJE DE CIERRE AUTOMÁTICO
# -------------------------------------------------------------------
async def inactivity_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(120)
    if context.user_data.get("active", False):
        await update.message.reply_text(
            "💙 Gracias por charlar conmigo. Recordá que tus emociones importan. "
            "Estoy acá cuando necesites hablar 🫂"
        )
        context.user_data["active"] = False


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def main():
    if TELEGRAM_TOKEN is None:
        print(
            "❌ ERROR: Debes exportar TELEGRAM_TOKEN en las variables de entorno "
            "antes de ejecutar el bot."
        )
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
