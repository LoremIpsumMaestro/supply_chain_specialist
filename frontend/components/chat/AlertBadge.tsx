'use client'

import { AlertTriangle, AlertCircle, Info } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { Alert, AlertSeverity } from '@/types'

interface AlertBadgeProps {
  alert: Alert
  showDetails?: boolean
}

const severityConfig: Record<
  AlertSeverity,
  {
    icon: typeof AlertTriangle
    colorClass: string
    bgClass: string
    label: string
  }
> = {
  critical: {
    icon: AlertTriangle,
    colorClass: 'text-red-700',
    bgClass: 'bg-red-100 border-red-300',
    label: 'Critique',
  },
  warning: {
    icon: AlertCircle,
    colorClass: 'text-orange-700',
    bgClass: 'bg-orange-100 border-orange-300',
    label: 'Avertissement',
  },
  info: {
    icon: Info,
    colorClass: 'text-blue-700',
    bgClass: 'bg-blue-100 border-blue-300',
    label: 'Info',
  },
}

const alertTypeLabels: Record<string, string> = {
  negative_stock: 'Stock négatif',
  date_inconsistency: 'Dates incohérentes',
  negative_quantity: 'Quantité négative',
  lead_time_outlier: 'Délai anormal',
}

export function AlertBadge({ alert, showDetails = false }: AlertBadgeProps) {
  const config = severityConfig[alert.severity]
  const Icon = config.icon
  const typeLabel = alertTypeLabels[alert.alert_type] || alert.alert_type

  if (showDetails) {
    return (
      <div
        className={`p-3 rounded-lg border ${config.bgClass} ${config.colorClass} flex items-start gap-3`}
      >
        <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline" className="text-xs">
              {typeLabel}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {config.label}
            </Badge>
          </div>
          <p className="text-sm font-medium">{alert.message}</p>
          {alert.metadata && Object.keys(alert.metadata).length > 0 && (
            <div className="mt-2 text-xs opacity-75">
              {Object.entries(alert.metadata).map(([key, value]) => (
                <div key={key}>
                  <span className="font-medium">{key}:</span>{' '}
                  {JSON.stringify(value)}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium border ${config.bgClass} ${config.colorClass}`}
      title={alert.message}
    >
      <Icon className="h-3.5 w-3.5" />
      <span>{typeLabel}</span>
    </div>
  )
}

interface AlertListProps {
  alerts: Alert[]
}

export function AlertList({ alerts }: AlertListProps) {
  if (alerts.length === 0) {
    return null
  }

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-gray-700">
        Alertes détectées ({alerts.length})
      </h4>
      <div className="space-y-2">
        {alerts.map((alert) => (
          <AlertBadge key={alert.id} alert={alert} showDetails />
        ))}
      </div>
    </div>
  )
}
