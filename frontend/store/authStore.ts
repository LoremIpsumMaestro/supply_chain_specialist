/**
 * Authentication state management with Zustand.
 */

import { create } from 'zustand'
import type { User, LoginRequest, RegisterRequest, AuthTokens } from '@/types'
import { authApi } from '@/lib/api'

interface AuthState {
  // State
  user: User | null
  tokens: AuthTokens | null
  isLoading: boolean
  error: string | null

  // Actions
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  loadUser: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  // Initial state
  user: null,
  tokens: null,
  isLoading: false,
  error: null,

  // Login
  login: async (data: LoginRequest) => {
    set({ isLoading: true, error: null })

    try {
      const tokens = await authApi.login(data)

      // Store tokens
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', tokens.access_token)
        localStorage.setItem('refresh_token', tokens.refresh_token)
      }

      set({ tokens, isLoading: false })

      // Load user info
      await get().loadUser()
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  // Register
  register: async (data: RegisterRequest) => {
    set({ isLoading: true, error: null })

    try {
      const tokens = await authApi.register(data)

      // Store tokens
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', tokens.access_token)
        localStorage.setItem('refresh_token', tokens.refresh_token)
      }

      set({ tokens, isLoading: false })

      // Load user info
      await get().loadUser()
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Registration failed'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  // Logout
  logout: () => {
    // Clear tokens from localStorage
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('refresh_token')
    }

    set({ user: null, tokens: null, error: null })
  },

  // Refresh access token
  refreshToken: async () => {
    const refreshToken =
      typeof window !== 'undefined'
        ? localStorage.getItem('refresh_token')
        : null

    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    try {
      const tokens = await authApi.refresh(refreshToken)

      // Update tokens
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', tokens.access_token)
        localStorage.setItem('refresh_token', tokens.refresh_token)
      }

      set({ tokens })
    } catch (error) {
      // Refresh failed, logout user
      get().logout()
      throw error
    }
  },

  // Load current user info
  loadUser: async () => {
    try {
      const user = await authApi.getCurrentUser()
      set({ user, error: null })
    } catch (error) {
      // Token might be expired, try refresh
      try {
        await get().refreshToken()
        const user = await authApi.getCurrentUser()
        set({ user, error: null })
      } catch (refreshError) {
        // Both failed, logout
        get().logout()
        throw refreshError
      }
    }
  },

  // Clear error
  clearError: () => set({ error: null }),
}))
