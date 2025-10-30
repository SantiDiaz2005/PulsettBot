# modules/auto_responses.py
import pandas as pd
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
        # Expand patterns (they can be separated by ';')
        X = []
        y = []
        for _, row in self.df.iterrows():
            patterns = str(row["patterns"]).split(";")
            for p in patterns:
                X.append(p.strip().lower())
                y.append(row["intent"])
            self.intents[row["intent"]] = row["response"]
        X_vec = self.vectorizer.fit_transform(X)
        self.model.fit(X_vec, y)

    def predict_response(self, text: str) -> str:
        if self.df is None:
            return ""
        x = self.vectorizer.transform([text.lower()])
        intent = self.model.predict(x)[0]
        return self.intents.get(intent, "")

# helper factory
_autoresponder = None
def get_autoresponder(csv_path="data/responses_dataset.csv"):
    global _autoresponder
    if _autoresponder is None:
        _autoresponder = AutoResponder(csv_path)
    return _autoresponder
