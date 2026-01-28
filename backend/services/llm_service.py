"""LLM service for generating responses with Ollama and RAG."""

print("=" * 80)
print("🔥 LLM_SERVICE.PY IS BEING LOADED NOW!")
print("=" * 80)

import asyncio
import json
import logging
import requests
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.models.message import MessageDB, MessageStreamChunk, CitationMetadata
from backend.models.file import FileDB
from backend.services.rag_service import rag_service
from backend.services.knowledge_service import knowledge_service
from backend.config import settings


logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Ollama LLM with RAG capabilities."""

    def __init__(self):
        """Initialize LLM service with Ollama configuration."""
        self.ollama_base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_CHAT_MODEL
        self.temperature = 0.1  # Low temperature for anti-hallucination

    async def stream_response(
        self,
        conversation_history: List[MessageDB],
        conversation_id: UUID,
        db: Session,
        user_id: UUID,
    ) -> AsyncGenerator[MessageStreamChunk, None]:
        """
        Stream AI response for a conversation with RAG context.

        Args:
            conversation_history: List of previous messages for context
            conversation_id: ID of the current conversation
            db: Database session for RAG queries
            user_id: User ID for RAG filtering

        Yields:
            MessageStreamChunk objects with streaming content
        """
        try:
            # Get last user message
            last_message = conversation_history[-1] if conversation_history else None
            if not last_message or last_message.role != "user":
                logger.error("No user message found in conversation history")
                return

            user_query = last_message.content

            # Check if conversation has uploaded files
            files = db.query(FileDB).filter(
                FileDB.conversation_id == conversation_id,
                FileDB.user_id == user_id,
            ).all()

            # Perform searches: knowledge base + user documents
            rag_context = ""
            search_results = []
            knowledge_results = []

            # 1. Always search knowledge base
            logger.info(f"Searching knowledge base for query: {user_query[:50]}...")
            knowledge_results = knowledge_service.search_knowledge(
                query=user_query,
                top_k=3,  # Top 3 from knowledge base
            )

            if knowledge_results:
                logger.info(f"Knowledge base search returned {len(knowledge_results)} results")

            # 2. Search user documents if files exist
            if files:
                logger.info(f"Performing RAG search in user documents for query: {user_query[:50]}...")
                search_results = rag_service.hybrid_search(
                    query=user_query,
                    user_id=str(user_id),
                    top_k=5,  # Top 5 from user documents
                )

                if search_results:
                    logger.info(f"User documents search returned {len(search_results)} results")

            # 3. Build combined context
            if knowledge_results or search_results:
                context_parts = []

                # Add knowledge base context first
                if knowledge_results:
                    kb_context = knowledge_service.build_knowledge_context(knowledge_results)
                    context_parts.append(kb_context)

                # Add user documents context
                if search_results:
                    docs_context = rag_service.build_rag_context(search_results)
                    context_parts.append(docs_context)

                rag_context = "\n\n".join(context_parts)
            else:
                logger.info("No relevant results from knowledge base or user documents")
                if files:
                    rag_context = "Aucune information pertinente n'a été trouvée dans vos documents ou dans la base de connaissances sur ce sujet."

            # Build messages for LLM
            messages = self._build_messages(conversation_history, rag_context)

            # Stream response from Ollama
            async for chunk in self._stream_ollama_response(messages):
                yield chunk

            # Send final chunk with citations from both sources
            all_citations = []

            # Add citations from knowledge base
            if knowledge_results:
                kb_citations = self._extract_knowledge_citations(knowledge_results)
                all_citations.extend(kb_citations)

            # Add citations from user documents
            if search_results:
                doc_citations = self._extract_citations(search_results)
                all_citations.extend(doc_citations)

            yield MessageStreamChunk(
                content="",
                is_final=True,
                citations=all_citations if all_citations else None,
            )

        except Exception as e:
            logger.error(f"Error streaming LLM response: {e}", exc_info=True)
            # Yield error message to user
            yield MessageStreamChunk(
                content=f"\n\n⚠️ Erreur lors de la génération de la réponse: {str(e)}",
                is_final=True,
            )

    async def _stream_ollama_response(self, messages: List[dict]) -> AsyncGenerator[MessageStreamChunk, None]:
        """
        Stream response from Ollama API.

        Args:
            messages: List of messages for the conversation

        Yields:
            MessageStreamChunk objects with streaming content
        """
        try:
            # Log request details for debugging
            url = f"{self.ollama_base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": self.temperature,
                }
            }
            print(f"🔍 DEBUG: Calling Ollama: {url}")
            print(f"🔍 DEBUG: Model: {self.model}")
            print(f"🔍 DEBUG: Payload keys: {payload.keys()}")

            # Call Ollama chat API with streaming
            response = requests.post(
                url,
                json=payload,
                stream=True,
                timeout=60,
            )

            print(f"🔍 DEBUG: Ollama response status: {response.status_code}")
            response.raise_for_status()

            # Stream response chunks
            for line in response.iter_lines():
                if line:
                    try:
                        chunk_data = json.loads(line)

                        # Check if response is done
                        if chunk_data.get('done', False):
                            break

                        # Extract content from message
                        message = chunk_data.get('message', {})
                        content = message.get('content', '')

                        if content:
                            yield MessageStreamChunk(
                                content=content,
                                is_final=False,
                            )

                            # Small delay to simulate natural typing
                            await asyncio.sleep(0.01)

                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding JSON chunk: {e}")
                        continue

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request error: {e}")
            raise Exception(f"Erreur de connexion à Ollama: {str(e)}")

    def _build_messages(self, conversation_history: List[MessageDB], rag_context: str = "") -> List[dict]:
        """
        Build messages array for Ollama API.

        Args:
            conversation_history: List of previous messages
            rag_context: RAG context from document search

        Returns:
            List of message dicts for Ollama API
        """
        system_content = (
            "Tu es un assistant IA spécialisé en Supply Chain. "
            "Tu aides les professionnels (Opérationnels et Directeurs) à analyser "
            "leurs données et contextes opérationnels.\n\n"
        )

        if rag_context:
            system_content += (
                "RÈGLES IMPORTANTES:\n"
                "1. Réponds UNIQUEMENT en te basant sur les sources fournies ci-dessous.\n"
                "2. Cite TOUJOURS tes sources avec le format exact fourni (fichier, feuille, cellule/page).\n"
                "3. Si l'information n'est pas dans les sources, dis clairement: "
                "\"Je n'ai pas trouvé d'information sur ce sujet dans vos documents.\"\n"
                "4. N'invente JAMAIS d'informations.\n"
                "5. Privilégie les réponses concises et précises.\n\n"
                f"{rag_context}\n"
            )
        else:
            system_content += (
                "Réponds toujours en français et sois précis et factuel. "
                "Si tu ne trouves pas d'information pertinente, indique-le clairement "
                "plutôt que d'inventer une réponse."
            )

        system_message = {
            "role": "system",
            "content": system_content,
        }

        messages = [system_message]

        # Add conversation history (skip last system message if exists)
        for msg in conversation_history:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    def _extract_citations(self, search_results: List[dict]) -> List[CitationMetadata]:
        """
        Extract citation metadata from search results.

        Args:
            search_results: Results from RAG search

        Returns:
            List of CitationMetadata objects
        """
        if not search_results:
            return []

        citations = []

        for result in search_results:
            metadata = result['metadata']

            citation = CitationMetadata(
                source_type=metadata.get('file_type', ''),
                filename=metadata.get('filename', 'unknown'),
                page=metadata.get('page'),
                sheet_name=metadata.get('sheet_name'),
                cell_ref=metadata.get('cell_ref'),
                slide_number=metadata.get('slide_number'),
                row_number=metadata.get('row_number'),
                excerpt=result['content'][:200],  # First 200 chars
            )

            citations.append(citation)

        return citations

    def _extract_knowledge_citations(self, knowledge_results: List[dict]) -> List[CitationMetadata]:
        """
        Extract citation metadata from knowledge base search results.

        Args:
            knowledge_results: Results from knowledge base search

        Returns:
            List of CitationMetadata objects
        """
        if not knowledge_results:
            return []

        citations = []

        for result in knowledge_results:
            # Knowledge base citations use "knowledge" as source type
            citation = CitationMetadata(
                source_type='knowledge',
                filename=f"{result.get('category', 'General')} - {result.get('title', 'Untitled')}",
                page=None,
                sheet_name=None,
                cell_ref=None,
                slide_number=None,
                row_number=None,
                excerpt=result['content'][:200],  # First 200 chars
            )

            citations.append(citation)

        return citations


# Singleton instance
llm_service = LLMService()
