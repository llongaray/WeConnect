import { NavLink } from 'react-router-dom'
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { navCategories, filterNavCategories, type NavCategory, type NavItem } from '@/config/navigation'
import NavSection from '@/components/ui/NavSection'
import { cn } from '@/lib/cn'

interface SidebarProps {
  collapsed: boolean
  onToggleCollapse: () => void
  isSectionOpen: (category: NavCategory) => boolean
  onToggleSection: (categoryId: string) => void
  onNavigate?: () => void
  showCollapseToggle?: boolean
}

function roleFilterCategories(capabilities: ReturnType<typeof useAuthStore.getState>['capabilities']) {
  return filterNavCategories(navCategories, capabilities)
}

function NavItemLink({
  item,
  categoryId,
  collapsed,
  onNavigate,
}: {
  item: NavItem
  categoryId: string
  collapsed: boolean
  onNavigate?: () => void
}) {
  const Icon = item.icon

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      'group relative flex items-center rounded-lg text-sm transition-all duration-200',
      collapsed
        ? 'justify-center px-2 py-2.5 mx-auto w-10'
        : 'gap-3 px-3 py-2.5 hover:translate-x-0.5 hover:bg-wa-panel/80',
      isActive
        ? cn('font-medium', collapsed ? 'nav-item-active-collapsed' : 'nav-item-active')
        : 'text-gray-300',
    )

  return (
    <NavLink
      key={`${categoryId}-${item.label}`}
      to={item.to}
      end={item.end}
      className={linkClass}
      onClick={onNavigate}
      title={collapsed ? item.label : undefined}
    >
      <Icon className="w-4 h-4 shrink-0" />
      {!collapsed && <span className="truncate">{item.label}</span>}
      {collapsed && (
        <span className="sidebar-tooltip" role="tooltip">
          {item.label}
        </span>
      )}
    </NavLink>
  )
}

export default function Sidebar({
  collapsed,
  onToggleCollapse,
  isSectionOpen,
  onToggleSection,
  onNavigate,
  showCollapseToggle = true,
}: SidebarProps) {
  const capabilities = useAuthStore((s) => s.capabilities)
  const isMobileDrawer = Boolean(onNavigate)
  const railMode = collapsed && !isMobileDrawer

  const visibleCategories = roleFilterCategories(capabilities)
  const standaloneCategory = visibleCategories.find((cat) => cat.standalone)
  const sectionCategories = visibleCategories.filter((cat) => !cat.standalone)

  return (
    <aside
      className={cn(
        'bg-wa-panel border-r border-wa-border flex flex-col shrink-0 h-full transition-[width] duration-200',
        railMode ? 'w-[4.5rem]' : 'w-64',
      )}
    >
      <div
        className={cn(
          'border-b border-wa-border shrink-0',
          railMode ? 'p-2 flex justify-center' : 'p-4',
        )}
      >
        <div className={cn('flex items-center', railMode ? 'justify-center' : 'gap-3')}>
          <img
            src="/branding/logo-weconnect.png"
            alt="WeConnect"
            className={cn('shrink-0', railMode ? 'h-8 w-auto' : 'h-9 w-auto')}
          />
          {!railMode && (
            <div className="min-w-0 flex-1">
              <h1 className="text-base font-bold text-wa-green truncate">WeConnect</h1>
              <p className="text-[10px] text-wa-muted">Aray Soluções Tecnológicas</p>
            </div>
          )}
        </div>
      </div>

      <nav className={cn('flex-1 overflow-y-auto overflow-x-hidden', railMode ? 'p-2' : 'p-3')}>
        {standaloneCategory?.items.map((item) => (
          <div key={item.to} className={cn('mb-3', railMode && 'mb-2')}>
            <NavItemLink
              item={item}
              categoryId={standaloneCategory.id}
              collapsed={railMode}
              onNavigate={onNavigate}
            />
          </div>
        ))}

        {sectionCategories.map((category) => (
          <NavSection
            key={category.id}
            sectionId={category.id}
            label={category.label}
            open={isSectionOpen(category)}
            onToggle={() => onToggleSection(category.id)}
            collapsible={category.collapsible !== false && category.items.length > 1}
            collapsedSidebar={railMode}
          >
            {category.items.map((item) => (
              <NavItemLink
                key={`${category.id}-${item.label}`}
                item={item}
                categoryId={category.id}
                collapsed={railMode}
                onNavigate={onNavigate}
              />
            ))}
          </NavSection>
        ))}
      </nav>

      {showCollapseToggle && !isMobileDrawer && (
        <div className={cn('border-t border-wa-border shrink-0', railMode ? 'p-2' : 'p-3')}>
          <button
            type="button"
            onClick={onToggleCollapse}
            title={railMode ? 'Expandir menu' : 'Recolher menu'}
            className={cn(
              'flex items-center rounded-lg text-wa-muted hover:text-white hover:bg-wa-dark/60 transition-colors',
              railMode ? 'justify-center w-10 h-10 mx-auto' : 'gap-2 w-full px-3 py-2.5 text-sm',
            )}
          >
            {railMode ? (
              <PanelLeftOpen className="w-4 h-4" />
            ) : (
              <>
                <PanelLeftClose className="w-4 h-4 shrink-0" />
                <span>Recolher menu</span>
              </>
            )}
          </button>
        </div>
      )}
    </aside>
  )
}

export { roleFilterCategories }
