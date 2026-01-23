'use client'

import { Plus, LogOut } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useConversationStore } from '@/store/conversationStore'
import { useAuthStore } from '@/store/authStore'
import { conversationApi } from '@/lib/api'
import { ensureAuthToken } from '@/lib/auth'
import ConversationList from './ConversationList'

export default function Sidebar() {
  const router = useRouter()
  const { addConversation, setActiveConversation } = useConversationStore()
  const { logout, user } = useAuthStore()

  const handleNewConversation = async () => {
    try {
      // Ensure we have an auth token
      await ensureAuthToken()
      const newConversation = await conversationApi.create()
      addConversation(newConversation)
      setActiveConversation(newConversation.id)
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  return (
    <div className="flex h-full flex-col border-r bg-background">
      {/* Header with New Conversation button */}
      <div className="border-b p-4">
        <Button
          onClick={handleNewConversation}
          className="w-full"
          size="sm"
        >
          <Plus className="mr-2 h-4 w-4" />
          Nouvelle conversation
        </Button>
      </div>

      {/* Conversation list */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          <ConversationList />
        </div>
      </ScrollArea>

      {/* Footer with user info and logout */}
      <div className="border-t p-4 space-y-2">
        {user && (
          <div className="text-xs text-muted-foreground mb-2">
            <p className="font-medium truncate">{user.email}</p>
            {user.full_name && <p className="truncate">{user.full_name}</p>}
          </div>
        )}
        <Button
          onClick={handleLogout}
          variant="outline"
          size="sm"
          className="w-full"
        >
          <LogOut className="mr-2 h-4 w-4" />
          Déconnexion
        </Button>
        <div className="text-center text-xs text-muted-foreground pt-2">
          <p>Supply Chain AI Assistant</p>
          <p className="mt-1">Données purgées après 24h</p>
        </div>
      </div>
    </div>
  )
}
