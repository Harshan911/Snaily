"""
Memory Store — Persistent cross-chat memory.
Uses ChromaDB when available, falls back to in-memory store.
"""

from typing import List, Dict, Optional
from pathlib import Path
import uuid
import json
import os

MEMORY_DIR = Path(__file__).parent / "data"

# Try importing ChromaDB — may fail on Python 3.14+
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    HAS_CHROMADB = True
except Exception:
    HAS_CHROMADB = False


class MemoryStore:
    """
    Persistent vector memory.
    Uses ChromaDB + local embeddings when available.
    Falls back to simple JSON file store with keyword matching.
    """

    def __init__(self, embedder, persist_dir: Path = None):
        self.embedder = embedder
        self.persist_dir = persist_dir or MEMORY_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._collection = None
        self._fallback_store = []  # list of {id, content, metadata}
        self._fallback_file = self.persist_dir / "memory_fallback.json"
        self._use_chromadb = HAS_CHROMADB

    async def initialize(self):
        """Initialize ChromaDB client and collection, or load fallback."""
        if self._use_chromadb:
            try:
                self._client = chromadb.PersistentClient(
                    path=str(self.persist_dir),
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                self._collection = self._client.get_or_create_collection(
                    name="blue_dragon_memory",
                    metadata={"hnsw:space": "cosine"},
                )
                print(f"   Memory initialized (ChromaDB): {self._collection.count()} entries")
                return
            except Exception as e:
                print(f"   ⚠️ ChromaDB failed ({e}), falling back to JSON store")
                self._use_chromadb = False

        # Fallback: load from JSON
        if self._fallback_file.exists():
            try:
                self._fallback_store = json.loads(self._fallback_file.read_text(encoding="utf-8"))
            except Exception:
                self._fallback_store = []
        print(f"   Memory initialized (JSON fallback): {len(self._fallback_store)} entries")

    def _save_fallback(self):
        """Persist fallback store to disk."""
        try:
            self._fallback_file.write_text(
                json.dumps(self._fallback_store, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

    async def add(self, content: str, metadata: dict = None):
        """Add a conversation turn to memory."""
        doc_id = str(uuid.uuid4())
        meta = metadata or {}
        meta["length"] = len(content)

        if self._use_chromadb and self._collection:
            try:
                embedding = self.embedder.embed(content)
                self._collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[meta],
                )
                return
            except Exception:
                pass

        # Fallback
        self._fallback_store.append({
            "id": doc_id,
            "content": content,
            "metadata": meta,
        })
        # Keep max 500 entries
        if len(self._fallback_store) > 500:
            self._fallback_store = self._fallback_store[-500:]
        self._save_fallback()

    async def query(self, query: str, top_k: int = 5) -> List[Dict]:
        """Query memory for semantically similar past context."""
        if self._use_chromadb and self._collection and self._collection.count() > 0:
            try:
                query_embedding = self.embedder.embed(query)
                results = self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, self._collection.count()),
                )

                formatted = []
                if results and results["documents"]:
                    for i, doc in enumerate(results["documents"][0]):
                        score = 1 - results["distances"][0][i] if results["distances"] else 0
                        formatted.append({
                            "content": doc,
                            "score": round(score, 3),
                            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        })
                return formatted
            except Exception:
                pass

        # Fallback: simple keyword matching
        if not self._fallback_store:
            return []

        query_words = set(query.lower().split())
        scored = []
        for entry in self._fallback_store:
            content_words = set(entry["content"].lower().split())
            overlap = len(query_words & content_words)
            if overlap > 0:
                score = overlap / max(len(query_words), 1)
                scored.append({
                    "content": entry["content"],
                    "score": round(min(score, 1.0), 3),
                    "metadata": entry.get("metadata", {}),
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    async def count(self) -> int:
        """Get total number of memory entries."""
        if self._use_chromadb and self._collection:
            try:
                return self._collection.count()
            except Exception:
                pass
        return len(self._fallback_store)

    async def size_mb(self) -> float:
        """Estimate memory store size on disk."""
        total = 0
        for f in self.persist_dir.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return round(total / (1024 * 1024), 2)

    async def clear(self):
        """Clear all memory entries."""
        if self._use_chromadb and self._client:
            try:
                self._client.delete_collection("blue_dragon_memory")
                self._collection = self._client.get_or_create_collection(
                    name="blue_dragon_memory",
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception:
                pass

        # Clear fallback too
        self._fallback_store = []
        self._save_fallback()
