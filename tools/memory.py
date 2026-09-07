from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions


def _build_chroma_client(path: str) -> chromadb.ClientAPI:
	"""Return an HttpClient when CHROMA_HOST is set, otherwise a PersistentClient."""
	host = os.getenv("CHROMA_HOST", "").strip()
	if host:
		port = int(os.getenv("CHROMA_PORT", "8000"))
		ssl = os.getenv("CHROMA_SSL", "false").lower() in ("1", "true", "yes")
		return chromadb.HttpClient(host=host, port=port, ssl=ssl)
	os.makedirs(path, exist_ok=True)
	return chromadb.PersistentClient(path=path)


class VectorMemory:
	"""Persistent vector memory backed by ChromaDB."""

	def __init__(
		self,
		path: str = os.getenv("CHROMA_PERSIST_PATH", "./memory_store"),
		collection: str = os.getenv("CHROMA_COLLECTION", "research-cache"),
		embedding_model: str = os.getenv(
			"CHROMA_EMBEDDING_MODEL",
			"sentence-transformers/all-MiniLM-L6-v2",
		),
	):
		self.client = _build_chroma_client(path)
		self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
			model_name=embedding_model
		)
		self.collection = self.client.get_or_create_collection(
			name=collection,
			embedding_function=self.embedding_fn,
		)

	def upsert(
		self,
		texts: List[str],
		metadatas: Optional[List[Dict[str, Any]]] = None,
		ids: Optional[List[str]] = None,
	) -> List[str]:
		if ids is None:
			ids = [str(uuid.uuid4()) for _ in texts]
		if metadatas is None:
			metadatas = [{} for _ in texts]

		self.collection.upsert(documents=texts, metadatas=metadatas, ids=ids)
		return ids

	def query(
		self,
		query_text: str,
		top_k: int = 8,
		where: Optional[Dict[str, Any]] = None,
	) -> List[Dict[str, Any]]:
		result = self.collection.query(
			query_texts=[query_text],
			n_results=top_k,
			where=where,
		)

		matches = []
		documents = result.get("documents", [[]])[0] if result else []
		metadatas = result.get("metadatas", [[]])[0] if result else []
		ids = result.get("ids", [[]])[0] if result else []
		distances = result.get("distances", [[]])[0] if result else []

		for index, document in enumerate(documents):
			distance = distances[index] if index < len(distances) else None
			matches.append(
				{
					"id": ids[index] if index < len(ids) else "",
					"text": document,
					"metadata": metadatas[index] if index < len(metadatas) else {},
					"score": 1 - distance if isinstance(distance, (int, float)) else None,
				}
			)
		return matches
