from __future__ import annotations
from functools import lru_cache
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 384-dim, fast

@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME, device="cpu")  # force CPU for portability

def embed_texts(texts: List[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    m = _model()
    # normalize embeddings for cosine sim via dot product
    embs = m.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return embs.astype("float32")
