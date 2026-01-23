'use client'

import { useEffect, useRef } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useMessageStore } from '@/store/messageStore'
import { useUIStore } from '@/store/uiStore'
import Message from './Message'
import LoadingIndicator from './LoadingIndicator'

interface MessageListProps {
  conversationId: string
}

export default function MessageList({ conversationId }: MessageListProps) {
  const { messagesByConversation, isStreaming, streamingContent } = useMessageStore()
  const { isAutoScrollEnabled, setAutoScrollEnabled, setNewMessageIndicator } =
    useUIStore()

  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const messages = messagesByConversation[conversationId] || []

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (isAutoScrollEnabled && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, streamingContent, isAutoScrollEnabled])

  // Detect manual scroll up
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const element = e.currentTarget
    const isAtBottom =
      element.scrollHeight - element.scrollTop <= element.clientHeight + 100

    if (!isAtBottom && isAutoScrollEnabled) {
      setAutoScrollEnabled(false)
      setNewMessageIndicator(true)
    } else if (isAtBottom && !isAutoScrollEnabled) {
      setAutoScrollEnabled(true)
      setNewMessageIndicator(false)
    }
  }

  const scrollToBottom = () => {
    setAutoScrollEnabled(true)
    setNewMessageIndicator(false)
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  if (messages.length === 0 && !isStreaming) {
    return (
      <div className="flex h-full items-center justify-center text-center text-muted-foreground">
        <div>
          <p className="text-lg font-semibold">
            Bienvenue dans votre Assistant IA Supply Chain
          </p>
          <p className="mt-2 text-sm">
            Posez une question ou uploadez un document pour commencer
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative h-full">
      <ScrollArea
        ref={scrollAreaRef}
        className="h-full px-4 py-6"
        onScroll={handleScroll}
      >
        <div className="mx-auto max-w-3xl space-y-6">
          {messages.map((message) => (
            <Message key={message.id} message={message} />
          ))}

          {isStreaming && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg bg-muted p-4">
                <div className="whitespace-pre-wrap break-words text-sm">
                  {streamingContent}
                  <LoadingIndicator />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* New message indicator */}
      {!isAutoScrollEnabled && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground shadow-lg transition-opacity hover:bg-primary/90"
        >
          Nouveau message ↓
        </button>
      )}
    </div>
  )
}
