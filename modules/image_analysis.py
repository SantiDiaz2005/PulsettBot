from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch

# Modelo de emociones disponible públicamente
MODEL_NAME = "dima806/facial_emotions_image_detection"

processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)

def analyze_image(image_path):
    image = Image.open(image_path).convert("RGB")

    # Preprocesar imagen
    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        predicted_class_id = logits.argmax(-1).item()

    # Obtener emoción
    emotion = model.config.id2label[predicted_class_id]

    return {
        "emotion": emotion
    }
