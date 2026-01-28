/**
 * Authentication utilities for the frontend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface TokenResponse {
  access_token: string
  token_type: string
  user_id: string
}

/**
 * Get or create a demo authentication token.
 * In production, this would be replaced by proper login.
 */
export async function ensureAuthToken(): Promise<string> {
  // Check if we already have a token
  if (typeof window !== 'undefined') {
    const existingToken = localStorage.getItem('auth_token')

    // If we have a token, verify it's still valid by checking its expiry
    if (existingToken) {
      try {
        // Decode JWT to check expiry (basic check without verification)
        const payload = JSON.parse(atob(existingToken.split('.')[1]))
        const expiresAt = payload.exp * 1000 // Convert to milliseconds
        const now = Date.now()

        // If token expires in more than 1 minute, use it
        if (expiresAt > now + 60000) {
          return existingToken
        }

        // Token is expired or about to expire, clear it
        console.log('Token expired or expiring soon, getting new one')
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_id')
      } catch (e) {
        // If we can't decode the token, it's invalid - clear it
        console.warn('Invalid token format, clearing and getting new one')
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_id')
      }
    }

    // Get a new demo token
    try {
      const response = await fetch(`${API_URL}/api/auth/demo-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to get auth token')
      }

      const data: TokenResponse = await response.json()

      // Store the token
      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('user_id', data.user_id)

      return data.access_token
    } catch (error) {
      console.error('Failed to get auth token:', error)
      throw error
    }
  }

  return ''
}

/**
 * Clear the authentication token (logout).
 */
export function clearAuthToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_id')
  }
}
