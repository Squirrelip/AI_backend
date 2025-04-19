# llm_agent/utils/embedding.py

from sentence_transformers import SentenceTransformer
from llm_agent import config
import numpy as np

class EmbeddingModel:
    def __init__(self, model_name: str = config.EMBEDDING_MODEL):
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str]) -> list[np.ndarray]:
        return self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)