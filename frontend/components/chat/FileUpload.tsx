'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, FileIcon, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useFileStore } from '@/store/fileStore'
import type { FileUpload as FileUploadType } from '@/types'

interface FileUploadProps {
  conversationId?: string
  onUploadComplete?: (file: FileUploadType) => void
  onUploadError?: (error: string) => void
}

const ALLOWED_TYPES = [
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
  'application/vnd.ms-excel', // .xls
  'text/csv', // .csv
  'application/pdf', // .pdf
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  'application/msword', // .doc
  'application/vnd.openxmlformats-officedocument.presentationml.presentation', // .pptx
  'application/vnd.ms-powerpoint', // .ppt
  'text/plain', // .txt
]

const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB

export function FileUpload({
  conversationId,
  onUploadComplete,
  onUploadError,
}: FileUploadProps) {
  const { uploadFile, uploadProgress, isUploading, error, clearError } =
    useFileStore()
  const [localError, setLocalError] = useState<string | null>(null)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      setLocalError(null)
      clearError()

      if (acceptedFiles.length === 0) {
        return
      }

      const file = acceptedFiles[0]

      // Validate file type
      if (!ALLOWED_TYPES.includes(file.type)) {
        const errorMsg = `Type de fichier non supporté: ${file.type}. Formats acceptés: Excel, CSV, PDF, Word, PowerPoint, Texte.`
        setLocalError(errorMsg)
        onUploadError?.(errorMsg)
        return
      }

      // Validate file size
      if (file.size > MAX_FILE_SIZE) {
        const errorMsg = `Fichier trop volumineux: ${(file.size / 1024 / 1024).toFixed(1)}MB. Taille maximum: 50MB.`
        setLocalError(errorMsg)
        onUploadError?.(errorMsg)
        return
      }

      try {
        const uploadedFile = await uploadFile(file, conversationId)
        onUploadComplete?.(uploadedFile)
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Upload échoué'
        setLocalError(errorMsg)
        onUploadError?.(errorMsg)
      }
    },
    [uploadFile, conversationId, onUploadComplete, onUploadError, clearError]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': [
        '.xlsx',
      ],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        ['.docx'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation':
        ['.pptx'],
      'application/vnd.ms-powerpoint': ['.ppt'],
      'text/plain': ['.txt'],
    },
    maxSize: MAX_FILE_SIZE,
    multiple: false,
    disabled: isUploading,
  })

  const currentError = localError || error
  const currentProgress = Object.values(uploadProgress)[0] || 0

  return (
    <div className="w-full" data-testid="file-upload-container">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        data-testid="file-dropzone"
      >
        <input {...getInputProps()} data-testid="file-input" />

        <div className="flex flex-col items-center gap-2">
          {isUploading ? (
            <>
              <FileIcon className="h-10 w-10 text-blue-500 animate-pulse" />
              <div className="w-full max-w-xs">
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all duration-300"
                    style={{ width: `${currentProgress}%` }}
                  />
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  Upload en cours... {currentProgress}%
                </p>
              </div>
            </>
          ) : (
            <>
              <Upload className="h-10 w-10 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-700">
                  {isDragActive
                    ? 'Déposez le fichier ici'
                    : 'Glissez-déposez un fichier ou cliquez pour sélectionner'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Excel, CSV, PDF, Word, PowerPoint, Texte (max 50MB)
                </p>
              </div>
            </>
          )}
        </div>
      </div>

      {currentError && (
        <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-red-700">{currentError}</p>
          </div>
          <button
            onClick={() => {
              setLocalError(null)
              clearError()
            }}
            className="text-red-500 hover:text-red-700"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  )
}
