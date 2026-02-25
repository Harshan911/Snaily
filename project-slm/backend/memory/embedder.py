"""
Embedder — Local sentence embeddings using Sentence Transformers.
Runs on CPU. ~90 MB model. No GPU needed.
Falls back to simple bag-of-words if sentence-transformers unavailable.
"""

from typing import List
import hashlib
import logging

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except Exception:
    HAS_ST = False

# all-MiniLM-L6-v2: 90 MB, fast on CPU, good quality for RAG
DEFAULT_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # MiniLM output dimension


class Embedder:
    """Generates embeddings locally for memory storage and retrieval."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self._model = None
        self._use_st = HAS_ST

    def _load_model(self):
        """Lazy load — only loads when first embedding is requested."""
        if self._use_st and not self._model:
            try:
                logger.info(f"Loading embedding model: {self.model_name} ...")
                print(f"   Loading embedding model: {self.model_name} ...")
                self._model = SentenceTransformer(self.model_name)
                logger.info("Embedding model loaded ✓")
                print(f"   Embedding model loaded ✓")
            except Exception as e:
                logger.warning(f"Embedding model failed ({e}), using fallback")
                print(f"   ⚠️ Embedding model failed ({e}), using fallback")
                self._use_st = False

    def embed(self, text: str) -> List[float]:
        """Embed a single text string → vector."""
        if not text or not text.strip():
            return [0.0] * EMBEDDING_DIM

        self._load_model()

        if self._use_st and self._model:
            embedding = self._model.encode(text, normalize_embeddings=True)
            return embedding.tolist()

        # Fallback: simple hash-based pseudo-embedding (384 dims to match MiniLM)
        return self._fallback_embed(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts → list of vectors."""
        self._load_model()

        if self._use_st and self._model:
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()

        return [self._fallback_embed(t) for t in texts]

    def _fallback_embed(self, text: str) -> List[float]:
        """
        Deterministic pseudo-embedding using iterative hashing.
        Produces exactly EMBEDDING_DIM (384) floats.
        NOTE: This is NOT a real embedding — just a placeholder that allows
        the system to run without sentence-transformers installed.
        """
        if not text or not text.strip():
            return [0.0] * EMBEDDING_DIM

        result = []
        seed = text.lower().encode("utf-8")
        counter = 0
        while len(result) < EMBEDDING_DIM:
            data = seed + counter.to_bytes(4, "big")
            h = hashlib.sha256(data).digest()
            for b in h:
                if len(result) >= EMBEDDING_DIM:
                    break
                result.append((b - 128) / 128.0)
            counter += 1
        return result[:EMBEDDING_DIM]
