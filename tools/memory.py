from __future__ import annotations
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import uuid
import os


class VectorMemory:
    """
    Memoria vettoriale persistente in ChromaDB.
    Ogni item ha: id, testo, metadati (tipo, url, topic, timestamp, ecc).
    """
    def __init__(
        self,
        path: str = "./memory_store",
        collection: str = os.getenv("DEFAULT_COLLECTION", ""),
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        os.makedirs(path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=path)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        self.collection = self.client.get_or_create_collection(
            name=collection,
            embedding_function=self.embedding_fn
        )

    def upsert(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        if metadatas is None:
            metadatas = [{} for _ in texts]

        self.collection.upsert(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        return ids

    def query(
        self,
        query_text: str,
        top_k: int = 8,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        res = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where
        )
        # Normalizzazione output
        matches = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        ids = res.get("ids", [[]])[0]
        dists = res.get("distances", [[]])[0] or res.get("embeddings", [[]])[0]
        for i, doc in enumerate(docs):
            matches.append({
                "id": ids[i],
                "text": doc,
                "metadata": metas[i],
                "score": (1 - dists[i]) if isinstance(dists[i], (int, float)) and 0 <= dists[i] <= 1 else None
            })
        return matches