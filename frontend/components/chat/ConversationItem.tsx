'use client'

import { formatDistanceToNow } from 'date-fns'
import { fr } from 'date-fns/locale'
import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useConversationStore } from '@/store/conversationStore'
import { useMessageStore } from '@/store/messageStore'
import { conversationApi } from '@/lib/api'
import { ensureAuthToken } from '@/lib/auth'
import type { Conversation } from '@/types'

interface ConversationItemProps {
  conversation: Conversation
}

export default function ConversationItem({ conversation }: ConversationItemProps) {
  const { activeConversationId, setActiveConversation, removeConversation } =
    useConversationStore()
  const { clearMessages } = useMessageStore()

  const isActive = activeConversationId === conversation.id

  const handleSelect = () => {
    setActiveConversation(conversation.id)
  }

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()

    if (!confirm('Êtes-vous sûr de vouloir supprimer cette conversation ?')) {
      return
    }

    try {
      // Ensure we have an auth token
      await ensureAuthToken()
      await conversationApi.delete(conversation.id)
      removeConversation(conversation.id)
      clearMessages(conversation.id)
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  const title = conversation.title || 'Nouvelle conversation'
  const timeAgo = formatDistanceToNow(new Date(conversation.updated_at), {
    addSuffix: true,
    locale: fr,
  })

  return (
    <div
      onClick={handleSelect}
      className={`
        group relative flex cursor-pointer items-start gap-3 rounded-lg p-3 transition-colors
        ${isActive ? 'bg-primary/10 text-primary' : 'hover:bg-muted'}
      `}
    >
      <div className="flex-1 min-w-0">
        <p className="truncate text-sm font-medium">{title}</p>
        <p className="mt-1 text-xs text-muted-foreground">{timeAgo}</p>
      </div>

      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 opacity-0 group-hover:opacity-100"
        onClick={handleDelete}
        aria-label="Supprimer la conversation"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  )
}
