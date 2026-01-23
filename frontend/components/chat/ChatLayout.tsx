'use client'

import { useEffect } from 'react'
import { Menu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useUIStore } from '@/store/uiStore'
import { useConversationStore } from '@/store/conversationStore'
import { conversationApi } from '@/lib/api'
import { ensureAuthToken } from '@/lib/auth'
import Sidebar from './Sidebar'

interface ChatLayoutProps {
  children: React.ReactNode
}

export default function ChatLayout({ children }: ChatLayoutProps) {
  const { isSidebarOpen, toggleSidebar } = useUIStore()
  const { setConversations, setLoading, setError } = useConversationStore()

  // Load conversations on mount
  useEffect(() => {
    const loadConversations = async () => {
      try {
        setLoading(true)
        // Ensure we have an auth token before making API calls
        await ensureAuthToken()
        const conversations = await conversationApi.list()
        setConversations(conversations)
      } catch (error) {
        console.error('Failed to load conversations:', error)
        setError(error instanceof Error ? error.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    loadConversations()
  }, [setConversations, setLoading, setError])

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar - hidden on mobile by default */}
      <div
        className={`
          fixed inset-y-0 left-0 z-50 w-80 transform transition-transform duration-300 ease-in-out
          lg:relative lg:translate-x-0
          ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <Sidebar />
      </div>

      {/* Overlay for mobile sidebar */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Main content area */}
      <div className="flex flex-1 flex-col">
        {/* Header with hamburger menu (mobile only) */}
        <header className="border-b bg-background px-4 py-3 lg:hidden">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            aria-label="Toggle sidebar"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </header>

        {/* Chat area */}
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  )
}
