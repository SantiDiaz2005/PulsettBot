# modules/auto_responses.py
import pandas as pd
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import os

class AutoResponder:
    def __init__(self, csv_path="data/responses_dataset.csv"):
        self.csv_path = csv_path
        self.df = None
        self.vectorizer = TfidfVectorizer()
        self.model = LogisticRegression()
        self.intents = {}
        if os.path.exists(csv_path):
            self._load_and_train()

    def _load_and_train(self):
        self.df = pd.read_csv(self.csv_path)
        X, y = [], []

        # Permitir varias frases y varias respuestas por intención
        for _, row in self.df.iterrows():
            patterns = str(row["patterns"]).split(";")
            responses = str(row["response"]).split("|")  # separador de posibles respuestas
            self.intents[row["intent"]] = responses
            for p in patterns:
                X.append(p.strip().lower())
                y.append(row["intent"])

        X_vec = self.vectorizer.fit_transform(X)
        self.model.fit(X_vec, y)

    def predict_response(self, text: str) -> str:
        if self.df is None:
            return ""
        x = self.vectorizer.transform([text.lower()])
        intent = self.model.predict(x)[0]
        responses = self.intents.get(intent, [])
        if responses:
            return random.choice(responses).strip()  # elige una aleatoria
        else:
            return ""
