/**
 * Zustand store for message management.
 */

import { create } from 'zustand'
import type { Message } from '@/types'

interface MessageState {
  messagesByConversation: Record<string, Message[]>
  isStreaming: boolean
  streamingContent: string
  error: string | null

  // Actions
  setMessages: (conversationId: string, messages: Message[]) => void
  addMessage: (conversationId: string, message: Message) => void
  updateMessage: (conversationId: string, messageId: string, updates: Partial<Message>) => void
  clearMessages: (conversationId: string) => void
  setStreaming: (isStreaming: boolean) => void
  setStreamingContent: (content: string) => void
  appendStreamingContent: (content: string) => void
  setError: (error: string | null) => void
  reset: () => void
}

const initialState = {
  messagesByConversation: {},
  isStreaming: false,
  streamingContent: '',
  error: null,
}

export const useMessageStore = create<MessageState>((set) => ({
  ...initialState,

  setMessages: (conversationId, messages) =>
    set((state) => ({
      messagesByConversation: {
        ...state.messagesByConversation,
        [conversationId]: messages,
      },
    })),

  addMessage: (conversationId, message) =>
    set((state) => ({
      messagesByConversation: {
        ...state.messagesByConversation,
        [conversationId]: [
          ...(state.messagesByConversation[conversationId] || []),
          message,
        ],
      },
    })),

  updateMessage: (conversationId, messageId, updates) =>
    set((state) => ({
      messagesByConversation: {
        ...state.messagesByConversation,
        [conversationId]: (state.messagesByConversation[conversationId] || []).map(
          (msg) => (msg.id === messageId ? { ...msg, ...updates } : msg)
        ),
      },
    })),

  clearMessages: (conversationId) =>
    set((state) => {
      const newMessages = { ...state.messagesByConversation }
      delete newMessages[conversationId]
      return { messagesByConversation: newMessages }
    }),

  setStreaming: (isStreaming) => set({ isStreaming }),

  setStreamingContent: (content) => set({ streamingContent: content }),

  appendStreamingContent: (content) =>
    set((state) => ({
      streamingContent: state.streamingContent + content,
    })),

  setError: (error) => set({ error }),

  reset: () => set(initialState),
}))
