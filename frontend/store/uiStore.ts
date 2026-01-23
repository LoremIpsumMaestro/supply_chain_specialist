/**
 * Zustand store for UI state management.
 */

import { create } from 'zustand'

interface UIState {
  isSidebarOpen: boolean
  showNewMessageIndicator: boolean
  isAutoScrollEnabled: boolean

  // Actions
  setSidebarOpen: (isOpen: boolean) => void
  toggleSidebar: () => void
  setNewMessageIndicator: (show: boolean) => void
  setAutoScrollEnabled: (enabled: boolean) => void
  reset: () => void
}

const initialState = {
  isSidebarOpen: true,
  showNewMessageIndicator: false,
  isAutoScrollEnabled: true,
}

export const useUIStore = create<UIState>((set) => ({
  ...initialState,

  setSidebarOpen: (isOpen) => set({ isSidebarOpen: isOpen }),

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

  setNewMessageIndicator: (show) => set({ showNewMessageIndicator: show }),

  setAutoScrollEnabled: (enabled) => set({ isAutoScrollEnabled: enabled }),

  reset: () => set(initialState),
}))
