/**
 * API client for backend communication.
 */

import type {
  Conversation,
  ConversationWithMessages,
  Message,
  MessageStreamChunk,
  SendMessageRequest,
  FileUpload,
  Alert,
  LoginRequest,
  RegisterRequest,
  AuthTokens,
  User,
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Utility to get auth token (for now, using mock token)
// TODO: Implement proper authentication
function getAuthToken(): string {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('auth_token') || ''
  }
  return ''
}

// Utility to handle API errors
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    // Handle 401 Unauthorized - token expired or invalid
    if (response.status === 401) {
      // Clear expired token
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_id')
      }
      throw new Error('Session expired. Please refresh the page.')
    }

    const error = await response.json().catch(() => ({
      detail: response.statusText,
    }))
    throw new Error(error.detail || 'An error occurred')
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

/**
 * Conversation API
 */
export const conversationApi = {
  /**
   * Get all conversations for the current user.
   */
  async list(): Promise<Conversation[]> {
    const response = await fetch(`${API_URL}/api/conversations`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    })
    return handleResponse<Conversation[]>(response)
  },

  /**
   * Create a new conversation.
   */
  async create(title?: string): Promise<Conversation> {
    const response = await fetch(`${API_URL}/api/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getAuthToken()}`,
      },
      body: JSON.stringify({ title }),
    })
    return handleResponse<Conversation>(response)
  },

  /**
   * Get a specific conversation with messages.
   */
  async get(id: string): Promise<ConversationWithMessages> {
    const response = await fetch(`${API_URL}/api/conversations/${id}`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    })
    return handleResponse<ConversationWithMessages>(response)
  },

  /**
   * Update a conversation.
   */
  async update(id: string, title: string): Promise<Conversation> {
    const response = await fetch(`${API_URL}/api/conversations/${id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getAuthToken()}`,
      },
      body: JSON.stringify({ title }),
    })
    return handleResponse<Conversation>(response)
  },

  /**
   * Delete a conversation.
   */
  async delete(id: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/conversations/${id}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    })
    return handleResponse<void>(response)
  },
}

/**
 * Message API
 */
export const messageApi = {
  /**
   * Get messages for a conversation.
   */
  async list(conversationId: string): Promise<Message[]> {
    const response = await fetch(
      `${API_URL}/api/conversations/${conversationId}/messages`,
      {
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
        },
      }
    )
    return handleResponse<Message[]>(response)
  },

  /**
   * Send a message and stream the response.
   * Returns an async generator that yields message chunks.
   */
  async *sendMessageStream(
    conversationId: string,
    content: string
  ): AsyncGenerator<MessageStreamChunk> {
    const response = await fetch(
      `${API_URL}/api/conversations/${conversationId}/messages`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify({ content } as SendMessageRequest),
      }
    )

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()

    try {
      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            try {
              const parsed: MessageStreamChunk = JSON.parse(data)
              yield parsed
            } catch (e) {
              console.error('Failed to parse SSE data:', data, e)
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  },
}

/**
 * File API
 */
export const fileApi = {
  /**
   * Upload a file with optional conversation association.
   */
  async upload(
    file: File,
    conversationId?: string,
    onProgress?: (progress: number) => void
  ): Promise<FileUpload> {
    const formData = new FormData()
    formData.append('file', file)
    if (conversationId) {
      formData.append('conversation_id', conversationId)
    }

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const progress = Math.round((e.loaded / e.total) * 100)
          onProgress(progress)
        }
      })

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText)
            resolve(data)
          } catch (e) {
            reject(new Error('Failed to parse upload response'))
          }
        } else {
          try {
            const error = JSON.parse(xhr.responseText)
            reject(new Error(error.detail || 'Upload failed'))
          } catch (e) {
            reject(new Error(`Upload failed with status ${xhr.status}`))
          }
        }
      })

      xhr.addEventListener('error', () => {
        reject(new Error('Network error during upload'))
      })

      xhr.open('POST', `${API_URL}/api/files/upload`)
      xhr.setRequestHeader('Authorization', `Bearer ${getAuthToken()}`)
      xhr.send(formData)
    })
  },

  /**
   * List all files for the current user.
   */
  async list(conversationId?: string): Promise<FileUpload[]> {
    const url = conversationId
      ? `${API_URL}/api/files?conversation_id=${conversationId}`
      : `${API_URL}/api/files`

    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    })
    return handleResponse<FileUpload[]>(response)
  },

  /**
   * Delete a file.
   */
  async delete(fileId: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/files/${fileId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    })
    return handleResponse<void>(response)
  },
}

/**
 * Alert API
 */
export const alertApi = {
  /**
   * Get alerts for a specific file.
   */
  async getForFile(fileId: string): Promise<Alert[]> {
    const response = await fetch(`${API_URL}/api/alerts/files/${fileId}`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    })
    return handleResponse<Alert[]>(response)
  },

  /**
   * Get alerts for a conversation.
   */
  async getForConversation(conversationId: string): Promise<Alert[]> {
    const response = await fetch(
      `${API_URL}/api/alerts/conversations/${conversationId}`,
      {
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
        },
      }
    )
    return handleResponse<Alert[]>(response)
  },
}

/**
 * Auth API
 */
export const authApi = {
  /**
   * Register a new user.
   */
  async register(data: RegisterRequest): Promise<AuthTokens> {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    return handleResponse<AuthTokens>(response)
  },

  /**
   * Login with email and password.
   */
  async login(data: LoginRequest): Promise<AuthTokens> {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    return handleResponse<AuthTokens>(response)
  },

  /**
   * Refresh access token.
   */
  async refresh(refreshToken: string): Promise<AuthTokens> {
    const response = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    return handleResponse<AuthTokens>(response)
  },

  /**
   * Get current user info (requires valid token).
   */
  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    })
    return handleResponse<User>(response)
  },
}

/**
 * Generic API client for custom endpoints
 */
export const api = {
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    })
    return handleResponse<T>(response)
  },

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getAuthToken()}`,
      },
      body: data ? JSON.stringify(data) : undefined,
    })
    return handleResponse<T>(response)
  },

  async patch<T>(endpoint: string, data?: unknown): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getAuthToken()}`,
      },
      body: data ? JSON.stringify(data) : undefined,
    })
    return handleResponse<T>(response)
  },

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
      },
    })
    return handleResponse<T>(response)
  },
}
