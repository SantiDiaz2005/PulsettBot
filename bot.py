# bot.py
import os
import logging
import random
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from modules.sentiment_analysis import analyze_sentiment
from modules.auto_responses import get_autoresponder
from modules.speech_to_text import transcribe_audio
from modules.image_analysis import analyze_image

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Cargar el dataset de respuestas automáticas
auto_responder = get_autoresponder("data/responses_dataset.csv")

# -------------- MENSAJES BASE --------------
WELCOME_MESSAGES = [
    "👋 ¡Hola! Soy Pulsett Bot 🤖. Estoy acá para acompañarte, ¿cómo te sentís hoy?",
    "🌈 ¡Bienvenido! Soy Pulsett Bot. Podemos charlar sobre lo que necesites 💬",
    "💙 ¡Hola! Me alegra verte por acá. Contame, ¿cómo va tu día?",
    "🤗 ¡Hola! Soy tu compañero emocional digital. Estoy acá para escucharte."
]

NEUTRAL_BASE = [
    "🙂 Gracias por compartir cómo te sentís. A veces no tenerlo del todo claro también está bien.",
    "🧠 Entiendo, y aprecio que lo compartas conmigo. Si querés charlar un poco más, estoy acá.",
    "😌 Gracias por contarme eso. Poner en palabras lo que sentimos ya es un gran paso."
]

POSITIVE_BASE = [
    "🌟 Qué alegría leerte así. Me encanta saber que estás bien, seguí aprovechando ese estado de ánimo para recargar energía 💪.",
    "😄 Me pone muy contento ver tu buena energía. Disfrutá este momento y hacé algo que te haga sonreír.",
    "✨ Me encanta leer eso. Cada día con una sonrisa es una victoria, seguí así 💙."
]

NEGATIVE_BASE = [
    "💙 Lamento que estés pasando por un momento difícil. A veces no estar bien también está bien, y hablar de lo que sentimos puede ayudar.",
    "😔 Entiendo cómo te sentís. No estás solo en esto; estoy acá para escucharte si querés contarme más.",
    "🤍 Gracias por confiarme lo que sentís. Recordá que cada emoción es válida, incluso las más duras."
]

# -------------- COMANDOS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = random.choice(WELCOME_MESSAGES)
    await update.message.reply_text(message)
    context.user_data["active"] = True
    asyncio.create_task(inactivity_timer(update, context))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 *Comandos disponibles:*\n\n"
        "/start - Iniciar conversación\n/help - Mostrar ayuda\n\n"
        "Podés enviarme texto, audio o imágenes para analizar 😊",
        parse_mode="Markdown"
    )

# -------------- MANEJADOR TEXTO --------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_raw = update.message.text
    text = text_raw.lower().strip()

    SALUDOS = ["hola", "buenas", "hey", "holaa", "buen día", "buenas tardes", "buenas noches"]
    if any(text.startswith(s) for s in SALUDOS):
        await update.message.reply_text(
            "👋 ¡Hola! Soy Pulsett Bot 🤖, tu compañero emocional. ¿Cómo te sentís hoy?"
        )
        context.user_data["last_emotion"] = "neutral"
        return

    sent = analyze_sentiment(text_raw)
    tone = sent["label"].lower()
    last_tone = context.user_data.get("last_emotion", None)

    reply = f"🔍 *Análisis de sentimiento:* {sent['label'].capitalize()}.\n\n"

    if tone == "negativo":
        if any(p in text for p in ["solo", "sola", "soledad"]):
            reply += "💙 Sentirse solo puede ser muy duro. Gracias por contarlo. Estoy acá para vos."
        elif last_tone == "positivo":
            reply += "😔 Veo un cambio en tu ánimo. Está bien tener altibajos. ¿Querés hablar sobre eso?"
        else:
            reply += random.choice(NEGATIVE_BASE)

    elif tone == "positivo":
        if last_tone == "negativo":
            reply += "💪 Qué bueno ver que estás mejor. Me alegra mucho por vos 🙌."
        else:
            reply += random.choice(POSITIVE_BASE)

    else:
        auto_reply = auto_responder.predict_response(text_raw) if auto_responder else None
        if auto_reply:
            reply += auto_reply
        else:
            reply += random.choice(NEUTRAL_BASE)

    context.user_data["last_emotion"] = tone
    await update.message.reply_text(reply, parse_mode="Markdown")

# -------------- MANEJADOR AUDIO --------------
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Manejar tanto voice como audio
        if update.message.voice:
            file = await update.message.voice.get_file()
            file_extension = ".oga"
        elif update.message.audio:
            file = await update.message.audio.get_file()
            # Detectar extensión del archivo de audio
            file_name = update.message.audio.file_name or "audio"
            if file_name.endswith(('.mp3', '.m4a', '.wav')):
                file_extension = os.path.splitext(file_name)[1]
            else:
                file_extension = ".oga"
        else:
            await update.message.reply_text("❌ No se pudo procesar el mensaje de audio.")
            return

        local_audio = f"temp_{update.message.message_id}{file_extension}"
        
        try:
            await file.download_to_drive(custom_path=local_audio)
        except Exception as e:
            logger.error(f"Error al descargar audio: {e}")
            await update.message.reply_text("❌ Error al descargar tu audio. Por favor, intentá nuevamente.")
            return

        if not os.path.exists(local_audio):
            await update.message.reply_text("❌ Error al descargar tu audio.")
            return

        await update.message.reply_text("🎧 Estoy escuchando tu mensaje... un momento por favor ⏳")

        text = transcribe_audio(local_audio)

        # Limpiar archivo temporal
        if os.path.exists(local_audio):
            try:
                os.remove(local_audio)
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal: {e}")

        if not text or not text.strip():
            await update.message.reply_text("😕 No logré entender tu audio. ¿Podés repetirlo o escribir cómo te sentís?")
            return

        sent = analyze_sentiment(text)
        tone = sent["label"].lower()

        reply = f"🧠 **Análisis de tu mensaje de voz:**\n\n"
        reply += f"📝 *Transcripción:* {text}\n\n"

        if tone == "positivo":
            reply += random.choice(POSITIVE_BASE)
        elif tone == "negativo":
            reply += random.choice(NEGATIVE_BASE)
        else:
            reply += random.choice(NEUTRAL_BASE)

        auto_reply = auto_responder.predict_response(text) if auto_responder else None
        if auto_reply and auto_reply != "ERROR_DATASET_VACIO":
            reply += f"\n\n🗣 {auto_reply}"

        await update.message.reply_text(reply, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error en voice_handler: {e}")
        await update.message.reply_text("❌ Ocurrió un error al procesar tu audio. Por favor, intentá nuevamente.")

# -------------- MANEJADOR IMÁGENES --------------
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    local_jpg = f"temp_photo_{update.message.message_id}.jpg"
    await file.download_to_drive(custom_path=local_jpg)

    await update.message.reply_text("🖼️ Analizando la imagen... un momento por favor ⚪")

    res = analyze_image(local_jpg)

    os.remove(local_jpg)

    emotion = res.get("emotion", "unknown").lower()

    reply_map = {
        "happy": "🙂 Hay una emoción positiva en la imagen.",
        "sad": "💙 Veo tristeza en la imagen. ¿Querés contarme qué pasó?",
        "angry": "😠 La imagen muestra enojo.",
        "surprise": "😮 Parece que algo inesperado sucedió.",
        "fear": "😰 Noto miedo o ansiedad.",
        "disgust": "🤢 Detecto signos de disgusto.",
        "neutral": "😐 La expresión es neutra."
    }

    reply = f"🖼️ *Análisis de imagen:*\nEmoción detectada: **{emotion.capitalize()}**\n\n"
    reply += reply_map.get(emotion, "🙂 No estoy seguro de la emoción en la imagen.")

    await update.message.reply_text(reply, parse_mode="Markdown")

# -------------- INACTIVIDAD --------------
async def inactivity_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(120)
    if context.user_data.get("active", False):
        await update.message.reply_text(
            "💙 Gracias por charlar conmigo. Estoy acá cuando necesites hablar 🫂"
        )
        context.user_data["active"] = False

# -------------- MAIN --------------
def main():
    if TELEGRAM_TOKEN is None:
        print("❌ ERROR: Debes exportar TELEGRAM_TOKEN en las variables de entorno.")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    # Capturar tanto mensajes de voz como archivos de audio
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, voice_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("✅ Pulsett Bot iniciado. Presioná Ctrl+C para detener.")
    app.run_polling()

if __name__ == "__main__":
    main()