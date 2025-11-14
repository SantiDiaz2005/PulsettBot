# modules/speech_to_text.py
import os
import tempfile
import subprocess

# Ruta a tu ffmpeg
# IMPORTANTE: Asegúrate que esta ruta sea correcta en tu PC.
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
    Convierte cualquier formato (usualmente OGG/OPUS de Telegram) a WAV.
    Devuelve ruta temporal .wav o "" si falla.
    """
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        dst = tmp.name

        # Añadido -vn para asegurar solo audio, -ar 16000 para la tasa de muestreo estándar
        cmd = [FFMPEG_PATH, "-y", "-i", src_path, "-vn", "-ar", "16000", "-ac", "1", dst]
        
        # subprocess.run levanta la excepción si check=True
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True) 

        return dst
    except Exception as e:
        print("❌ Error FFmpeg al convertir (Verifica la ruta de FFMPEG_PATH y el archivo):", e)
        # Asegurarse de que el archivo temporal se elimine si falla la conversión
        if os.path.exists(dst):
            os.remove(dst)
        return ""


# ---------------------------------------------------------
# TRANSCRIPCIÓN PRINCIPAL
# ---------------------------------------------------------
def transcribe_audio(file_path: str) -> str:
    """
    Transcribe audios de Telegram usando Whisper o SpeechRecognition.
    Devuelve texto limpio o "" si falla.
    """
    # Siempre convertimos el archivo de entrada de Telegram (OGG) a WAV primero.
    # Esta es la corrección clave para que Whisper y SpeechRecognition funcionen.
    wav_path = convert_to_wav(file_path)
    if not wav_path:
        return ""
    
    # Aseguramos que el archivo original de Telegram se elimine si está en temp
    # Aunque la librería Telegram lo hace, es una buena práctica.
    
    text = ""

    try:
        # ----------------------------
        # 1) INTENTO CON WHISPER
        # ----------------------------
        if _WHISPER_AVAILABLE:
            try:
                # Usamos el archivo WAV convertido
                result = _whisper_model.transcribe(wav_path, fp16=False, language="es")
                text = result.get("text", "").strip()

                if text:
                    print(f"Whisper → {text}")
                    return text
                else:
                    print("⚠️ Whisper no extrajo texto, probando Google SR.")

            except Exception as e:
                print("❌ Whisper falló durante la transcripción:", e)


        # ----------------------------
        # 2) INTENTO CON SPEECHRECOGNITION
        # ----------------------------
        if not text:
            import speech_recognition as sr
            recognizer = sr.Recognizer()

            with sr.AudioFile(wav_path) as source:
                audio = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio, language="es-ES").strip()
                print(f"Google SR → {text}")
                return text

            except Exception as e:
                print("❌ Google SR no pudo transcribir:", e)
                return ""

    except Exception as e:
        print("❌ Error general en la transcripción de audio:", e)
        return ""

    finally:
        # 3) LIMPIEZA: Eliminar el archivo WAV temporal
        if os.path.exists(wav_path):
            os.remove(wav_path)
            
        return text

