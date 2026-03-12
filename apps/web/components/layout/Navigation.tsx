'use client'

import { Suspense, useCallback } from 'react'
import { usePathname } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { fetchRacePace } from '@/lib/api'
import { queryKeys } from '@/lib/hooks/queryKeys'
import { RaceWeekendSelector } from './RaceWeekendSelector'

/**
 * Navigation links configuration
 */
const navLinks = [
  { href: '/', label: 'Home' },
  { href: '/qualifying', label: 'Qualifying' },
  { href: '/race', label: 'Race' },
  { href: '/practice', label: 'Practice' },
  { href: '/track', label: 'Track Intelligence' },
]

/**
 * Main navigation component with active state indicators.
 * Uses red underline to show current page.
 */
/** Default session for prefetch — matches RaceContent DEFAULT_SEASON/DEFAULT_ROUND */
const PREFETCH_SESSION = '2025_24_Race'
/** Default fuel effect for prefetch (general default 0.032) */
const PREFETCH_FUEL_EFFECT = 0.032

export function Navigation() {
  const pathname = usePathname()
  const queryClient = useQueryClient()

  /**
   * Check if a nav link is currently active
   */
  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === '/'
    }
    return pathname.startsWith(href)
  }

  /**
   * Prefetch race pace data on Race link hover.
   * Uses hardcoded default session to avoid useSearchParams hydration issues.
   * If the user has navigated to a different GP, this prefetch won't match,
   * but that's acceptable for a hover-optimisation.
   */
  const handleRaceHover = useCallback(() => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.race.pace(PREFETCH_SESSION, PREFETCH_FUEL_EFFECT),
      queryFn: () => fetchRacePace(PREFETCH_SESSION, PREFETCH_FUEL_EFFECT),
      staleTime: Infinity,
    })
  }, [queryClient])

  return (
    <nav 
      className="sticky top-0 z-50 border-b border-f1gray bg-f1dark/95 backdrop-blur supports-[backdrop-filter]:bg-f1dark/60"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center">
            <Link
              href="/"
              className="font-heading text-2xl font-bold uppercase tracking-tight text-white transition-opacity hover:opacity-80"
            >
              Apex<span className="text-f1red">View</span>
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            {navLinks.map((link) => {
              const active = isActive(link.href)
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`
                    relative px-4 py-2 text-sm font-medium transition-colors duration-200
                    focus-ring rounded-md
                    ${active 
                      ? 'text-white' 
                      : 'text-gray-400 hover:text-white hover:bg-f1gray/50'
                    }
                  `}
                  aria-current={active ? 'page' : undefined}
                  onMouseEnter={link.href === '/race' ? handleRaceHover : undefined}
                >
                  {link.label}
                  {/* Active indicator - red underline with glow */}
                  {active && (
                    <span 
                      className="absolute bottom-0 left-2 right-2 h-0.5 bg-f1red shadow-glow-red-sm"
                      aria-hidden="true"
                    />
                  )}
                </Link>
              )
            })}
          </div>

          {/* Race Weekend Selector */}
          <Suspense fallback={
            <div className="h-9 w-40 rounded-md bg-f1gray/30 animate-pulse" />
          }>
            <RaceWeekendSelector />
          </Suspense>
        </div>
      </div>
    </nav>
  )
}
