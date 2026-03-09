'use client'

interface PracticeSessionTabsProps {
  sessions: string[]
  activeSession: string
  onSessionChange: (session: string) => void
}

/**
 * Tab bar for switching between FP1/FP2/FP3 practice sessions.
 *
 * Uses the existing .session-tab / .session-tab-active CSS classes.
 * For sprint weekends with only FP1, shows a single label instead of tabs.
 */
export default function PracticeSessionTabs({
  sessions,
  activeSession,
  onSessionChange,
}: PracticeSessionTabsProps) {
  // Sprint weekend: single session, no tab selector needed
  if (sessions.length <= 1) {
    return (
      <div className="text-sm text-gray-400">
        Free Practice 1 <span className="text-gray-600">(Sprint Weekend — single practice session)</span>
      </div>
    )
  }

  return (
    <div className="flex gap-2">
      {sessions.map((session) => {
        const isActive = session === activeSession
        return (
          <button
            key={session}
            onClick={() => onSessionChange(session)}
            className={isActive ? 'session-tab-active' : 'session-tab'}
          >
            {session}
          </button>
        )
      })}
    </div>
  )
}
