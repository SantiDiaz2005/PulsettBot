# bot.py
import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from modules.sentiment_analysis import analyze_sentiment
from modules.auto_responses import AutoResponder
from modules.speech_to_text import transcribe_audio
from modules.image_analysis import analyze_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token de Telegram (desde .env o variable de entorno)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Instancia del auto-responder
auto_responder = AutoResponder("data/responses_dataset.csv")

# ---------------- COMANDOS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! Soy Pulsett Bot 🤖. Envíame un mensaje, una nota de voz o una foto y te acompaño.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 *Comandos disponibles:*\n\n/start - Iniciar conversación\n/help - Mostrar ayuda\n\nPodés enviarme texto, audio o imágenes para analizar 😊", parse_mode="Markdown")

# ---------------- MANEJADORES DE TEXTO ----------------

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # 1️⃣ Análisis de sentimiento
    sent = analyze_sentiment(text)

    # 2️⃣ Respuesta automática por dataset
    auto_reply = auto_responder.predict_response(text)

    # 3️⃣ Composición del mensaje
    reply = f"🔍 *Análisis de sentimiento:* {sent['label']} (polarity={sent['polarity']:.2f})\n\n"
    if auto_reply:
        reply += f"{auto_reply}"
    else:
        reply += "🤔 No tengo una respuesta exacta para eso todavía, pero estoy acá para escucharte 💬"

    await update.message.reply_text(reply, parse_mode="Markdown")

# ---------------- MANEJADORES DE VOZ ----------------

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.voice.get_file()
    local_ogg = f"temp_{update.message.message_id}.ogg"
    await file.download_to_drive(custom_path=local_ogg)
    await update.message.reply_text("🎙️ Transcribiendo tu audio...")

    try:
        text = transcribe_audio(local_ogg)
    except Exception as e:
        text = ""
    finally:
        if os.path.exists(local_ogg):
            os.remove(local_ogg)

    if text:
        sent = analyze_sentiment(text)
        auto_reply = auto_responder.predict_response(text)
        reply = f"🗣️ *Transcripción:* {text}\n\n🔍 *Análisis:* {sent['label']} (polarity={sent['polarity']:.2f})\n"
        if auto_reply:
            reply += f"\n{auto_reply}"
    else:
        reply = "😕 No pude entender bien tu audio. ¿Podés intentar hablar un poco más cerca del micrófono o escribirme por texto?"

    await update.message.reply_text(reply, parse_mode="Markdown")

# ---------------- MANEJADORES DE IMÁGENES ----------------

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    local_jpg = f"temp_photo_{update.message.message_id}.jpg"
    await file.download_to_drive(custom_path=local_jpg)

    res = analyze_image(local_jpg)
    if os.path.exists(local_jpg):
        os.remove(local_jpg)

    reply = f"🖼️ *Análisis de imagen:*\nEscenario detectado: {res['scene_label']}\nCaras: {res['faces']}\nBrillo: {res['brightness']}"
    await update.message.reply_text(reply, parse_mode="Markdown")

# ---------------- MAIN ----------------

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
