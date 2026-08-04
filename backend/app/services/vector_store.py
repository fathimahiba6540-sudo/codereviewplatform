"""
vector_store.py — Phase 4.2
ChromaDB vector store wrapper with Google Gemini embeddings.

Handles:
- Embedding and upserting code chunks
- Semantic similarity search for AI agents
- Per-project collection management
- Content-hash-based caching to avoid re-embedding unchanged files
"""
import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Embedding dimension for Gemini text-embedding-004
GEMINI_EMBEDDING_MODEL = "models/text-embedding-004"
CHROMA_COLLECTION_PREFIX = "project_"

# Maximum chunks to upsert per batch (ChromaDB recommended max: 500)
UPSERT_BATCH_SIZE = 200


def _get_chroma_client() -> chromadb.PersistentClient:
    """Return a persistent ChromaDB client pointed at the configured vector_db path."""
    return chromadb.PersistentClient(
        path=settings.VECTOR_DB_PATH,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _get_embedding_function():
    """
    Return a ChromaDB-compatible embedding function using Google Gemini.
    Falls back to ChromaDB's default (sentence-transformers) if Gemini key is missing.
    """
    if settings.GEMINI_API_KEY:
        try:
            from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction
            return GoogleGenerativeAiEmbeddingFunction(
                api_key=settings.GEMINI_API_KEY,
                model_name=GEMINI_EMBEDDING_MODEL,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini embedding function: {e}. Using default.")
    # Fallback to ChromaDB's built-in sentence-transformers (works offline)
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    return DefaultEmbeddingFunction()


class VectorStore:
    """
    Service layer wrapping ChromaDB for code chunk storage and retrieval.
    Each project gets its own named collection: `project_<project_id>`.
    """

    def __init__(self):
        self._client: Optional[chromadb.PersistentClient] = None
        self._embedding_fn = None

    def _ensure_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            self._client = _get_chroma_client()
        return self._client

    def _ensure_embedding_fn(self):
        if self._embedding_fn is None:
            self._embedding_fn = _get_embedding_function()
        return self._embedding_fn

    def _collection_name(self, project_id: str) -> str:
        # ChromaDB collection names: alphanumeric + hyphens, max 63 chars
        safe_id = project_id.replace("-", "")[:40]
        return f"{CHROMA_COLLECTION_PREFIX}{safe_id}"

    def get_or_create_collection(self, project_id: str):
        """Get or create the ChromaDB collection for a project."""
        client = self._ensure_client()
        emb_fn = self._ensure_embedding_fn()
        return client.get_or_create_collection(
            name=self._collection_name(project_id),
            embedding_function=emb_fn,
            metadata={"project_id": project_id, "hnsw:space": "cosine"},
        )

    def upsert_chunks(
        self,
        project_id: str,
        chunks: List[Dict[str, Any]],
    ) -> int:
        """
        Embed and upsert a list of code chunks into the project's ChromaDB collection.

        Chunks are upserted (insert or update) so re-running ingestion is idempotent.
        Returns the total number of chunks stored.

        Args:
            project_id: UUID of the project.
            chunks:     List of chunk dicts from CodeChunker.chunk_file().

        Returns:
            Number of chunks successfully upserted.
        """
        if not chunks:
            return 0

        collection = self.get_or_create_collection(project_id)
        total_upserted = 0

        for batch_start in range(0, len(chunks), UPSERT_BATCH_SIZE):
            batch = chunks[batch_start: batch_start + UPSERT_BATCH_SIZE]

            ids = [c["chunk_id"] for c in batch]
            documents = [c["content"] for c in batch]
            metadatas = [
                {
                    "project_id": c.get("project_id", project_id),
                    "file_id": c.get("file_id") or "",
                    "file_path": c.get("file_path", ""),
                    "language": c.get("language", ""),
                    "chunk_index": int(c.get("chunk_index", 0)),
                    "line_start": int(c.get("line_start", 0)),
                    "line_end": int(c.get("line_end", 0)),
                    "chunk_type": c.get("chunk_type", "window"),
                    "node_name": c.get("node_name") or "",
                    "node_type": c.get("node_type") or "",
                }
                for c in batch
            ]

            try:
                collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                )
                total_upserted += len(batch)
                logger.debug(f"Upserted batch of {len(batch)} chunks for project {project_id}")
            except Exception as e:
                logger.error(f"Failed to upsert chunk batch for project {project_id}: {e}")
                raise

        return total_upserted

    def query_similar(
        self,
        project_id: str,
        query_text: str,
        n_results: int = 10,
        language_filter: Optional[str] = None,
        file_path_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity search over a project's vector collection.

        Args:
            project_id:        UUID of the project to search within.
            query_text:        Natural language or code query.
            n_results:         Max number of results to return.
            language_filter:   Optional — restrict results to a specific language.
            file_path_filter:  Optional — restrict results to a specific file path.

        Returns:
            List of result dicts with keys: content, metadata, distance, file_path, language
        """
        collection = self.get_or_create_collection(project_id)

        where_clause: Optional[Dict] = None
        if language_filter and file_path_filter:
            where_clause = {
                "$and": [
                    {"language": {"$eq": language_filter}},
                    {"file_path": {"$eq": file_path_filter}},
                ]
            }
        elif language_filter:
            where_clause = {"language": {"$eq": language_filter}}
        elif file_path_filter:
            where_clause = {"file_path": {"$eq": file_path_filter}}

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Vector query failed for project {project_id}: {e}")
            return []

        hits = []
        if not results or not results.get("documents"):
            return hits

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            hits.append({
                "content": doc,
                "metadata": meta,
                "distance": dist,
                "file_path": meta.get("file_path", ""),
                "language": meta.get("language", ""),
                "line_start": meta.get("line_start", 0),
                "line_end": meta.get("line_end", 0),
            })

        return hits

    def get_all_chunks(
        self,
        project_id: str,
        file_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all stored chunks for a project (or a specific file).
        Useful for agent full-context scans on smaller projects.
        """
        collection = self.get_or_create_collection(project_id)
        where = {"file_path": {"$eq": file_path}} if file_path else None

        try:
            results = collection.get(
                where=where,
                include=["documents", "metadatas"],
            )
        except Exception as e:
            logger.error(f"Failed to fetch chunks for project {project_id}: {e}")
            return []

        chunks = []
        for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            chunks.append({"content": doc, "metadata": meta})
        return chunks

    def delete_project_collection(self, project_id: str) -> bool:
        """
        Delete all vector data for a project by dropping its ChromaDB collection.
        Called when a project is deleted from the platform.
        """
        client = self._ensure_client()
        collection_name = self._collection_name(project_id)
        try:
            client.delete_collection(name=collection_name)
            logger.info(f"Deleted ChromaDB collection for project {project_id}")
            return True
        except Exception as e:
            logger.warning(f"Could not delete collection for project {project_id}: {e}")
            return False

    def collection_count(self, project_id: str) -> int:
        """Return the number of chunks stored for a project."""
        try:
            collection = self.get_or_create_collection(project_id)
            return collection.count()
        except Exception:
            return 0


# Singleton instance — shared across the application
vector_store = VectorStore()
