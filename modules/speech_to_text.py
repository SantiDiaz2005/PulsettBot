# modules/speech_to_text.py
import os
import tempfile
import subprocess
import shutil

# Detectar FFmpeg automáticamente
def find_ffmpeg():
    """Busca FFmpeg en rutas comunes o en PATH."""
    # Rutas comunes en Windows
    common_paths = [
        r"C:\Users\User\Documents\ffmpeg-8.0-essentials_build\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]
    
    # Primero verificar si está en PATH
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return ffmpeg_in_path
    
    # Luego verificar rutas comunes
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None

FFMPEG_PATH = find_ffmpeg()
if not FFMPEG_PATH:
    print("⚠️ ADVERTENCIA: FFmpeg no encontrado. La conversión de audio puede fallar.")

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
    # Verificar que el archivo existe
    if not os.path.exists(file_path):
        print(f"❌ El archivo no existe: {file_path}")
        return ""

    # ----------------------------
    # 1) INTENTO CON WHISPER
    # ----------------------------
    if _WHISPER_AVAILABLE:
        try:
            # Convertir a WAV primero para mejor compatibilidad con Whisper
            wav_path = None
            if file_path.lower().endswith(('.oga', '.ogg', '.opus')):
                if FFMPEG_PATH:
                    wav_path = convert_to_wav(file_path)
                    if wav_path and os.path.exists(wav_path):
                        audio_file = wav_path
                    else:
                        audio_file = file_path  # Fallback al original
                else:
                    audio_file = file_path
            else:
                audio_file = file_path
            
            result = _whisper_model.transcribe(audio_file, fp16=False, language="es")
            text = result.get("text", "").strip()

            # Limpiar archivo temporal si se creó
            if wav_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except:
                    pass

            if text:
                print(f"Whisper → {text}")
                return text

        except Exception as e:
            print("❌ Whisper falló:", e)
            # Limpiar archivo temporal si existe
            if 'wav_path' in locals() and wav_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except:
                    pass

    # ----------------------------
    # 2) INTENTO CON SPEECHRECOGNITION
    # ----------------------------
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        # Convertir a WAV sí o sí (necesario para SpeechRecognition)
        if not FFMPEG_PATH:
            print("❌ FFmpeg no disponible. No se puede convertir el audio.")
            return ""

        wav_path = convert_to_wav(file_path)
        if not wav_path or not os.path.exists(wav_path):
            print("❌ No se pudo convertir a WAV.")
            return ""

        try:
            with sr.AudioFile(wav_path) as source:
                # Ajustar para ruido ambiental
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.record(source)

            text = recognizer.recognize_google(audio, language="es-ES").strip()
            print(f"Google SR → {text}")
            
            # Limpiar archivo temporal
            if os.path.exists(wav_path):
                os.remove(wav_path)
            
            return text

        except sr.UnknownValueError:
            print("❌ Google SR no pudo entender el audio.")
            if os.path.exists(wav_path):
                os.remove(wav_path)
            return ""
        except sr.RequestError as e:
            print(f"❌ Error de servicio de Google SR: {e}")
            if os.path.exists(wav_path):
                os.remove(wav_path)
            return ""
        except Exception as e:
            print(f"❌ Google SR no pudo transcribir: {e}")
            if os.path.exists(wav_path):
                os.remove(wav_path)
            return ""

    except ImportError:
        print("❌ SpeechRecognition no está instalado.")
        return ""
    except Exception as e:
        print(f"❌ Error general en SpeechRecognition: {e}")
        return ""
