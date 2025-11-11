# bot.py
import os
import logging
import random
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from modules.sentiment_analysis import analyze_sentiment
from modules.auto_responses import AutoResponder
from modules.speech_to_text import transcribe_audio
from modules.image_analysis import analyze_image

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Cargar el dataset de respuestas automáticas
auto_responder = AutoResponder("data/responses_dataset.csv")

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
    """Mensaje inicial con bienvenida aleatoria"""
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

# -------------- MANEJADOR DE TEXTO CON MEMORIA EMOCIONAL (mejorado) --------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_raw = update.message.text
    text = text_raw.lower().strip()

    # --- Detección de saludos ---
    SALUDOS = ["hola", "buenas", "hey", "holaa", "buen día", "buenas tardes", "buenas noches"]
    if any(saludo == text or text.startswith(saludo + " ") for saludo in SALUDOS):
        await update.message.reply_text(
            "👋 ¡Hola! Soy Pulsett Bot 🤖, tu compañero emocional. ¿Cómo te sentís hoy?"
        )
        context.user_data["last_emotion"] = "neutral"
        return

    # --- Análisis emocional del texto ---
    sent = analyze_sentiment(text_raw)
    tone = sent["label"].lower()
    last_tone = context.user_data.get("last_emotion", None)

    reply = f"🔍 *Análisis de sentimiento:* {sent['label'].capitalize()}.\n\n"

    # --- Respuesta según tono ---
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

    else:  # tono neutral
        auto_reply = auto_responder.predict_response(text_raw)
        if auto_reply:
            reply += f"{auto_reply}"
        else:
            reply += random.choice(NEUTRAL_BASE)

    # Guardar el estado emocional actual
    context.user_data["last_emotion"] = tone

    await update.message.reply_text(reply, parse_mode="Markdown")

# ---------------- MANEJADOR DE AUDIO ----------------
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa mensajes de voz, analiza el sentimiento y responde emocionalmente."""
    file = await update.message.voice.get_file()
    local_ogg = f"temp_{update.message.message_id}.ogg"
    await file.download_to_drive(custom_path=local_ogg)

    await update.message.reply_text("🎧 Estoy escuchando tu mensaje... un momento por favor ⏳")

    try:
        text = transcribe_audio(local_ogg)
    except Exception as e:
        text = ""
        print("❌ Error al transcribir el audio:", e)
    finally:
        if os.path.exists(local_ogg):
            os.remove(local_ogg)

    if text:
        sent = analyze_sentiment(text)
        tone = sent["label"].lower()
        auto_reply = auto_responder.predict_response(text)

        reply = f"🔊 *Análisis de tu mensaje de voz:*\n"

        if tone == "positivo":
            reply += random.choice([
                "😄 Me alegra escucharte con esa energía positiva. ¡Seguí así!",
                "🌟 Qué bueno escucharte tan bien. Aprovechá este momento para recargar pilas 💪",
                "😁 Transmitís muy buena vibra, me encanta saber que estás así de bien."
            ])
        elif tone == "negativo":
            reply += random.choice([
                "💙 Lamento que estés pasando por un momento difícil. Estoy acá para acompañarte 💬",
                "🤍 Gracias por compartirlo. No estás solo, podemos hablar de eso si querés 🫂",
                "😔 Entiendo cómo te sentís. A veces hablarlo ayuda, contame si querés que te escuche."
            ])
        else:
            reply += random.choice([
                "🙂 Gracias por compartir tu mensaje conmigo.",
                "😌 Te escucho con atención. Contame un poco más si querés.",
                "🧠 Gracias por confiar en mí, a veces hablar ya es un gran paso."
            ])

        if auto_reply:
            reply += f"\n\n{auto_reply}"

        await update.message.reply_text(reply, parse_mode="Markdown")

    else:
        await update.message.reply_text(
            "😕 No pude entender bien tu audio. ¿Podés intentar hablar un poco más cerca del micrófono o escribirme cómo te sentís por texto?"
        )


# -------------- MANEJADOR DE IMÁGENES --------------
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    local_jpg = f"temp_photo_{update.message.message_id}.jpg"
    await file.download_to_drive(custom_path=local_jpg)
    await update.message.reply_text("🧐 Analizando la imagen... un momento por favor 🕓")

    try:
        res = analyze_image(local_jpg)
    except Exception:
        res = None
    finally:
        if os.path.exists(local_jpg):
            os.remove(local_jpg)

    if res:
        scene = res.get("scene_label", "Desconocido")
        faces = res.get("faces", 0)
        brightness = res.get("brightness", "N/A")

        reply = f"🖼️ *Análisis de imagen:*\nEscenario detectado: *{scene}*\nCaras detectadas: *{faces}*\nBrillo promedio: *{brightness}*\n\n"

        if faces > 0 and "happy" in scene.lower():
            reply += "😊 Parece una imagen alegre y con buena energía. ¡Me encanta ver momentos felices como este!"
        elif "dark" in scene.lower() or brightness == "bajo":
            reply += "🌙 La imagen tiene tonos oscuros, quizás transmite calma o introspección. ¿Te gustaría contarme qué te inspiró a tomarla?"
        elif faces == 0 and "outdoor" in scene.lower():
            reply += "🌄 Qué linda vista. Las fotos de exteriores siempre traen un aire de libertad y conexión con uno mismo."
        else:
            reply += "📷 Interesante captura. Cada imagen tiene una historia detrás, y esta parece tener mucho para decir."

    else:
        reply = (
            "😕 No pude analizar la imagen correctamente. "
            "Podés intentar enviarla nuevamente o contarme qué representa para vos 📸."
        )

    await update.message.reply_text(reply, parse_mode="Markdown")

# -------------- MENSAJE DE CIERRE AUTOMÁTICO --------------
async def inactivity_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(120)
    if context.user_data.get("active", False):
        await update.message.reply_text(
            "💙 Gracias por charlar conmigo. Recordá que tus emociones importan. Estoy acá cuando necesites hablar 🫂"
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
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("✅ Pulsett Bot iniciado. Presioná Ctrl+C para detener.")
    app.run_polling()

if __name__ == "__main__":
    main()
