# modules/speech_to_text.py
import os
import tempfile
import subprocess

# Ruta a tu ffmpeg
FFMPEG_PATH = r"C:\Users\User\Documents\ffmpeg-8.0-essentials_build\bin\ffmpeg.exe"

# ---------------------------------------------------------
# INTENTO 1: Whisper local
# ---------------------------------------------------------
_WHISPER_AVAILABLE = False
try:
    import whisper
    _whisper_model = whisper.load_model("small")
    print("🎧 Whisper activado correctamente.")
    _WHISPER_AVAILABLE = True
except Exception as e:
    print("⚠️ Whisper no disponible. Usaré SpeechRecognition:", e)
    _WHISPER_AVAILABLE = False


# ---------------------------------------------------------
# FFmpeg – Conversión OGG/OPUS → WAV
# ---------------------------------------------------------
def convert_to_wav(src_path: str) -> str:
    """
    Convierte cualquier formato a WAV usando ffmpeg.
    Devuelve ruta temporal .wav o "" si falla.
    """
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        dst = tmp.name

        cmd = [FFMPEG_PATH, "-y", "-i", src_path, "-ar", "16000", "-ac", "1", dst]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        return dst
    except Exception as e:
        print("❌ Error FFmpeg al convertir:", e)
        return ""


# ---------------------------------------------------------
# TRANSCRIPCIÓN PRINCIPAL
# ---------------------------------------------------------
def transcribe_audio(file_path: str) -> str:
    """
    Transcribe audios de Telegram usando Whisper o SpeechRecognition.
    Devuelve texto limpio o "" si falla.
    """

    # ----------------------------
    # 1) INTENTO CON WHISPER
    # ----------------------------
    if _WHISPER_AVAILABLE:
        try:
            result = _whisper_model.transcribe(file_path, fp16=False)
            text = result.get("text", "").strip()

            if text:
                print(f"Whisper → {text}")
                return text

        except Exception as e:
            print("❌ Whisper falló:", e)

    # ----------------------------
    # 2) INTENTO CON SPEECHRECOGNITION
    # ----------------------------
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        # Convertir a WAV sí o sí
        wav_path = convert_to_wav(file_path)
        if not wav_path:
            print("❌ No se pudo convertir a WAV.")
            return ""

        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)

        try:
            text = recognizer.recognize_google(audio, language="es-ES").strip()
            print(f"Google SR → {text}")
            os.remove(wav_path)
            return text

        except Exception as e:
            print("❌ Google SR no pudo transcribir:", e)
            os.remove(wav_path)
            return ""

    except Exception as e:
        print("❌ Error general en SpeechRecognition:", e)
        return ""

