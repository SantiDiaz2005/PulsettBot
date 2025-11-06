# bot.py
import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from modules.sentiment_analysis import analyze_sentiment
from modules.auto_responses import get_autoresponder
from modules.speech_to_text import transcribe_audio
from modules.image_analysis import analyze_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # setear en el entorno o .env

autoresponder = get_autoresponder("data/responses_dataset.csv")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola! Soy Pulsett Bot 🤖. Envíame un mensaje, voz o foto y te acompaño.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Comandos:\n/start - iniciar\n/help - ayuda\nPodés enviar texto, mensajes de voz o fotos.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # 1) análisis de sentimiento
    sent = analyze_sentiment(text)
    # 2) respuesta automática por dataset
    auto = autoresponder.predict_response(text)
    reply = f"Análisis de sentimiento: {sent['label']} (polarity={sent['polarity']})\n"
    if auto:
        reply += f"\n{auto}"
    else:
        reply += (
            "\nNo tengo una respuesta exacta para eso todavía, "
            "pero estoy acá para leerte. ¿Querés contarme un poco más?" 
            )
    await update.message.reply_text(reply)

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # El archivo de voz se baja y transcribe
    file = await update.message.voice.get_file()
    local_ogg = f"temp_{update.message.message_id}.ogg"
    await file.download_to_drive(custom_path=local_ogg)
    await update.message.reply_text("Transcribiendo tu audio...")
    try:
        text = transcribe_audio(local_ogg)
    except Exception as e:
        text = ""
    if os.path.exists(local_ogg):
        os.remove(local_ogg)

    if text:
        sent = analyze_sentiment(text)
        auto = autoresponder.predict_response(text)
        reply = f"Transcripción: {text}\nAnálisis: {sent['label']} (polarity={sent['polarity']})\n"
        if auto:
            reply += f"\n{auto}"
    else:
        reply = (
            "No pude entender bien tu audio 😕. "
            "¿Podés intentar hablar un poco más cerca del micrófono "
            "o mandarme lo que sentís por texto?"
        )
    await update.message.reply_text(reply)

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    local_jpg = f"temp_photo_{update.message.message_id}.jpg"
    await file.download_to_drive(custom_path=local_jpg)
    res = analyze_image(local_jpg)
    if os.path.exists(local_jpg):
        os.remove(local_jpg)
    reply = f"Análisis de imagen: {res['scene_label']}. Faces detectadas: {res['faces']}. Brillo: {res['brightness']}."
    await update.message.reply_text(reply)

def main():
    if TELEGRAM_TOKEN is None:
        print("ERROR: Debes exportar TELEGRAM_TOKEN en las variables de entorno.")
        return
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot iniciado. Presioná Ctrl+C para detener.")
    app.run_polling()

if __name__ == "__main__":
    main()

