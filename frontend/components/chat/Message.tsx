'use client'

import { formatDistanceToNow } from 'date-fns'
import { fr } from 'date-fns/locale'
import { User, Bot } from 'lucide-react'
import type { Message as MessageType } from '@/types'
import Citation from './Citation'

interface MessageProps {
  message: MessageType
}

export default function Message({ message }: MessageProps) {
  const isUser = message.role === 'user'
  const timeAgo = formatDistanceToNow(new Date(message.created_at), {
    addSuffix: true,
    locale: fr,
  })

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} max-w-[80%]`}>
        {/* Avatar */}
        <div
          className={`
            flex h-8 w-8 shrink-0 items-center justify-center rounded-full
            ${isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'}
          `}
        >
          {isUser ? (
            <User className="h-4 w-4" />
          ) : (
            <Bot className="h-4 w-4" />
          )}
        </div>

        {/* Message content */}
        <div className="flex flex-col gap-1">
          <div
            className={`
              rounded-lg p-4
              ${
                isUser
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }
            `}
          >
            <div className="whitespace-pre-wrap break-words text-sm">
              {message.content}
            </div>

            {/* Citations */}
            {message.citations && message.citations.length > 0 && (
              <div className="mt-3 space-y-1">
                {message.citations.map((citation, index) => (
                  <Citation key={index} citation={citation} />
                ))}
              </div>
            )}
          </div>

          {/* Timestamp */}
          <span
            className={`
              text-xs text-muted-foreground
              ${isUser ? 'text-right' : 'text-left'}
            `}
          >
            {timeAgo}
          </span>
        </div>
      </div>
    </div>
  )
}
