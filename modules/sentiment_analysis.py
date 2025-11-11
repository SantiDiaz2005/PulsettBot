# modules/sentiment_analysis.py
from textblob import TextBlob

# --- Listas simples de palabras clave en español ---
POSITIVE_WORDS = [
    "feliz", "alegre", "contento", "contenta", "bien", "motivado", "motivada",
    "tranquilo", "tranquila", "animado", "animada", "entusiasmado", "entusiasmada",
    "agradecido", "agradecida", "optimista", "positivo", "satisfecho", "satisfecha",
    "genial", "excelente", "perfecto", "maravilloso", "increíble"
]

NEGATIVE_WORDS = [
    "triste", "mal", "deprimido", "deprimida", "angustiado", "angustiada",
    "ansioso", "ansiosa", "estresado", "estresada", "cansado", "cansada",
    "nervioso", "nerviosa", "solo", "sola", "soledad", "miedo", "asustado",
    "asustada", "preocupado", "preocupada", "enojado", "enojada", "frustrado",
    "frustrada", "abrumado", "abrumada", "tristeza", "pena", "dolor",
    "murió", "murio", "falleció", "fallecio", "perdí", "perdi", "pérdida",
    "perdida", "duelo"
]


def analyze_sentiment(text: str) -> dict:
    """
    Analiza el sentimiento de un texto en español.
    Retorna un dict con:
      - label: 'positivo', 'negativo' o 'neutral'
      - polarity: número entre -1 y 1
    """
    text_low = text.lower()
    score = 0

    # --- Evaluación manual por palabras clave ---
    for word in POSITIVE_WORDS:
        if word in text_low:
            score += 1

    for word in NEGATIVE_WORDS:
        if word in text_low:
            score -= 1

    # --- Si detecta emociones, usa ese resultado ---
    if score != 0:
        polarity = max(-1.0, min(1.0, score / 3))
        label = "positivo" if score > 0 else "negativo"
        return {"label": label, "polarity": polarity}

    # --- Si no detecta nada, usa TextBlob como respaldo ---
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
    except Exception:
        polarity = 0.0

    if polarity > 0.1:
        label = "positivo"
    elif polarity < -0.1:
        label = "negativo"
    else:
        label = "neutral"

    return {"label": label, "polarity": polarity}
