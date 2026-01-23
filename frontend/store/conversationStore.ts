/**
 * Zustand store for conversation management.
 */

import { create } from 'zustand'
import type { Conversation } from '@/types'

interface ConversationState {
  conversations: Conversation[]
  activeConversationId: string | null
  isLoading: boolean
  error: string | null

  // Actions
  setConversations: (conversations: Conversation[]) => void
  addConversation: (conversation: Conversation) => void
  updateConversation: (id: string, updates: Partial<Conversation>) => void
  removeConversation: (id: string) => void
  setActiveConversation: (id: string | null) => void
  setLoading: (isLoading: boolean) => void
  setError: (error: string | null) => void
  reset: () => void
}

const initialState = {
  conversations: [],
  activeConversationId: null,
  isLoading: false,
  error: null,
}

export const useConversationStore = create<ConversationState>((set) => ({
  ...initialState,

  setConversations: (conversations) => set({ conversations }),

  addConversation: (conversation) =>
    set((state) => ({
      conversations: [conversation, ...state.conversations],
    })),

  updateConversation: (id, updates) =>
    set((state) => ({
      conversations: state.conversations.map((conv) =>
        conv.id === id ? { ...conv, ...updates } : conv
      ),
    })),

  removeConversation: (id) =>
    set((state) => ({
      conversations: state.conversations.filter((conv) => conv.id !== id),
      activeConversationId:
        state.activeConversationId === id ? null : state.activeConversationId,
    })),

  setActiveConversation: (id) => set({ activeConversationId: id }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  reset: () => set(initialState),
}))
