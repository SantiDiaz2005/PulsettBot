import os
import subprocess
import tempfile

# Intentar usar Whisper si está disponible
try:
    import whisper
    _WHISPER_AVAILABLE = True
    _whisper_model = whisper.load_model("small")
    print("✅ Whisper activo: usando modelo 'small' para transcripción.")
except Exception as e:
    _WHISPER_AVAILABLE = False
    print("⚠️ Whisper no disponible, se usará SpeechRecognition como alternativa.", e)


def convert_ogg_to_wav(src_path, dst_path):
    """
    Convierte un archivo OGG/OPUS a WAV usando ffmpeg.
    """
    cmd = ["ffmpeg", "-y", "-i", src_path, dst_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def transcribe_audio(file_path: str) -> str:
    """
    Recibe la ruta de un archivo de audio (ogg, oga, webm, mp3, wav),
    lo convierte si es necesario y devuelve el texto transcripto.
    """

    # Si Whisper está disponible
    if _WHISPER_AVAILABLE:
        try:
            # Convertir si el formato no es compatible directamente
            if file_path.endswith((".ogg", ".oga", ".webm")):
                tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
                convert_ogg_to_wav(file_path, tmp_wav)
                file_path = tmp_wav

            print(f"🎧 Transcribiendo con Whisper: {file_path}")
            result = _whisper_model.transcribe(file_path, language="es")
            text = result.get("text", "").strip()

            if not text:
                print("⚠️ Whisper no pudo extraer texto.")
            else:
                print(f"🗣️ Texto detectado: {text}")

            return text

        except Exception as e:
            print("❌ Error en Whisper:", e)
            return ""

    # Si Whisper no está disponible, usar SpeechRecognition (fallback)
    else:
        import speech_recognition as sr
        r = sr.Recognizer()

        wav_path = file_path
        if file_path.endswith((".ogg", ".oga", ".webm")):
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            wav_path = tmp.name
            convert_ogg_to_wav(file_path, wav_path)

        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
        try:
            text = r.recognize_google(audio, language="es-ES")
            print(f"🗣️ Texto detectado (Google): {text}")
        except Exception as e:
            print("❌ Error en SpeechRecognition:", e)
            text = ""

        if wav_path != file_path and os.path.exists(wav_path):
            os.remove(wav_path)

        return text
