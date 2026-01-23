'use client'

import { useEffect, useState } from 'react'
import { useConversationStore } from '@/store/conversationStore'
import { useMessageStore } from '@/store/messageStore'
import { useFileStore } from '@/store/fileStore'
import { useAlertStore } from '@/store/alertStore'
import { conversationApi } from '@/lib/api'
import { ensureAuthToken } from '@/lib/auth'
import ChatLayout from '@/components/chat/ChatLayout'
import MessageList from '@/components/chat/MessageList'
import MessageInput from '@/components/chat/MessageInput'
import { FileUpload } from '@/components/chat/FileUpload'
import { AlertList } from '@/components/chat/AlertBadge'
import { Button } from '@/components/ui/button'
import { Upload, X } from 'lucide-react'

export default function ChatPage() {
  const { activeConversationId, conversations, addConversation, setActiveConversation } =
    useConversationStore()
  const { setMessages } = useMessageStore()
  const { loadFiles, files } = useFileStore()
  const { loadAlertsForConversation, alerts } = useAlertStore()
  const [showUpload, setShowUpload] = useState(false)

  // Create initial conversation if none exists
  useEffect(() => {
    const initializeConversation = async () => {
      if (conversations.length === 0 && !activeConversationId) {
        try {
          // Ensure we have an auth token
          await ensureAuthToken()
          const newConversation = await conversationApi.create()
          addConversation(newConversation)
          setActiveConversation(newConversation.id)
        } catch (error) {
          console.error('Failed to create initial conversation:', error)
        }
      } else if (conversations.length > 0 && !activeConversationId) {
        // Select first conversation if none is active
        setActiveConversation(conversations[0].id)
      }
    }

    initializeConversation()
  }, [conversations, activeConversationId, addConversation, setActiveConversation])

  // Load messages, files, and alerts when active conversation changes
  useEffect(() => {
    const loadConversationData = async () => {
      if (!activeConversationId) return

      try {
        // Ensure we have an auth token
        await ensureAuthToken()

        // Load messages
        const conversation = await conversationApi.get(activeConversationId)
        setMessages(activeConversationId, conversation.messages)

        // Load files and alerts for this conversation
        await loadFiles(activeConversationId)
        await loadAlertsForConversation(activeConversationId)
      } catch (error) {
        console.error('Failed to load conversation data:', error)
      }
    }

    loadConversationData()
  }, [activeConversationId, setMessages, loadFiles, loadAlertsForConversation])

  if (!activeConversationId) {
    return (
      <ChatLayout>
        <div className="flex h-full items-center justify-center text-muted-foreground">
          <p>Chargement...</p>
        </div>
      </ChatLayout>
    )
  }

  return (
    <ChatLayout>
      <div className="flex h-full flex-col">
        {/* File upload toggle button */}
        <div className="p-4 border-b flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowUpload(!showUpload)}
            >
              {showUpload ? (
                <>
                  <X className="h-4 w-4 mr-2" />
                  Fermer
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Uploader un fichier
                </>
              )}
            </Button>
            {files.length > 0 && (
              <span className="text-sm text-gray-600">
                {files.length} fichier{files.length > 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>

        {/* File upload area */}
        {showUpload && (
          <div className="p-4 bg-gray-50 border-b">
            <FileUpload
              conversationId={activeConversationId}
              onUploadComplete={async (file) => {
                console.log('File uploaded:', file)
                // Reload files and alerts after upload
                await loadFiles(activeConversationId)
                await loadAlertsForConversation(activeConversationId)
                setShowUpload(false)
              }}
            />
          </div>
        )}

        {/* Alerts display */}
        {alerts.length > 0 && (
          <div className="p-4 bg-yellow-50 border-b">
            <AlertList alerts={alerts} />
          </div>
        )}

        {/* Messages area - scrollable */}
        <div className="flex-1 overflow-hidden">
          <MessageList conversationId={activeConversationId} />
        </div>

        {/* Input area - fixed at bottom */}
        <div className="flex-shrink-0">
          <MessageInput conversationId={activeConversationId} />
        </div>
      </div>
    </ChatLayout>
  )
}
