from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

try:
    import faiss  # type: ignore
except Exception:
    faiss = None

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.empty((0, 384), dtype="float32")

    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return embeddings.astype("float32")


def build_faiss_index(embeddings: np.ndarray):
    if faiss is None:
        return None

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index