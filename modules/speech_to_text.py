# modules/speech_to_text.py
import os
import subprocess
import tempfile

# Try to use whisper if available, otherwise fallback to SpeechRecognition+Google
try:
    import whisper
    _WHISPER_AVAILABLE = True
    _whisper_model = whisper.load_model("small")
except Exception:
    _WHISPER_AVAILABLE = False

def convert_ogg_to_wav(src_path, dst_path):
    # usa ffmpeg (pydub alternative)
    cmd = ["ffmpeg", "-y", "-i", src_path, dst_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def transcribe_audio(file_path: str) -> str:
    """
    Recibe ruta a archivo de audio (ogg/oga/ogg opus, mp3, wav...), convierte si hace falta
    y devuelve texto transcrito.
    """
    if _WHISPER_AVAILABLE:
        result = _whisper_model.transcribe(file_path)
        return result.get("text", "").strip()
    else:
        # fallback simple: try SpeechRecognition (online Google API)
        import speech_recognition as sr
        wav_path = file_path
        if file_path.endswith(".oga") or file_path.endswith(".ogg") or file_path.endswith(".webm"):
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            wav_path = tmp.name
            convert_ogg_to_wav(file_path, wav_path)
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
        try:
            text = r.recognize_google(audio, language="es-ES")
        except Exception as e:
            text = ""
        # cleanup
        if wav_path != file_path and os.path.exists(wav_path):
            os.remove(wav_path)
        return text
