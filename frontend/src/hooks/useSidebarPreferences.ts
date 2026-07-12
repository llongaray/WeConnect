import { useCallback, useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { categoryContainsPath, navCategories, type NavCategory } from '@/config/navigation'

const COLLAPSED_KEY = 'weconnect.sidebar.collapsed'
const SECTIONS_KEY = 'weconnect.sidebar.sections'

function readCollapsed(): boolean {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === 'true'
  } catch {
    return false
  }
}

function readSections(): Record<string, boolean> {
  try {
    const raw = localStorage.getItem(SECTIONS_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as Record<string, boolean>
    return typeof parsed === 'object' && parsed !== null ? parsed : {}
  } catch {
    return {}
  }
}

function defaultSectionState(categories: NavCategory[]): Record<string, boolean> {
  const state: Record<string, boolean> = {}
  for (const cat of categories) {
    if (cat.standalone) continue
    state[cat.id] = cat.defaultOpen ?? true
  }
  return state
}

export function useSidebarPreferences(visibleCategories: NavCategory[]) {
  const { pathname } = useLocation()
  const [collapsed, setCollapsed] = useState(readCollapsed)
  const [sections, setSections] = useState<Record<string, boolean>>(() => {
    const stored = readSections()
    const defaults = defaultSectionState(navCategories)
    return { ...defaults, ...stored }
  })

  const activeCategoryId = useMemo(
    () => visibleCategories.find((cat) => categoryContainsPath(cat, pathname))?.id ?? null,
    [visibleCategories, pathname],
  )

  // Abre automaticamente a seção da rota ativa
  useEffect(() => {
    if (!activeCategoryId || collapsed) return
    setSections((prev) => {
      if (prev[activeCategoryId]) return prev
      return { ...prev, [activeCategoryId]: true }
    })
  }, [activeCategoryId, collapsed])

  useEffect(() => {
    try {
      localStorage.setItem(COLLAPSED_KEY, String(collapsed))
    } catch {
      /* storage indisponível */
    }
  }, [collapsed])

  useEffect(() => {
    try {
      localStorage.setItem(SECTIONS_KEY, JSON.stringify(sections))
    } catch {
      /* storage indisponível */
    }
  }, [sections])

  const toggleCollapsed = useCallback(() => {
    setCollapsed((v) => !v)
  }, [])

  const toggleSection = useCallback((categoryId: string) => {
    setSections((prev) => ({ ...prev, [categoryId]: !prev[categoryId] }))
  }, [])

  const isSectionOpen = useCallback(
    (category: NavCategory) => {
      if (category.standalone) return true
      if (category.collapsible === false) return true
      return sections[category.id] ?? category.defaultOpen ?? true
    },
    [sections],
  )

  return {
    collapsed,
    toggleCollapsed,
    toggleSection,
    isSectionOpen,
  }
}
