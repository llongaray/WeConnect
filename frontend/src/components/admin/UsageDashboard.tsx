import { Radio, Users, UsersRound } from 'lucide-react'
import type { CompanyUsage } from '@/types'
import { cn } from '@/lib/cn'

type UsageMetric = 'users' | 'teams' | 'channels'

interface UsageDashboardProps {
  usage?: CompanyUsage
  only?: UsageMetric
  className?: string
}

function getBarColor(percent: number) {
  if (percent >= 100) return 'bg-red-500'
  if (percent >= 80) return 'bg-amber-400'
  return 'bg-wa-green'
}

function getTextColor(percent: number) {
  if (percent >= 100) return 'text-red-300'
  if (percent >= 80) return 'text-amber-300'
  return 'text-wa-green'
}

function formatPercent(current: number, max: number) {
  if (max <= 0) return 0
  return Math.min(100, Math.round((current / max) * 100))
}

export default function UsageDashboard({ usage, only, className }: UsageDashboardProps) {
  if (!usage) return null

  const userCurrent = usage.supervisors + usage.atendentes
  const userMax = usage.limits.max_supervisors + usage.limits.max_atendentes

  const metrics = [
    {
      id: 'users' as const,
      label: 'Usuários',
      hint: `${usage.supervisors} supervisores · ${usage.atendentes} atendentes`,
      current: userCurrent,
      max: userMax,
      icon: Users,
    },
    {
      id: 'teams' as const,
      label: 'Equipes',
      hint: 'Equipes ativas',
      current: usage.teams,
      max: usage.limits.max_teams,
      icon: UsersRound,
    },
    {
      id: 'channels' as const,
      label: 'Canais',
      hint: 'Canais WhatsApp',
      current: usage.channels,
      max: usage.limits.max_channels,
      icon: Radio,
    },
  ].filter((metric) => !only || metric.id === only)

  return (
    <div
      className={cn(
        'grid gap-3 mb-6',
        metrics.length === 1 ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-3',
        className,
      )}
    >
      {metrics.map((metric) => {
        const Icon = metric.icon
        const percent = formatPercent(metric.current, metric.max)
        const remaining = Math.max(metric.max - metric.current, 0)

        return (
          <div
            key={metric.id}
            className="rounded-xl border border-wa-border bg-gradient-to-br from-wa-panel to-wa-dark/60 p-4"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-wa-green/15 flex items-center justify-center shrink-0">
                <Icon className="w-5 h-5 text-wa-green" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-2">
                  <p className="text-sm font-medium text-white">{metric.label}</p>
                  <p className={cn('text-lg font-semibold tabular-nums', getTextColor(percent))}>
                    {metric.current}<span className="text-sm text-wa-muted font-normal">/{metric.max}</span>
                  </p>
                </div>
                <p className="text-xs text-wa-muted mt-0.5">{metric.hint}</p>
              </div>
            </div>

            <div className="mt-3">
              <div className="flex justify-between text-[11px] text-wa-muted mb-1">
                <span>{percent}% em uso</span>
                <span>{remaining} disponível(is)</span>
              </div>
              <div className="h-1.5 rounded-full bg-wa-dark overflow-hidden">
                <div
                  className={cn('h-full rounded-full transition-all duration-300', getBarColor(percent))}
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
