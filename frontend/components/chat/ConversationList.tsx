'use client'

import { useConversationStore } from '@/store/conversationStore'
import ConversationItem from './ConversationItem'

export default function ConversationList() {
  const { conversations, isLoading, error } = useConversationStore()

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="h-16 animate-pulse rounded-lg bg-muted"
          />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
        <p className="font-semibold">Erreur</p>
        <p className="mt-1">{error}</p>
      </div>
    )
  }

  if (conversations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
        <p className="text-sm">Aucune conversation</p>
        <p className="mt-1 text-xs">
          Cliquez sur &quot;Nouvelle conversation&quot; pour commencer
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {conversations.map((conversation) => (
        <ConversationItem
          key={conversation.id}
          conversation={conversation}
        />
      ))}
    </div>
  )
}
