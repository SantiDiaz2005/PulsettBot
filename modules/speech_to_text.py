# modules/speech_to_text.py
import os
import tempfile
import subprocess

# ffmpeg: se busca en el PATH del sistema o se puede indicar con la variable de entorno FFMPEG_PATH
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")

# -------------------------
# INTENTO 1: Whisper local
# -------------------------
_WHISPER_AVAILABLE = False
try:
    import whisper  # si no está instalado, se va al except
    _whisper_model = whisper.load_model("small")
    print("🎧 Whisper activado: modelo 'small' cargado para transcripción.")
    _WHISPER_AVAILABLE = True
except Exception as e:
    print("⚠️ Whisper no disponible, se intentará usar SpeechRecognition. Detalle:", e)
    _WHISPER_AVAILABLE = False


def convert_ogg_to_wav(src_path: str, dst_path: str) -> str:
    """Convierte audio OGG/OPUS a WAV usando ffmpeg."""
    try:
        cmd = [FFMPEG_PATH, "-y", "-i", src_path, dst_path]
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return dst_path
    except Exception as e:
        print("❌ Error usando ffmpeg:", e)
        return ""


def transcribe_audio(file_path: str) -> str:
    """
    Recibe el archivo de audio (ogg, opus, mp3, wav...) y devuelve texto transcripto.
    Usa Whisper si está disponible; si no, usa SpeechRecognition (Google API).
    Si nada funciona, devuelve "".
    """

    # ------ INTENTO 1: Whisper ------
    if _WHISPER_AVAILABLE:
        try:
            result = _whisper_model.transcribe(file_path, fp16=False)
            text = result.get("text", "").strip()
            if text:
                return text
        except Exception as e:
            print("❌ Error Whisper:", e)

    # ------ INTENTO 2: SpeechRecognition ------
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        # Si el archivo no es WAV, convierto temporalmente
        if not file_path.lower().endswith(".wav"):
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            wav_path = tmp.name
            tmp.close()
            wav_path = convert_ogg_to_wav(file_path, wav_path)
            if not wav_path:
                # conversión falló
                return ""
        else:
            wav_path = file_path

        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language="es-ES")

        # limpiar archivo temporal
        if wav_path != file_path and os.path.exists(wav_path):
            os.remove(wav_path)

        return text.strip()

    except Exception as e:
        print("❌ Error SpeechRecognition:", e)
        return ""
