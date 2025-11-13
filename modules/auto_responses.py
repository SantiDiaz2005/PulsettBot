# modules/auto_responses.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from typing import Optional

# 1. Importaciones y definición de stop words de NLTK
try:
    import nltk
    from nltk.corpus import stopwords
    SPANISH_STOP_WORDS = stopwords.words('spanish')
except ImportError:
    # Fallback si NLTK no está instalado
    SPANISH_STOP_WORDS = None
    print("ADVERTENCIA: nltk no está instalado. No se filtrarán stop words en español.")


class AutoResponder:
    def __init__(self, responses_df: pd.DataFrame):
        # ⚠️ IMPORTANTE: Validar que el DataFrame no esté vacío ⚠️
        if responses_df.empty or 'text_sample' not in responses_df.columns:
            
            # Inicialización de componentes si el DataFrame está vacío o falta la columna
            # ✅ CORRECCIÓN FINAL: Usar la lista de variables de NLTK
            self.vectorizer = TfidfVectorizer(stop_words=SPANISH_STOP_WORDS)
            
            self.responses = pd.DataFrame({'text_sample': [''], 'response': ['Error de carga']})
            self.nn = NearestNeighbors(n_neighbors=1)
            
            self.X = self.vectorizer.fit_transform(self.responses['text_sample'])
            self.nn.fit(self.X)
            print("ADVERTENCIA: AutoResponder inicializado con datos vacíos o erróneos.")
            return

        # ✅ CORRECCIÓN FINAL: Usar la lista de variables de NLTK para el entrenamiento normal
        self.vectorizer = TfidfVectorizer(stop_words=SPANISH_STOP_WORDS)
        
        self.responses = responses_df
        
        # ✅ AQUÍ ES DONDE SE ACCEDE A LA COLUMNA 'text_sample'
        self.X = self.vectorizer.fit_transform(responses_df['text_sample'])
        
        self.nn = NearestNeighbors(n_neighbors=1)
        self.nn.fit(self.X)

    def predict_response(self, text: str) -> Optional[str]:
        # Si el modelo se inicializó con datos vacíos, siempre retorna None
        if self.responses.empty or self.X.shape[0] <= 1: 
            return "ERROR_DATASET_VACIO"
            
        text_vector = self.vectorizer.transform([text])
        distances, indices = self.nn.kneighbors(text_vector)
        
        if distances[0][0] < 0.8:  # Umbral de similitud
            # Asegurarse de que el índice exista antes de acceder a iloc
            if indices[0][0] < len(self.responses):
                return self.responses.iloc[indices[0][0]]['response']
        
        return None

def get_autoresponder(dataset_path: str) -> Optional[AutoResponder]:
    """
    Carga el dataset de respuestas y crea un AutoResponder.
    """
    try:
        responses_df = pd.read_csv(dataset_path)
        
        # Asegurarse de que el DataFrame no esté vacío ANTES de pasarlo a la clase
        if responses_df.empty:
            print("ERROR: El archivo CSV se cargó, pero está vacío.")
            return None 

        # Si el CSV usa 'input' en lugar de 'text_sample', renómbrala
        if 'input' in responses_df.columns:
           responses_df.rename(columns={'input': 'text_sample'}, inplace=True)

        return AutoResponder(responses_df)
    
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de dataset en la ruta: {dataset_path}")
        return None
    except Exception as e:
        print(f"Error grave al cargar el dataset de respuestas: {e}")
        # Devuelve None para que bot.py sepa que la funcionalidad está inactiva
        return None