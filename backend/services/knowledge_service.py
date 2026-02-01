"""Knowledge base service for permanent system knowledge."""

import hashlib
import json
import logging
import uuid
from typing import List, Dict, Any, Optional

import typesense

from backend.config import settings
from backend.services.rag_service import rag_service


logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service for managing permanent knowledge base (no TTL)."""

    def __init__(self):
        """Initialize TypeSense client for knowledge base."""
        self.typesense_client = typesense.Client({
            'nodes': [{
                'host': settings.TYPESENSE_HOST,
                'port': settings.TYPESENSE_PORT,
                'protocol': settings.TYPESENSE_PROTOCOL,
            }],
            'api_key': settings.TYPESENSE_API_KEY,
            'connection_timeout_seconds': 5,
        })

        # Separate collection for permanent knowledge
        self.collection_name = "knowledge_base"

        # Ensure collection exists
        try:
            self._ensure_collection_exists()
        except Exception as e:
            logger.warning(f"TypeSense not available for knowledge base: {e}")

    def _ensure_collection_exists(self) -> None:
        """Create TypeSense collection for knowledge base if it doesn't exist."""
        try:
            # Try to get collection
            self.typesense_client.collections[self.collection_name].retrieve()
            logger.info(f"Knowledge base collection already exists: {self.collection_name}")
        except typesense.exceptions.ObjectNotFound:
            # Create collection with schema
            schema = {
                'name': self.collection_name,
                'fields': [
                    {'name': 'knowledge_id', 'type': 'string'},
                    {'name': 'category', 'type': 'string', 'facet': True},  # e.g., "supply_chain", "logistics"
                    {'name': 'subcategory', 'type': 'string', 'facet': True, 'optional': True},
                    {'name': 'title', 'type': 'string'},  # Knowledge title/topic
                    {'name': 'content', 'type': 'string'},
                    {'name': 'embedding', 'type': 'float[]', 'num_dim': 768},  # nomic-embed-text
                    {'name': 'metadata', 'type': 'string'},  # JSON string for additional info
                    {'name': 'tags', 'type': 'string[]', 'optional': True},  # Optional tags for filtering
                    {'name': 'created_at', 'type': 'int64'},  # Unix timestamp
                ],
                'default_sorting_field': 'created_at',
            }

            self.typesense_client.collections.create(schema)
            logger.info(f"Created knowledge base collection: {self.collection_name}")

    def add_knowledge(
        self,
        content: str,
        category: str,
        title: str,
        subcategory: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Add a single knowledge chunk to the knowledge base.

        Args:
            content: The knowledge content/text
            category: Main category (e.g., "supply_chain", "logistics", "inventory")
            title: Title/topic of this knowledge
            subcategory: Optional subcategory
            metadata: Optional additional metadata
            tags: Optional tags for filtering

        Returns:
            True if successfully added
        """
        try:
            # Generate embedding for content
            embedding = rag_service.generate_embedding(content)

            if not embedding:
                logger.error("Failed to generate embedding for knowledge")
                return False

            # Prepare document
            import time
            knowledge_id = str(uuid.uuid4())

            doc = {
                'knowledge_id': knowledge_id,
                'category': category,
                'title': title,
                'content': content,
                'embedding': embedding,
                'metadata': json.dumps(metadata or {}),
                'created_at': int(time.time()),
            }

            # Add optional fields
            if subcategory:
                doc['subcategory'] = subcategory
            if tags:
                doc['tags'] = tags

            # Add to TypeSense
            self.typesense_client.collections[self.collection_name].documents.create(doc)

            logger.info(f"Added knowledge: {title} (category: {category})")
            return True

        except Exception as e:
            logger.error(f"Error adding knowledge: {e}")
            return False

    def add_knowledge_batch(
        self,
        knowledge_items: List[Dict[str, Any]]
    ) -> int:
        """
        Add multiple knowledge chunks in batch.

        Args:
            knowledge_items: List of dicts with keys: content, category, title, subcategory, metadata, tags

        Returns:
            Number of successfully added items
        """
        documents = []
        import time

        for item in knowledge_items:
            content = item.get('content')
            if not content:
                logger.warning("Skipping knowledge item with no content")
                continue

            # Generate embedding
            embedding = rag_service.generate_embedding(content)
            if not embedding:
                logger.warning(f"Failed to generate embedding for: {item.get('title', 'untitled')}")
                continue

            # Prepare document
            knowledge_id = str(uuid.uuid4())
            doc = {
                'knowledge_id': knowledge_id,
                'category': item.get('category', 'general'),
                'title': item.get('title', 'Untitled'),
                'content': content,
                'embedding': embedding,
                'metadata': json.dumps(item.get('metadata', {})),
                'created_at': int(time.time()),
            }

            # Add optional fields
            if 'subcategory' in item and item['subcategory']:
                doc['subcategory'] = item['subcategory']
            if 'tags' in item and item['tags']:
                doc['tags'] = item['tags']

            documents.append(doc)

        # Batch import to TypeSense
        if documents:
            try:
                self.typesense_client.collections[self.collection_name].documents.import_(
                    documents,
                    {'action': 'create'}
                )
                logger.info(f"Added {len(documents)} knowledge items in batch")
                return len(documents)
            except Exception as e:
                logger.error(f"Error in batch knowledge import: {e}")
                return 0
        else:
            logger.warning("No valid knowledge items to add")
            return 0

    def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        query_embedding: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base with hybrid search.

        Args:
            query: Search query
            top_k: Number of results to return
            category: Optional category filter
            tags: Optional tag filters
            query_embedding: Optional pre-computed query embedding (for performance)

        Returns:
            List of search results with content and metadata
        """
        try:
            # Use provided embedding or generate new one
            if query_embedding is None:
                query_embedding = rag_service.generate_embedding(query)

            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            # Build search parameters using multi_search for large embeddings
            search_request = {
                'searches': [{
                    'collection': self.collection_name,
                    'q': query,
                    'query_by': 'content,title',
                    'vector_query': f'embedding:([{",".join(map(str, query_embedding))}], k:{top_k * 2})',
                    'per_page': top_k,
                    'sort_by': '_text_match:desc,_vector_distance:asc',
                }]
            }

            # Add filters
            filters = []
            if category:
                filters.append(f'category:={category}')
            if tags:
                tag_filters = ' && '.join([f'tags:={tag}' for tag in tags])
                filters.append(tag_filters)

            if filters:
                search_request['searches'][0]['filter_by'] = ' && '.join(filters)

            # Execute multi_search
            multi_results = self.typesense_client.multi_search.perform(search_request, {})
            results = multi_results['results'][0] if multi_results.get('results') else {'hits': []}

            # Format results
            formatted_results = []

            for hit in results.get('hits', []):
                doc = hit['document']
                formatted_results.append({
                    'content': doc['content'],
                    'title': doc['title'],
                    'category': doc['category'],
                    'subcategory': doc.get('subcategory'),
                    'metadata': json.loads(doc.get('metadata', '{}')),
                    'tags': doc.get('tags', []),
                    'score': hit.get('text_match_info', {}).get('score', 0),
                    'vector_distance': hit.get('vector_distance', 0),
                })

            logger.info(f"Knowledge search returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []

    def build_knowledge_context(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Build context string from knowledge base search results.

        Args:
            search_results: Results from search_knowledge

        Returns:
            Formatted context string
        """
        if not search_results:
            return ""

        context_parts = ["Voici des connaissances pertinentes de la base de connaissances:\n"]

        for idx, result in enumerate(search_results, start=1):
            title = result['title']
            category = result.get('category', 'général')
            content = result['content']

            source = f"[Connaissance {idx}: {title} (Catégorie: {category})]"
            context_parts.append(f"\n{source}\n{content}\n")

        return "\n".join(context_parts)

    def delete_knowledge(self, knowledge_id: str) -> bool:
        """
        Delete a knowledge item by ID.

        Args:
            knowledge_id: Knowledge ID

        Returns:
            True if deletion successful
        """
        try:
            self.typesense_client.collections[self.collection_name].documents[knowledge_id].delete()
            logger.info(f"Deleted knowledge: {knowledge_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting knowledge: {e}")
            return False

    def delete_by_category(self, category: str) -> bool:
        """
        Delete all knowledge items in a category.

        Args:
            category: Category name

        Returns:
            True if deletion successful
        """
        try:
            self.typesense_client.collections[self.collection_name].documents.delete({
                'filter_by': f'category:={category}'
            })
            logger.info(f"Deleted all knowledge in category: {category}")
            return True
        except Exception as e:
            logger.error(f"Error deleting category: {e}")
            return False

    def list_categories(self) -> List[str]:
        """
        Get list of all categories in knowledge base.

        Returns:
            List of category names
        """
        try:
            # Use facet search to get unique categories
            result = self.typesense_client.collections[self.collection_name].documents.search({
                'q': '*',
                'facet_by': 'category',
                'per_page': 0,
            })

            categories = []
            for facet in result.get('facet_counts', []):
                if facet['field_name'] == 'category':
                    categories = [c['value'] for c in facet['counts']]
                    break

            return categories
        except Exception as e:
            logger.error(f"Error listing categories: {e}")
            return []


# Singleton instance
knowledge_service = KnowledgeService()
