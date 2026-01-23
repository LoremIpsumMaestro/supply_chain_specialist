/**
 * File upload state management with Zustand.
 */

import { create } from 'zustand'
import type { FileUpload } from '@/types'
import { fileApi } from '@/lib/api'

interface FileState {
  // State
  files: FileUpload[]
  uploadProgress: Record<string, number> // filename -> progress %
  isUploading: boolean
  error: string | null

  // Actions
  uploadFile: (file: File, conversationId?: string) => Promise<FileUpload>
  loadFiles: (conversationId?: string) => Promise<void>
  deleteFile: (fileId: string) => Promise<void>
  clearError: () => void
}

export const useFileStore = create<FileState>((set, get) => ({
  // Initial state
  files: [],
  uploadProgress: {},
  isUploading: false,
  error: null,

  // Upload a file
  uploadFile: async (file: File, conversationId?: string) => {
    set({ isUploading: true, error: null })

    try {
      const uploadedFile = await fileApi.upload(
        file,
        conversationId,
        (progress) => {
          set((state) => ({
            uploadProgress: {
              ...state.uploadProgress,
              [file.name]: progress,
            },
          }))
        }
      )

      // Add to files list
      set((state) => ({
        files: [...state.files, uploadedFile],
        isUploading: false,
        uploadProgress: {
          ...state.uploadProgress,
          [file.name]: 100,
        },
      }))

      // Clear progress after 2s
      setTimeout(() => {
        set((state) => {
          const { [file.name]: _, ...rest } = state.uploadProgress
          return { uploadProgress: rest }
        })
      }, 2000)

      return uploadedFile
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Upload failed'
      set({ isUploading: false, error: message })
      throw error
    }
  },

  // Load files from API
  loadFiles: async (conversationId?: string) => {
    try {
      const files = await fileApi.list(conversationId)
      set({ files, error: null })
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Failed to load files'
      set({ error: message, files: [] })
    }
  },

  // Delete a file
  deleteFile: async (fileId: string) => {
    try {
      await fileApi.delete(fileId)
      set((state) => ({
        files: state.files.filter((f) => f.id !== fileId),
        error: null,
      }))
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Failed to delete file'
      set({ error: message })
      throw error
    }
  },

  // Clear error
  clearError: () => set({ error: null }),
}))
