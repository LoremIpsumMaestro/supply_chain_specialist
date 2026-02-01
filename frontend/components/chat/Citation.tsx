'use client'

import { FileText } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { CitationMetadata } from '@/types'

interface CitationProps {
  citation: CitationMetadata
}

export default function Citation({ citation }: CitationProps) {
  const formatCitation = () => {
    // Excel citation with sheet and cell reference
    if (citation.sheet_name && citation.cell_ref) {
      return `${citation.filename} | ${citation.sheet_name} | ${citation.cell_ref}`
    }

    // PDF/Word/PowerPoint with page number
    if (citation.page) {
      return `${citation.filename} | Page ${citation.page}`
    }

    // Fallback to filename only
    return citation.filename
  }

  const formatTemporalContext = () => {
    const tc = citation.temporal_context
    if (!tc) return null

    const parts: string[] = []

    // Format date
    if (tc.date) {
      try {
        const date = new Date(tc.date)
        parts.push(`📅 ${date.toLocaleDateString('fr-FR')}`)
      } catch {
        parts.push(`📅 ${tc.date}`)
      }
    }

    // Format variation
    if (tc.vs_previous_month) {
      parts.push(tc.vs_previous_month)
    }

    // Format seasonal pattern
    if (tc.seasonal_pattern) {
      parts.push(tc.seasonal_pattern)
    }

    // Format lead time
    if (tc.lead_time_days !== undefined) {
      parts.push(`Délai: ${tc.lead_time_days}j`)
    }

    return parts.length > 0 ? parts.join(' • ') : null
  }

  const getTooltipContent = () => {
    const parts: string[] = []

    parts.push(`Fichier: ${citation.filename}`)

    if (citation.sheet_name) {
      parts.push(`Feuille: ${citation.sheet_name}`)
    }

    if (citation.cell_ref) {
      parts.push(`Cellule: ${citation.cell_ref}`)
    }

    if (citation.page) {
      parts.push(`Page: ${citation.page}`)
    }

    if (citation.row !== undefined) {
      parts.push(`Ligne: ${citation.row}`)
    }

    if (citation.column !== undefined) {
      parts.push(`Colonne: ${citation.column}`)
    }

    if (citation.value) {
      parts.push(`Valeur: ${citation.value}`)
    }

    return parts.join('\n')
  }

  const temporalInfo = formatTemporalContext()

  return (
    <div className="inline-flex flex-col gap-1">
      <Badge
        variant="outline"
        className="inline-flex items-center gap-1.5 text-xs"
        title={getTooltipContent()}
      >
        <FileText className="h-3 w-3" />
        <span>{formatCitation()}</span>
      </Badge>

      {temporalInfo && (
        <span className="text-xs text-gray-600 ml-1">
          {temporalInfo}
        </span>
      )}
    </div>
  )
}
