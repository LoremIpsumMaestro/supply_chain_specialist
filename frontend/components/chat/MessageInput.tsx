'use client'

import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useMessageStore } from '@/store/messageStore'
import { messageApi } from '@/lib/api'
import { ensureAuthToken } from '@/lib/auth'
import type { Message } from '@/types'

interface MessageInputProps {
  conversationId: string
}

export default function MessageInput({ conversationId }: MessageInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const {
    addMessage,
    setStreaming,
    setStreamingContent,
    appendStreamingContent,
    isStreaming,
  } = useMessageStore()

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [input])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim() || isStreaming) return

    const userMessage: Message = {
      id: crypto.randomUUID(),
      conversation_id: conversationId,
      role: 'user',
      content: input.trim(),
      created_at: new Date().toISOString(),
    }

    // Add user message
    addMessage(conversationId, userMessage)

    // Clear input
    setInput('')

    // Start streaming
    setStreaming(true)
    setStreamingContent('')

    try {
      // Ensure we have an auth token
      await ensureAuthToken()

      let accumulatedContent = ''
      let citations = []

      for await (const chunk of messageApi.sendMessageStream(
        conversationId,
        userMessage.content
      )) {
        if (chunk.error) {
          console.error('Streaming error:', chunk.error)
          break
        }

        if (chunk.content) {
          accumulatedContent += chunk.content
          appendStreamingContent(chunk.content)
        }

        if (chunk.citations) {
          citations = chunk.citations
        }

        if (chunk.is_final) {
          // Add complete assistant message
          const assistantMessage: Message = {
            id: crypto.randomUUID(),
            conversation_id: conversationId,
            role: 'assistant',
            content: accumulatedContent,
            citations: citations.length > 0 ? citations : undefined,
            created_at: new Date().toISOString(),
          }

          addMessage(conversationId, assistantMessage)
          break
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setStreaming(false)
      setStreamingContent('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="border-t bg-background p-4">
      <div className="mx-auto flex max-w-3xl gap-3">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Posez votre question..."
          disabled={isStreaming}
          rows={1}
          className="
            flex-1 resize-none rounded-lg border border-input bg-background px-4 py-3 text-sm
            ring-offset-background placeholder:text-muted-foreground
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
            disabled:cursor-not-allowed disabled:opacity-50
          "
          style={{ maxHeight: '200px' }}
        />

        <Button
          type="submit"
          size="icon"
          disabled={!input.trim() || isStreaming}
          className="h-auto self-end"
        >
          <Send className="h-5 w-5" />
          <span className="sr-only">Envoyer</span>
        </Button>
      </div>

      <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-muted-foreground">
        Appuyez sur Entrée pour envoyer, Maj+Entrée pour une nouvelle ligne
      </p>
    </form>
  )
}
