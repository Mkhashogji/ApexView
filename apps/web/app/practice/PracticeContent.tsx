'use client'

import { useState, useMemo } from 'react'
import { useSearchParams } from 'next/navigation'
import { usePracticeSessionsQuery } from '@/lib/hooks/usePracticeSessionsQuery'
import { getRaceFuelEffect } from '@/data/tracks/race-lookup'
import PracticeSessionTabs from '@/components/practice/PracticeSessionTabs'
import LongRunPacePanel from '@/components/practice/LongRunPacePanel'
import ShortRunPanel from '@/components/practice/ShortRunPanel'
import SectorMapPanel from '@/components/practice/SectorMapPanel'
import SectorAnalysisPanel from '@/components/practice/SectorAnalysisPanel'
import SessionProgressionPanel from '@/components/practice/SessionProgressionPanel'
import { ErrorBoundary } from '@/components/race/ErrorBoundary'

const DEFAULT_SEASON = 2025
const DEFAULT_ROUND = 24

/**
 * Practice Analysis Page Content — Client Component
 *
 * Orchestrates data fetching, state management, and panel rendering
 * for the Practice page. Must be wrapped in Suspense because it uses
 * useSearchParams().
 */
export default function PracticeContent() {
  const searchParams = useSearchParams()

  // Parse URL state
  const season = parseInt(searchParams.get('season') || String(DEFAULT_SEASON))
  const round = parseInt(searchParams.get('round') || String(DEFAULT_ROUND))

  // Session state: "FP1", "FP2", or "FP3"
  const [selectedSession, setSelectedSession] = useState('FP2')

  // Fuel correction state (default OFF for practice — fuel loads unknown)
  const [fuelCorrected, setFuelCorrected] = useState(false)

  // Fetch available sessions for this weekend
  const { data: sessionsData } = usePracticeSessionsQuery(season, round)
  const availableSessions = sessionsData?.sessions ?? ['FP1', 'FP2', 'FP3']

  // Adjust selection if chosen session is not available (sprint weekend)
  const activeSession = useMemo(() => {
    if (availableSessions.includes(selectedSession)) return selectedSession
    return availableSessions[0] ?? 'FP1'
  }, [selectedSession, availableSessions])

  // Derive session ID for API calls (e.g. "2025_24_FP2")
  const sessionId = `${season}_${round}_${activeSession}`

  // Get circuit-specific fuel effect from lightweight lookup
  const fuelEffectPerKg = getRaceFuelEffect(round)
  const fuelEffect = fuelCorrected ? fuelEffectPerKg : 0

  return (
    <div className="flex flex-col lg:flex-row gap-6">
      {/* Sidebar */}
      <aside className="w-full lg:w-72 lg:flex-shrink-0 lg:sticky lg:top-16 lg:self-start lg:max-h-[calc(100vh-5rem)] lg:overflow-y-auto">
        <div className="card-panel space-y-6">
          {/* Session Info */}
          <div>
            <h3 className="text-xs font-medium uppercase tracking-wide text-gray-400 mb-2">
              Session
            </h3>
            <p className="text-sm text-gray-300">{activeSession}</p>
          </div>

          {/* Fuel Correction Toggle */}
          <div>
            <h3 className="text-xs font-medium uppercase tracking-wide text-gray-400 mb-3">
              Pace Correction
            </h3>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={fuelCorrected}
                onChange={(e) => setFuelCorrected(e.target.checked)}
                className="rounded border-gray-600 bg-gray-700 text-f1red
                           focus:ring-f1red focus:ring-offset-0"
              />
              <span className="text-sm text-gray-300">
                Approximate fuel correction
              </span>
            </label>
            <p className="text-xs text-gray-500 mt-2">
              {fuelCorrected
                ? 'Showing pace with estimated fuel correction (~1.6 kg/lap burn rate)'
                : 'Showing raw lap times as recorded on track'}
            </p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 min-w-0 space-y-6">
        {/* Session Tabs */}
        <PracticeSessionTabs
          sessions={availableSessions}
          activeSession={activeSession}
          onSessionChange={setSelectedSession}
        />

        {/* Long Run Pace Panel (Phase 1) */}
        <ErrorBoundary key={`longrun-${sessionId}`} panelName="Long Run Pace">
          <LongRunPacePanel
            sessionId={sessionId}
            fuelEffect={fuelEffect}
            fuelCorrected={fuelCorrected}
          />
        </ErrorBoundary>

        {/* Short Run / Best Lap Panel (Phase 2) */}
        <ErrorBoundary key={`shortrun-${sessionId}`} panelName="Short Run / Best Lap">
          <ShortRunPanel
            sessionId={sessionId}
            fuelEffect={fuelEffect}
          />
        </ErrorBoundary>

        {/* Circuit Map with Sector Highlighting (Phase 2b) */}
        <ErrorBoundary key={`sectormap-${sessionId}`} panelName="Circuit Map">
          <SectorMapPanel round={round} sessionId={sessionId} />
        </ErrorBoundary>

        {/* Sector Analysis Panel */}
        <ErrorBoundary key={`sectors-${sessionId}`} panelName="Sector Analysis">
          <SectorAnalysisPanel sessionId={sessionId} />
        </ErrorBoundary>

        {/* Session Progression Panel (Phase 3) — weekend-level, not session-specific */}
        <ErrorBoundary key={`progression-${season}-${round}`} panelName="Session Progression">
          <SessionProgressionPanel year={season} round={round} />
        </ErrorBoundary>
      </main>
    </div>
  )
}
