#!/bin/bash
# Script to initialize Ollama with required models

echo "Waiting for Ollama to be ready..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
  sleep 2
done

echo "Ollama is ready. Pulling models..."

# Pull embedding model (nomic-embed-text - 768 dimensions)
echo "Pulling nomic-embed-text for embeddings..."
ollama pull nomic-embed-text

# Pull LLM model (mistral 7B with French support)
echo "Pulling mistral:7b-instruct for chat..."
ollama pull mistral:7b-instruct

echo "All models pulled successfully!"
echo "Available models:"
ollama list
