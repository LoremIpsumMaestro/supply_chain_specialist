"""Unit tests for RAG (Retrieval Augmented Generation) service."""

import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import pytest

from backend.models.file import FileType
from backend.services.document_parser import DocumentChunk
from backend.services.rag_service import RAGService


# ============================================================================
# RAGService Initialization Tests
# ============================================================================

@pytest.mark.rag
class TestRAGServiceInitialization:
    """Tests for RAG service initialization."""

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    def test_initialization(self, mock_redis, mock_typesense):
        """Test RAG service initializes with clients."""
        mock_redis.from_url.return_value = MagicMock()
        mock_typesense.Client.return_value = MagicMock()

        service = RAGService()

        assert service.typesense_client is not None
        assert service.redis_client is not None
        assert service.collection_name == "document_chunks"

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    def test_collection_creation(self, mock_redis, mock_typesense):
        """Test that collection is created if it doesn't exist."""
        mock_redis.from_url.return_value = MagicMock()

        # Mock TypeSense client
        mock_ts_client = MagicMock()
        mock_typesense.Client.return_value = mock_ts_client

        # Simulate collection doesn't exist
        from typesense.exceptions import ObjectNotFound
        mock_ts_client.collections.__getitem__.return_value.retrieve.side_effect = ObjectNotFound()

        service = RAGService()

        # Should attempt to create collection
        mock_ts_client.collections.create.assert_called_once()

        # Verify schema
        schema = mock_ts_client.collections.create.call_args[0][0]
        assert schema['name'] == "document_chunks"
        assert any(field['name'] == 'embedding' for field in schema['fields'])
        assert any(field['name'] == 'user_id' for field in schema['fields'])


# ============================================================================
# Embedding Generation Tests
# ============================================================================

@pytest.mark.rag
class TestEmbeddingGeneration:
    """Tests for embedding generation."""

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    @patch('backend.services.rag_service.requests')
    def test_generate_embedding_success(self, mock_requests, mock_redis, mock_typesense):
        """Test successful embedding generation."""
        # Setup mocks
        mock_redis.from_url.return_value = MagicMock()
        mock_redis.from_url.return_value.get.return_value = None  # Cache miss
        mock_typesense.Client.return_value = MagicMock()

        # Mock Ollama API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'embedding': [0.1] * 768  # 768-dimensional embedding
        }
        mock_requests.post.return_value = mock_response

        service = RAGService()
        embedding = service.generate_embedding("Test text")

        assert embedding is not None
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    def test_generate_embedding_cache_hit(self, mock_redis, mock_typesense):
        """Test embedding retrieval from cache."""
        # Setup mocks
        cached_embedding = json.dumps([0.2] * 768)
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = cached_embedding
        mock_redis.from_url.return_value = mock_redis_client
        mock_typesense.Client.return_value = MagicMock()

        service = RAGService()
        embedding = service.generate_embedding("Test text")

        # Should return cached embedding
        assert embedding is not None
        assert len(embedding) == 768
        assert embedding[0] == 0.2

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    @patch('backend.services.rag_service.requests')
    def test_generate_embedding_api_error(self, mock_requests, mock_redis, mock_typesense):
        """Test handling of API errors during embedding generation."""
        # Setup mocks
        mock_redis.from_url.return_value = MagicMock()
        mock_redis.from_url.return_value.get.return_value = None
        mock_typesense.Client.return_value = MagicMock()

        # Mock API error
        mock_requests.post.side_effect = Exception("API Error")

        service = RAGService()
        embedding = service.generate_embedding("Test text")

        # Should return None on error
        assert embedding is None

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    @patch('backend.services.rag_service.requests')
    def test_generate_embeddings_batch(self, mock_requests, mock_redis, mock_typesense):
        """Test batch embedding generation."""
        # Setup mocks
        mock_redis.from_url.return_value = MagicMock()
        mock_redis.from_url.return_value.get.return_value = None
        mock_typesense.Client.return_value = MagicMock()

        # Mock Ollama API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'embedding': [0.1] * 768
        }
        mock_requests.post.return_value = mock_response

        service = RAGService()
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = service.generate_embeddings_batch(texts)

        assert len(embeddings) == 3
        assert all(emb is not None for emb in embeddings)


# ============================================================================
# Document Indexing Tests
# ============================================================================

@pytest.mark.rag
class TestDocumentIndexing:
    """Tests for document indexing."""

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    @patch('backend.services.rag_service.requests')
    def test_index_chunks_success(
        self,
        mock_requests,
        mock_redis,
        mock_typesense,
        sample_excel_chunks,
        test_user_id,
        test_file_id,
    ):
        """Test successful chunk indexing."""
        # Setup mocks
        mock_redis.from_url.return_value = MagicMock()
        mock_redis.from_url.return_value.get.return_value = None

        mock_ts_client = MagicMock()
        mock_typesense.Client.return_value = mock_ts_client

        # Mock embedding API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'embedding': [0.1] * 768
        }
        mock_requests.post.return_value = mock_response

        # Mock import success
        mock_ts_client.collections.__getitem__.return_value.documents.import_.return_value = []

        service = RAGService()
        result = service.index_chunks(
            chunks=sample_excel_chunks,
            user_id=test_user_id,
            file_id=test_file_id,
        )

        assert result is True

        # Verify import was called
        mock_ts_client.collections.__getitem__.return_value.documents.import_.assert_called_once()

        # Verify document structure
        call_args = mock_ts_client.collections.__getitem__.return_value.documents.import_.call_args
        documents = call_args[0][0]

        assert len(documents) == len(sample_excel_chunks)

        for doc in documents:
            assert 'chunk_id' in doc
            assert 'user_id' in doc
            assert doc['user_id'] == test_user_id
            assert 'file_id' in doc
            assert doc['file_id'] == test_file_id
            assert 'content' in doc
            assert 'embedding' in doc
            assert len(doc['embedding']) == 768
            assert 'metadata' in doc
            assert 'document_expires_at' in doc

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    @patch('backend.services.rag_service.requests')
    def test_index_chunks_with_ttl(
        self,
        mock_requests,
        mock_redis,
        mock_typesense,
        sample_excel_chunks,
        test_user_id,
        test_file_id,
    ):
        """Test that indexed documents have 24h TTL."""
        # Setup mocks
        mock_redis.from_url.return_value = MagicMock()
        mock_redis.from_url.return_value.get.return_value = None

        mock_ts_client = MagicMock()
        mock_typesense.Client.return_value = mock_ts_client

        # Mock embedding API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'embedding': [0.1] * 768
        }
        mock_requests.post.return_value = mock_response

        # Mock import
        mock_ts_client.collections.__getitem__.return_value.documents.import_.return_value = []

        service = RAGService()
        before_index = datetime.utcnow()

        result = service.index_chunks(
            chunks=sample_excel_chunks,
            user_id=test_user_id,
            file_id=test_file_id,
        )

        after_index = datetime.utcnow()

        # Verify TTL
        call_args = mock_ts_client.collections.__getitem__.return_value.documents.import_.call_args
        documents = call_args[0][0]

        for doc in documents:
            expires_at = datetime.fromtimestamp(doc['document_expires_at'])
            # Should expire ~24 hours from now
            expected_expiry = before_index + timedelta(hours=24)
            time_diff = abs((expires_at - expected_expiry).total_seconds())
            assert time_diff < 60  # Within 1 minute

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    @patch('backend.services.rag_service.requests')
    def test_index_chunks_embedding_failure(
        self,
        mock_requests,
        mock_redis,
        mock_typesense,
        sample_excel_chunks,
        test_user_id,
        test_file_id,
    ):
        """Test indexing when embedding generation fails."""
        # Setup mocks
        mock_redis.from_url.return_value = MagicMock()
        mock_redis.from_url.return_value.get.return_value = None

        mock_ts_client = MagicMock()
        mock_typesense.Client.return_value = mock_ts_client

        # Mock embedding API failure
        mock_requests.post.side_effect = Exception("API Error")

        service = RAGService()
        result = service.index_chunks(
            chunks=sample_excel_chunks,
            user_id=test_user_id,
            file_id=test_file_id,
        )

        # Should return False when all embeddings fail
        assert result is False


# ============================================================================
# Hybrid Search Tests
# ============================================================================

@pytest.mark.rag
class TestHybridSearch:
    """Tests for hybrid search functionality."""

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    @patch('backend.services.rag_service.requests')
    def test_hybrid_search_success(
        self,
        mock_requests,
        mock_redis,
        mock_typesense,
        test_user_id,
    ):
        """Test successful hybrid search."""
        # Setup mocks
        mock_redis.from_url.return_value = MagicMock()
        mock_redis.from_url.return_value.get.return_value = None

        mock_ts_client = MagicMock()
        mock_typesense.Client.return_value = mock_ts_client

        # Mock embedding API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'embedding': [0.1] * 768
        }
        mock_requests.post.return_value = mock_response

        # Mock search results
        mock_ts_client.collections.__getitem__.return_value.documents.search.return_value = {
            'hits': [
                {
                    'document': {
                        'content': 'Stock: -50',
                        'metadata': json.dumps({
                            'filename': 'test.xlsx',
                            'sheet_name': 'Stocks',
                            'cell_ref': 'C12',
                        }),
                    },
                    'text_match_info': {'score': 0.95},
                    'vector_distance': 0.1,
                },
                {
                    'document': {
                        'content': 'Stock: 150',
                        'metadata': json.dumps({
                            'filename': 'test.xlsx',
                            'sheet_name': 'Stocks',
                            'cell_ref': 'C10',
                        }),
                    },
                    'text_match_info': {'score': 0.85},
                    'vector_distance': 0.2,
                },
            ]
        }

        service = RAGService()
        results = service.hybrid_search(
            query="negative stock",
            user_id=test_user_id,
            top_k=5,
        )

        assert len(results) == 2

        # Verify result structure
        for result in results:
            assert 'content' in result
            assert 'metadata' in result
            assert 'score' in result
            assert 'vector_distance' in result

        # Verify metadata was parsed from JSON
        assert isinstance(results[0]['metadata'], dict)
        assert results[0]['metadata']['filename'] == 'test.xlsx'

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    @patch('backend.services.rag_service.requests')
    def test_hybrid_search_with_file_filter(
        self,
        mock_requests,
        mock_redis,
        mock_typesense,
        test_user_id,
        test_file_id,
    ):
        """Test search with file ID filter."""
        # Setup mocks
        mock_redis.from_url.return_value = MagicMock()
        mock_redis.from_url.return_value.get.return_value = None

        mock_ts_client = MagicMock()
        mock_typesense.Client.return_value = mock_ts_client

        # Mock embedding API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'embedding': [0.1] * 768
        }
        mock_requests.post.return_value = mock_response

        # Mock search results
        mock_ts_client.collections.__getitem__.return_value.documents.search.return_value = {
            'hits': []
        }

        service = RAGService()
        results = service.hybrid_search(
            query="test query",
            user_id=test_user_id,
            file_id=test_file_id,
            top_k=5,
        )

        # Verify filter_by includes both user_id and file_id
        call_args = mock_ts_client.collections.__getitem__.return_value.documents.search.call_args
        search_params = call_args[0][0]

        assert 'filter_by' in search_params
        assert f'user_id:={test_user_id}' in search_params['filter_by']
        assert f'file_id:={test_file_id}' in search_params['filter_by']

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    @patch('backend.services.rag_service.requests')
    def test_hybrid_search_embedding_failure(
        self,
        mock_requests,
        mock_redis,
        mock_typesense,
        test_user_id,
    ):
        """Test search when embedding generation fails."""
        # Setup mocks
        mock_redis.from_url.return_value = MagicMock()
        mock_redis.from_url.return_value.get.return_value = None

        mock_ts_client = MagicMock()
        mock_typesense.Client.return_value = mock_ts_client

        # Mock embedding API failure
        mock_requests.post.side_effect = Exception("API Error")

        service = RAGService()
        results = service.hybrid_search(
            query="test query",
            user_id=test_user_id,
        )

        # Should return empty list on error
        assert results == []


# ============================================================================
# RAG Context Building Tests
# ============================================================================

@pytest.mark.rag
class TestRAGContextBuilding:
    """Tests for building RAG context for LLM."""

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    def test_build_rag_context_with_results(self, mock_redis, mock_typesense):
        """Test building context from search results."""
        mock_redis.from_url.return_value = MagicMock()
        mock_typesense.Client.return_value = MagicMock()

        service = RAGService()

        search_results = [
            {
                'content': 'Stock: -50',
                'metadata': {
                    'filename': 'inventory.xlsx',
                    'file_type': 'excel',
                    'sheet_name': 'Products',
                    'cell_ref': 'C12',
                },
                'score': 0.95,
                'vector_distance': 0.1,
            },
            {
                'content': 'Lead time: 120 days',
                'metadata': {
                    'filename': 'suppliers.pdf',
                    'file_type': 'pdf',
                    'page': 5,
                },
                'score': 0.85,
                'vector_distance': 0.2,
            },
        ]

        context = service.build_rag_context(search_results)

        # Verify context structure
        assert "Voici les informations pertinentes" in context

        # Should include Excel citation with cell reference
        assert "inventory.xlsx" in context
        assert "C12" in context
        assert "Products" in context  # Sheet name

        # Should include PDF citation with page number
        assert "suppliers.pdf" in context
        assert "page 5" in context

        # Should include actual content
        assert "Stock: -50" in context
        assert "Lead time: 120 days" in context

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    def test_build_rag_context_empty_results(self, mock_redis, mock_typesense):
        """Test building context with no search results."""
        mock_redis.from_url.return_value = MagicMock()
        mock_typesense.Client.return_value = MagicMock()

        service = RAGService()
        context = service.build_rag_context([])

        # Should return message indicating no results
        assert "Aucune information pertinente" in context

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    def test_build_rag_context_all_file_types(self, mock_redis, mock_typesense):
        """Test context building for all supported file types."""
        mock_redis.from_url.return_value = MagicMock()
        mock_typesense.Client.return_value = MagicMock()

        service = RAGService()

        search_results = [
            {
                'content': 'Excel content',
                'metadata': {'filename': 'test.xlsx', 'file_type': 'excel', 'sheet_name': 'Sheet1', 'cell_ref': 'A1'},
                'score': 1.0, 'vector_distance': 0.0,
            },
            {
                'content': 'PDF content',
                'metadata': {'filename': 'test.pdf', 'file_type': 'pdf', 'page': 1},
                'score': 1.0, 'vector_distance': 0.0,
            },
            {
                'content': 'Word content',
                'metadata': {'filename': 'test.docx', 'file_type': 'word', 'paragraph_index': 3},
                'score': 1.0, 'vector_distance': 0.0,
            },
            {
                'content': 'PowerPoint content',
                'metadata': {'filename': 'test.pptx', 'file_type': 'powerpoint', 'slide_number': 2},
                'score': 1.0, 'vector_distance': 0.0,
            },
            {
                'content': 'CSV content',
                'metadata': {'filename': 'test.csv', 'file_type': 'csv', 'row_number': 5},
                'score': 1.0, 'vector_distance': 0.0,
            },
        ]

        context = service.build_rag_context(search_results)

        # Verify all file types are properly cited
        assert "test.xlsx" in context and "A1" in context
        assert "test.pdf" in context and "page 1" in context
        assert "test.docx" in context and "paragraphe 3" in context
        assert "test.pptx" in context and "slide 2" in context
        assert "test.csv" in context and "ligne 5" in context


# ============================================================================
# File Deletion Tests
# ============================================================================

@pytest.mark.rag
class TestFileChunkDeletion:
    """Tests for deleting file chunks."""

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    def test_delete_file_chunks_success(
        self,
        mock_redis,
        mock_typesense,
        test_file_id,
    ):
        """Test successful deletion of file chunks."""
        mock_redis.from_url.return_value = MagicMock()

        mock_ts_client = MagicMock()
        mock_typesense.Client.return_value = mock_ts_client

        service = RAGService()
        result = service.delete_file_chunks(test_file_id)

        assert result is True

        # Verify delete was called with correct filter
        mock_ts_client.collections.__getitem__.return_value.documents.delete.assert_called_once()
        call_args = mock_ts_client.collections.__getitem__.return_value.documents.delete.call_args
        filter_dict = call_args[0][0]
        assert f'file_id:={test_file_id}' in filter_dict['filter_by']

    @patch('backend.services.rag_service.typesense')
    @patch('backend.services.rag_service.Redis')
    def test_delete_file_chunks_error(
        self,
        mock_redis,
        mock_typesense,
        test_file_id,
    ):
        """Test handling of deletion errors."""
        mock_redis.from_url.return_value = MagicMock()

        mock_ts_client = MagicMock()
        mock_ts_client.collections.__getitem__.return_value.documents.delete.side_effect = Exception("Delete error")
        mock_typesense.Client.return_value = mock_ts_client

        service = RAGService()
        result = service.delete_file_chunks(test_file_id)

        # Should return False on error
        assert result is False
