'use client'

import { useCallback } from 'react'
import { QualifyingSessionPart } from '@/../../packages/models/src/types'
import { getQualifyingSessionParts } from '@/lib/formatters'

interface QualifyingSessionTabsProps {
  /** Currently selected session part */
  selected: QualifyingSessionPart
  /** Callback when session part changes */
  onChange: (session: QualifyingSessionPart) => void
  /** Whether this is a sprint weekend (shows SQ1/SQ2/SQ3 instead of Q1/Q2/Q3) */
  isSprintWeekend?: boolean
  /** Sessions that have available data (others will be disabled) */
  availableSessions?: QualifyingSessionPart[]
  /** Optional className for custom styling */
  className?: string
}

/**
 * Tab component for switching between qualifying session parts.
 * Supports both traditional (Q1/Q2/Q3) and sprint (SQ1/SQ2/SQ3) formats.
 */
export function QualifyingSessionTabs({
  selected,
  onChange,
  isSprintWeekend = false,
  availableSessions,
  className = '',
}: QualifyingSessionTabsProps) {
  const sessionParts = getQualifyingSessionParts(isSprintWeekend)

  const handleKeyDown = useCallback((
    event: React.KeyboardEvent,
    currentIndex: number
  ) => {
    let newIndex = currentIndex

    switch (event.key) {
      case 'ArrowLeft':
        newIndex = currentIndex > 0 ? currentIndex - 1 : sessionParts.length - 1
        break
      case 'ArrowRight':
        newIndex = currentIndex < sessionParts.length - 1 ? currentIndex + 1 : 0
        break
      case 'Home':
        newIndex = 0
        break
      case 'End':
        newIndex = sessionParts.length - 1
        break
      default:
        return
    }

    event.preventDefault()
    const newSession = sessionParts[newIndex]
    
    // Skip disabled tabs
    if (!availableSessions || availableSessions.includes(newSession)) {
      onChange(newSession)
    }
  }, [sessionParts, availableSessions, onChange])

  const isSessionAvailable = (session: QualifyingSessionPart) => {
    if (!availableSessions) return true
    return availableSessions.includes(session)
  }

  return (
    <div 
      className={`flex items-center ${className}`}
      role="tablist"
      aria-label={isSprintWeekend ? 'Sprint Qualifying sessions' : 'Qualifying sessions'}
    >
      {sessionParts.map((session, index) => {
        const isActive = selected === session
        const isAvailable = isSessionAvailable(session)

        return (
          <button
            key={session}
            onClick={() => isAvailable && onChange(session)}
            onKeyDown={(e) => handleKeyDown(e, index)}
            disabled={!isAvailable}
            role="tab"
            aria-selected={isActive}
            aria-controls={`${session.toLowerCase()}-panel`}
            tabIndex={isActive ? 0 : -1}
            className={`
              session-tab
              ${isActive ? 'session-tab-active' : ''}
              ${!isAvailable ? 'opacity-40 cursor-not-allowed' : ''}
              focus-ring
            `}
          >
            {session}
          </button>
        )
      })}
      
      {/* Sprint indicator badge */}
      {isSprintWeekend && (
        <span 
          className="ml-3 rounded-full bg-f1red/20 px-2 py-0.5 text-xs font-medium text-f1red"
          title="Sprint Weekend Format"
        >
          Sprint
        </span>
      )}
    </div>
  )
}

/**
 * Compact version for use in tight spaces
 */
export function QualifyingSessionTabsCompact({
  selected,
  onChange,
  isSprintWeekend = false,
}: Pick<QualifyingSessionTabsProps, 'selected' | 'onChange' | 'isSprintWeekend'>) {
  const sessionParts = getQualifyingSessionParts(isSprintWeekend)

  return (
    <div 
      className="inline-flex rounded-lg border border-f1gray p-1"
      role="tablist"
      aria-label={isSprintWeekend ? 'Sprint Qualifying sessions' : 'Qualifying sessions'}
    >
      {sessionParts.map((session) => {
        const isActive = selected === session

        return (
          <button
            key={session}
            onClick={() => onChange(session)}
            role="tab"
            aria-selected={isActive}
            className={`
              px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200
              focus-ring
              ${isActive 
                ? 'bg-f1red text-white shadow-glow-red-sm' 
                : 'text-gray-400 hover:text-white hover:bg-f1gray/50'
              }
            `}
          >
            {session}
          </button>
        )
      })}
    </div>
  )
}
