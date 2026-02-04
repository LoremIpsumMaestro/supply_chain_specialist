"""LLM service for generating responses with Ollama and RAG."""

print("=" * 80)
print("🔥 LLM_SERVICE.PY IS BEING LOADED NOW!")
print("=" * 80)

import asyncio
import json
import logging
import requests
from datetime import datetime
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.models.message import MessageDB, MessageStreamChunk
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
        import time
        start_total = time.time()

        try:
            # Get last user message
            last_message = conversation_history[-1] if conversation_history else None
            if not last_message or last_message.role != "user":
                logger.error("No user message found in conversation history")
                return

            user_query = last_message.content

            # Check if conversation has uploaded files
            start_files = time.time()
            files = db.query(FileDB).filter(
                FileDB.conversation_id == conversation_id,
                FileDB.user_id == user_id,
            ).all()
            logger.info(f"⏱️ File query took: {time.time() - start_files:.3f}s")

            # Perform searches: knowledge base + user documents (OPTIMIZED: parallel + shared embedding)
            rag_context = ""
            search_results = []
            knowledge_results = []

            # OPTIMIZATION: Generate embedding once for both searches
            start_embedding = time.time()
            query_embedding = rag_service.generate_embedding(user_query)
            logger.info(f"⏱️ Embedding generation took: {time.time() - start_embedding:.3f}s")

            if query_embedding:
                # OPTIMIZATION: Run both searches in parallel using asyncio.to_thread
                start_searches = time.time()
                logger.info(f"Running parallel searches for query: {user_query[:50]}...")

                # Define async wrappers for synchronous functions
                async def search_kb():
                    return await asyncio.to_thread(
                        knowledge_service.search_knowledge,
                        query=user_query,
                        top_k=3,
                        query_embedding=query_embedding,
                    )

                async def search_docs():
                    if files:
                        return await asyncio.to_thread(
                            rag_service.hybrid_search,
                            query=user_query,
                            user_id=str(user_id),
                            top_k=5,
                            query_embedding=query_embedding,
                        )
                    return []

                # Execute searches in parallel
                knowledge_results, search_results = await asyncio.gather(
                    search_kb(),
                    search_docs(),
                )

                searches_duration = time.time() - start_searches
                logger.info(f"⏱️ Parallel searches took: {searches_duration:.3f}s")
                logger.info(f"Knowledge base returned {len(knowledge_results)} results")
                logger.info(f"User documents returned {len(search_results)} results")
            else:
                logger.warning("Failed to generate query embedding, skipping searches")

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
            start_build = time.time()
            messages = self._build_messages(conversation_history, rag_context)
            logger.info(f"⏱️ Build messages took: {time.time() - start_build:.3f}s")

            logger.info(f"⏱️ TOTAL TIME BEFORE STREAMING: {time.time() - start_total:.3f}s")

            # Stream response from Ollama
            start_stream = time.time()
            first_chunk = True
            async for chunk in self._stream_ollama_response(messages):
                if first_chunk:
                    logger.info(f"⏱️ Time to FIRST token: {time.time() - start_total:.3f}s")
                    first_chunk = False
                yield chunk
            logger.info(f"⏱️ Streaming took: {time.time() - start_stream:.3f}s")

            # Send final chunk
            yield MessageStreamChunk(
                content="",
                is_final=True,
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
                "keep_alive": "5m",  # Keep model loaded for 5 minutes
                "options": {
                    "temperature": self.temperature,
                }
            }
            print(f"🔍 DEBUG: Calling Ollama: {url}")
            print(f"🔍 DEBUG: Model: {self.model}")
            print(f"🔍 DEBUG: Payload keys: {payload.keys()}")

            # Call Ollama chat API with streaming
            # Use tuple timeout: (connect_timeout, read_timeout)
            # - connect_timeout: 10s to detect if Ollama is down
            # - read_timeout: 300s (5 min) for streaming generation
            response = requests.post(
                url,
                json=payload,
                stream=True,
                timeout=(10, 300),
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

                            # Small delay removed for performance
                            # await asyncio.sleep(0.01)

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
        # Inject current system date in French format
        try:
            import locale
            # Try to set French locale for month names
            try:
                locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
            except locale.Error:
                # Fallback: Use manual month mapping if locale not available
                logger.debug("French locale not available, using manual date formatting")

            current_date = datetime.now().strftime('%d %B %Y')
            logger.debug(f"Injecting system date: {current_date}")
        except Exception as e:
            logger.warning(f"Error formatting date, using ISO format: {e}")
            current_date = datetime.now().strftime('%Y-%m-%d')

        system_content = (
            f"DATE ACTUELLE: {current_date}\n\n"
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


# Singleton instance
llm_service = LLMService()
