'use client'

export default function LoadingIndicator() {
  return (
    <span className="inline-flex items-center gap-1">
      <span
        className="h-1.5 w-1.5 animate-bounce rounded-full bg-current"
        style={{ animationDelay: '0ms' }}
      />
      <span
        className="h-1.5 w-1.5 animate-bounce rounded-full bg-current"
        style={{ animationDelay: '150ms' }}
      />
      <span
        className="h-1.5 w-1.5 animate-bounce rounded-full bg-current"
        style={{ animationDelay: '300ms' }}
      />
    </span>
  )
}
