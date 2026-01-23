"""RAG (Retrieval Augmented Generation) service with TypeSense and Ollama."""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

import requests
import typesense
from redis import Redis

from backend.config import settings
from backend.services.document_parser import DocumentChunk


logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG pipeline: embeddings, indexing, and retrieval."""

    def __init__(self):
        """Initialize TypeSense client, Ollama client, and Redis cache."""
        # TypeSense client
        self.typesense_client = typesense.Client({
            'nodes': [{
                'host': settings.TYPESENSE_HOST,
                'port': settings.TYPESENSE_PORT,
                'protocol': settings.TYPESENSE_PROTOCOL,
            }],
            'api_key': settings.TYPESENSE_API_KEY,
            'connection_timeout_seconds': 5,
        })

        # Redis cache for embeddings
        self.redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=False)

        # Ollama API base URL
        self.ollama_base_url = settings.OLLAMA_HOST

        # Collection name
        self.collection_name = "document_chunks"

        # Ensure collection exists (non-blocking)
        try:
            self._ensure_collection_exists()
        except Exception as e:
            logger.warning(f"TypeSense not available, RAG functionality will be limited: {e}")
            logger.warning("To enable RAG, please start TypeSense service")

    def _ensure_collection_exists(self) -> None:
        """Create TypeSense collection if it doesn't exist."""
        try:
            # Try to get collection
            self.typesense_client.collections[self.collection_name].retrieve()
            logger.info(f"TypeSense collection already exists: {self.collection_name}")
        except typesense.exceptions.ObjectNotFound:
            # Create collection with schema
            schema = {
                'name': self.collection_name,
                'fields': [
                    {'name': 'chunk_id', 'type': 'string'},
                    {'name': 'user_id', 'type': 'string', 'facet': True},
                    {'name': 'file_id', 'type': 'string', 'facet': True},
                    {'name': 'content', 'type': 'string'},
                    {'name': 'embedding', 'type': 'float[]', 'num_dim': 768},  # nomic-embed-text
                    {'name': 'metadata', 'type': 'string'},  # JSON string
                    {'name': 'document_expires_at', 'type': 'int64'},  # Unix timestamp for TTL
                ],
                'default_sorting_field': 'document_expires_at',
            }

            self.typesense_client.collections.create(schema)
            logger.info(f"Created TypeSense collection: {self.collection_name}")

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using Ollama.

        Args:
            text: Text to embed

        Returns:
            768-dimensional embedding vector, or None if error
        """
        # Check cache first (SHA256 hash of content)
        cache_key = f"embedding:{hashlib.sha256(text.encode()).hexdigest()}"

        cached = self.redis_client.get(cache_key)
        if cached:
            logger.debug("Embedding cache hit")
            return json.loads(cached)

        try:
            # Call Ollama embeddings API
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={
                    "model": settings.OLLAMA_EMBEDDING_MODEL,
                    "prompt": text,
                },
                timeout=30,
            )

            response.raise_for_status()
            data = response.json()

            embedding = data.get('embedding')

            if not embedding:
                logger.error("No embedding in Ollama response")
                return None

            # Cache embedding for 24h
            self.redis_client.setex(cache_key, 86400, json.dumps(embedding))

            logger.debug(f"Generated embedding: {len(embedding)} dimensions")
            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts (batched).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []

        # Process in smaller batches to avoid timeout
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            for text in batch:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)

            logger.info(f"Generated embeddings for batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")

        return embeddings

    def index_chunks(
        self,
        chunks: List[DocumentChunk],
        user_id: str,
        file_id: str,
    ) -> bool:
        """
        Index document chunks in TypeSense with embeddings.

        Args:
            chunks: Parsed document chunks
            user_id: User ID for RLS
            file_id: File ID

        Returns:
            True if indexing successful
        """
        try:
            # Generate embeddings for all chunks
            texts = [chunk.content for chunk in chunks]
            embeddings = self.generate_embeddings_batch(texts)

            # Prepare documents for indexing
            documents = []
            expires_at = int((datetime.utcnow() + timedelta(hours=24)).timestamp())

            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                if not embedding:
                    logger.warning(f"Skipping chunk {idx} due to missing embedding")
                    continue

                doc = {
                    'chunk_id': f"{file_id}_{idx}",
                    'user_id': user_id,
                    'file_id': file_id,
                    'content': chunk.content,
                    'embedding': embedding,
                    'metadata': json.dumps(chunk.metadata),  # Store as JSON string
                    'document_expires_at': expires_at,
                }

                documents.append(doc)

            # Batch import to TypeSense
            if documents:
                result = self.typesense_client.collections[self.collection_name].documents.import_(
                    documents,
                    {'action': 'create'}
                )

                logger.info(f"Indexed {len(documents)} chunks for file {file_id}")
                return True
            else:
                logger.warning("No documents to index (all embeddings failed)")
                return False

        except Exception as e:
            logger.error(f"Error indexing chunks: {e}")
            return False

    def hybrid_search(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        file_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (keyword + semantic) in TypeSense.

        Args:
            query: User query
            user_id: User ID for RLS filtering
            top_k: Number of results to return
            file_id: Optional file ID to restrict search

        Returns:
            List of search results with content and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)

            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            # Build search parameters
            search_params = {
                'q': query,
                'query_by': 'content',
                'vector_query': f'embedding:([{",".join(map(str, query_embedding))}], k:{top_k * 2})',
                'filter_by': f'user_id:={user_id}',
                'per_page': top_k,
                'sort_by': '_text_match:desc,_vector_distance:asc',  # Hybrid: 30% keyword, 70% vector
            }

            # Add file filter if specified
            if file_id:
                search_params['filter_by'] += f' && file_id:={file_id}'

            # Execute search
            results = self.typesense_client.collections[self.collection_name].documents.search(search_params)

            # Format results
            formatted_results = []

            for hit in results.get('hits', []):
                doc = hit['document']
                formatted_results.append({
                    'content': doc['content'],
                    'metadata': json.loads(doc['metadata']),
                    'score': hit.get('text_match_info', {}).get('score', 0),
                    'vector_distance': hit.get('vector_distance', 0),
                })

            logger.info(f"Hybrid search returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Error performing hybrid search: {e}")
            return []

    def build_rag_context(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Build RAG context string from search results for LLM prompt.

        Args:
            search_results: Results from hybrid_search

        Returns:
            Formatted context string with citations
        """
        if not search_results:
            return "Aucune information pertinente n'a été trouvée dans vos documents."

        context_parts = ["Voici les informations pertinentes de vos documents:\n"]

        for idx, result in enumerate(search_results, start=1):
            metadata = result['metadata']
            content = result['content']

            # Format source citation based on file type
            file_type = metadata.get('file_type', '')
            filename = metadata.get('filename', 'unknown')

            if file_type == 'excel':
                source = f"[Source {idx}: {filename}, feuille '{metadata.get('sheet_name')}', cellule {metadata.get('cell_ref')}]"
            elif file_type == 'pdf':
                source = f"[Source {idx}: {filename}, page {metadata.get('page')}]"
            elif file_type == 'word':
                source = f"[Source {idx}: {filename}, paragraphe {metadata.get('paragraph_index')}]"
            elif file_type == 'powerpoint':
                source = f"[Source {idx}: {filename}, slide {metadata.get('slide_number')}]"
            elif file_type == 'csv':
                source = f"[Source {idx}: {filename}, ligne {metadata.get('row_number')}]"
            else:
                source = f"[Source {idx}: {filename}]"

            context_parts.append(f"\n{source}\nContenu: {content}\n")

        return "\n".join(context_parts)

    def delete_file_chunks(self, file_id: str) -> bool:
        """
        Delete all chunks for a file from TypeSense.

        Args:
            file_id: File ID

        Returns:
            True if deletion successful
        """
        try:
            # Delete all documents with matching file_id
            self.typesense_client.collections[self.collection_name].documents.delete({
                'filter_by': f'file_id:={file_id}'
            })

            logger.info(f"Deleted chunks for file: {file_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file chunks: {e}")
            return False


# Singleton instance
rag_service = RAGService()
