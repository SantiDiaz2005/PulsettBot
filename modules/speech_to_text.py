import os
import subprocess
import tempfile
import pathlib # Para manejo de rutas

# Intentar usar Whisper si está disponible
try:
    import whisper
    _WHISPER_AVAILABLE = True
    # Se recomienda usar 'base' o 'small' para mejor velocidad en bots
    _whisper_model = whisper.load_model("small")
    print("✅ Whisper activo: usando modelo 'small' para transcripción.")
except Exception as e:
    _WHISPER_AVAILABLE = False
    print(f"⚠️ Whisper no disponible, se usará SpeechRecognition como alternativa. Error: {e}")


def convert_ogg_to_wav(src_path: str, dst_path: str):
    """
    Convierte un archivo OGG/OPUS a WAV usando ffmpeg.
    Levanta una excepción si ffmpeg falla.
    """
    # ⚠️ Usar rutas absolutas para asegurar que FFmpeg las encuentre ⚠️
    src_abs = os.path.abspath(src_path)
    dst_abs = os.path.abspath(dst_path)
    
    cmd = ["ffmpeg", "-y", "-i", src_abs, dst_abs]
    
    # Capturar la salida de error de FFmpeg para un diagnóstico claro
    result = subprocess.run(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        check=False # No lanzar excepción automáticamente, la manejamos abajo
    )
    
    if result.returncode != 0:
        error_output = result.stderr.decode('utf-8')
        raise RuntimeError(f"FFmpeg falló (Code {result.returncode}): Asegúrate de que FFmpeg está en el PATH y funcional. Error detallado: {error_output}")


def transcribe_audio(file_path: str) -> str:
    """
    Recibe la ruta de un archivo de audio, lo convierte si es necesario 
    y devuelve el texto transcripto.
    """
    text = ""
    temp_files = [] # Lista para rastrear archivos temporales a eliminar
    
    # Normalizar la ruta del archivo de entrada
    input_file_abs = os.path.abspath(file_path)

    try:
        # --- 1. PROCESAMIENTO CON WHISPER (PREFERIDO) ---
        if _WHISPER_AVAILABLE:
            final_path_to_transcribe = input_file_abs
            
            # Conversión de formato si es necesario
            if final_path_to_transcribe.endswith((".ogg", ".oga", ".webm")):
                tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
                temp_files.append(tmp_wav) # Añadir a la lista de eliminación
                
                print(f"🔄 Convirtiendo a WAV para Whisper: {final_path_to_transcribe}")
                convert_ogg_to_wav(final_path_to_transcribe, tmp_wav)
                final_path_to_transcribe = tmp_wav

            print(f"🎧 Transcribiendo con Whisper: {pathlib.Path(final_path_to_transcribe).name}")
            result = _whisper_model.transcribe(final_path_to_transcribe, language="es")
            text = result.get("text", "").strip()

            if not text:
                print("⚠️ Whisper no pudo extraer texto, intentando SpeechRecognition.")
            else:
                print(f"🗣️ Texto detectado (Whisper): {text}")
                return text # Éxito, devuelve el texto
        
        # --- 2. FALLBACK CON SPEECHRECOGNITION (GOOGLE) ---
        if not text:
            import speech_recognition as sr
            r = sr.Recognizer()

            wav_path = input_file_abs
            
            # Conversión de formato si es necesario para AudioFile
            if wav_path.endswith((".ogg", ".oga", ".webm")):
                tmp_fallback_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
                temp_files.append(tmp_fallback_wav)
                
                print(f"🔄 Convirtiendo a WAV para SpeechRecognition: {wav_path}")
                convert_ogg_to_wav(wav_path, tmp_fallback_wav)
                wav_path = tmp_fallback_wav

            # SpeechRecognition solo funciona con archivos WAV (o formatos compatibles)
            with sr.AudioFile(wav_path) as source:
                audio = r.record(source)
                
            try:
                print("🧠 Transcribiendo con Google Speech Recognition...")
                text = r.recognize_google(audio, language="es-ES")
                print(f"🗣️ Texto detectado (Google): {text}")
            except Exception as e:
                print(f"❌ Error en SpeechRecognition (Google): {e}. Audio no reconocido.")
                text = ""

    except Exception as e:
        print(f"❌ Error general en la transcripción de audio: {e}")
        text = ""

    finally:
        # --- 3. LIMPIEZA DE ARCHIVOS TEMPORALES ---
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)
                
    return text