/**
 * Alert state management with Zustand.
 */

import { create } from 'zustand'
import type { Alert } from '@/types'
import { alertApi } from '@/lib/api'

interface AlertState {
  // State
  alerts: Alert[]
  isLoading: boolean
  error: string | null

  // Actions
  loadAlertsForFile: (fileId: string) => Promise<void>
  loadAlertsForConversation: (conversationId: string) => Promise<void>
  clearAlerts: () => void
  clearError: () => void
}

export const useAlertStore = create<AlertState>((set) => ({
  // Initial state
  alerts: [],
  isLoading: false,
  error: null,

  // Load alerts for a file
  loadAlertsForFile: async (fileId: string) => {
    set({ isLoading: true, error: null })

    try {
      const alerts = await alertApi.getForFile(fileId)
      set({ alerts, isLoading: false })
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Failed to load alerts'
      set({ error: message, isLoading: false, alerts: [] })
    }
  },

  // Load alerts for a conversation
  loadAlertsForConversation: async (conversationId: string) => {
    set({ isLoading: true, error: null })

    try {
      const alerts = await alertApi.getForConversation(conversationId)
      set({ alerts, isLoading: false })
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Failed to load alerts'
      set({ error: message, isLoading: false, alerts: [] })
    }
  },

  // Clear all alerts
  clearAlerts: () => set({ alerts: [] }),

  // Clear error
  clearError: () => set({ error: null }),
}))
