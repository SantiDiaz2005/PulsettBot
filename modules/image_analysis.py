# modules/image_analysis.py
import cv2
import numpy as np
import os

# Intent: detectar brillo general y si hay cara (Haar cascade)
_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def analyze_image(image_path: str) -> dict:
    """
    Devuelve: dict con 'faces' (n), 'brightness' (0..255), 'scene_label' (str simple)
    """
    img = cv2.imread(image_path)
    if img is None:
        return {"faces": 0, "brightness": 0.0, "scene_label": "unknown"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = _cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30,30))
    faces_count = len(faces)

    # brillo promedio
    brightness = float(np.mean(gray))

    # heurística simple:
    if faces_count > 0 and brightness > 90:
        scene = "probable_happy_or_social"
    elif faces_count > 0 and brightness <= 90:
        scene = "faces_but_dim_light"
    elif brightness < 70:
        scene = "dark_or_sad"
    else:
        scene = "neutral_or_outdoor"

    return {"faces": faces_count, "brightness": round(brightness,2), "scene_label": scene}
