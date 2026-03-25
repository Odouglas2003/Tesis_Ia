from typing import Dict
import numpy as np
from sentence_transformers import SentenceTransformer


class IntentDetector:
    def __init__(self):
        self.model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
        self.intents = {
            "team_formation": [
                "Necesito formar un equipo de desarrollo",
                "Quiero armar un equipo para un proyecto",
                "Busco programadores para un trabajo",
            ],
            "technical_question": [
                "Qué tecnologías recomiendas para este proyecto",
                "Cuál es el mejor stack para esta aplicación",
                "Qué habilidades son necesarias",
            ],
            "general_inquiry": [
                "Cómo funciona este sistema",
                "Qué puedes hacer",
                "Explícame las funcionalidades",
            ],
        }
        self._prepare_intent_embeddings()

    def _prepare_intent_embeddings(self):
        """Precalcula embeddings para las intenciones conocidas"""
        self.intent_embeddings = {}
        for intent, examples in self.intents.items():
            embeddings = self.model.encode(examples)
            self.intent_embeddings[intent] = np.mean(embeddings, axis=0)

    def detect_intent(self, text: str) -> Dict[str, float]:
        """
        Detecta la intención del texto de entrada

        Args:
            text: Texto del usuario

        Returns:
            Diccionario con intenciones y sus scores de confianza
        """
        query_embedding = self.model.encode([text])[0]
        scores = {}

        for intent, intent_embedding in self.intent_embeddings.items():
            # Similitud coseno
            score = np.dot(query_embedding, intent_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(intent_embedding)
            )
            scores[intent] = float(score)

        return scores
