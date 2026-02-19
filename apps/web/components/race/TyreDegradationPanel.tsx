'use client'

import { useState, useMemo, useEffect, useCallback, useRef } from 'react'
import { useRouter, useSearchParams, usePathname } from 'next/navigation'
import { useTyreDegradationQuery } from '@/lib/hooks/useTyreDegradationQuery'
import { useVisibility } from '@/lib/hooks/useVisibility'
import AnalysisModeToggle from './AnalysisModeToggle'
import DriverChipSelector from './DriverChipSelector'
import CompoundTabs from './CompoundTabs'
import DegradationScatter from './DegradationScatter'

interface TyreDegradationPanelProps {
  sessionId: string | undefined
  fuelEffect?: number
}

/**
 * Phase 3: Tyre Degradation Analysis Panel
 *
 * Orchestrates mode toggle, driver selector, compound tabs,
 * and the scatter + wear rate chart composition.
 *
 * State management:
 * - mode: 'driver' | 'team' — triggers backend refetch (persisted as ?tdMode)
 * - selectedIdentifiers: string[] — client-side filter (persisted as ?tdDrivers)
 * - activeCompound: string | null — client-side tab switch (persisted as ?tdCompound)
 *
 * Deferred loading: useVisibility + IntersectionObserver delays data fetching
 * until the panel approaches the viewport (200px threshold).
 */
export default function TyreDegradationPanel({
  sessionId,
  fuelEffect,
}: TyreDegradationPanelProps) {
  const { containerRef, isVisible } = useVisibility()

  // ── URL state persistence ──
  const router = useRouter()
  const searchParams = useSearchParams()
  const pathname = usePathname()

  // Read persisted state from URL (with defaults)
  const urlMode = (searchParams.get('tdMode') as 'driver' | 'team') || 'driver'
  const urlDrivers = searchParams.get('tdDrivers')?.split(',').filter(Boolean) || []
  const urlCompound = searchParams.get('tdCompound') || null

  const [mode, setMode] = useState<'driver' | 'team'>(urlMode)
  const [selectedIdentifiers, setSelectedIdentifiers] = useState<string[]>(urlDrivers)
  const [activeCompound, setActiveCompound] = useState<string | null>(urlCompound)
  const [userHasFiltered, setUserHasFiltered] = useState(urlDrivers.length > 0)
  const [infoOpen, setInfoOpen] = useState(false)
  const prevSessionIdRef = useRef<string | undefined>(undefined)

  const { data, isLoading, isError, error, isPlaceholderData } = useTyreDegradationQuery(
    sessionId,
    fuelEffect,
    mode,
    isVisible,
  )

  // Extract all identifiers from the response
  const allIdentifiers = useMemo(() => {
    if (!data) return []
    const ids = new Set<string>()
    for (const compound of data.compounds) {
      for (const driver of compound.drivers) {
        ids.add(driver.identifier)
      }
    }
    return Array.from(ids).sort()
  }, [data])

  // ── URL update helper ──
  // Writes tyre-degradation-specific params without affecting season/round/etc.
  const updateTyreDegURL = useCallback(
    (newMode: string, newDrivers: string[], newCompound: string | null) => {
      const params = new URLSearchParams(searchParams.toString())
      params.set('tdMode', newMode)
      // Only persist driver selection when it's a subset (all-selected is the default)
      if (newDrivers.length > 0 && newDrivers.length < allIdentifiers.length) {
        params.set('tdDrivers', newDrivers.join(','))
      } else {
        params.delete('tdDrivers')
      }
      if (newCompound) {
        params.set('tdCompound', newCompound)
      } else {
        params.delete('tdCompound')
      }
      router.replace(`${pathname}?${params.toString()}`, { scroll: false })
    },
    [searchParams, pathname, router, allIdentifiers.length]
  )

  // ── State change handlers ──

  const handleModeChange = useCallback(
    (newMode: 'driver' | 'team') => {
      setMode(newMode)
      setUserHasFiltered(false)
      // Identifiers change between driver/team — will be re-populated by useEffect below
      setSelectedIdentifiers([])
      updateTyreDegURL(newMode, [], activeCompound)
    },
    [activeCompound, updateTyreDegURL]
  )

  const handleSelectionChange = useCallback(
    (selected: string[]) => {
      setSelectedIdentifiers(selected)
      setUserHasFiltered(true)
      updateTyreDegURL(mode, selected, activeCompound)
    },
    [mode, activeCompound, updateTyreDegURL]
  )

  const handleCompoundChange = useCallback(
    (compound: string) => {
      setActiveCompound(compound)
      updateTyreDegURL(mode, selectedIdentifiers, compound)
    },
    [mode, selectedIdentifiers, updateTyreDegURL]
  )

  // ── Auto-select and validation effects ──

  // When data arrives: auto-select all if user hasn't manually filtered,
  // or validate persisted drivers still exist in current session
  useEffect(() => {
    if (allIdentifiers.length > 0) {
      if (userHasFiltered && selectedIdentifiers.length > 0) {
        // Validate persisted drivers exist in current data
        const valid = selectedIdentifiers.filter((id) => allIdentifiers.includes(id))
        if (valid.length === 0) {
          setSelectedIdentifiers(allIdentifiers)
          setUserHasFiltered(false)
        } else if (valid.length !== selectedIdentifiers.length) {
          setSelectedIdentifiers(valid)
        }
      } else if (!userHasFiltered) {
        setSelectedIdentifiers(allIdentifiers)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allIdentifiers])

  // Set initial active compound from data
  useEffect(() => {
    if (data && data.compoundOrder.length > 0 && !activeCompound) {
      setActiveCompound(data.compoundOrder[0])
    }
  }, [data, activeCompound])

  // Reset active compound when session changes (new GP) — skip on initial mount
  // to respect URL-persisted compound
  useEffect(() => {
    if (data && data.compoundOrder.length > 0) {
      if (prevSessionIdRef.current !== undefined && prevSessionIdRef.current !== data.sessionId) {
        setActiveCompound(data.compoundOrder[0])
      }
      prevSessionIdRef.current = data.sessionId
    }
  }, [data?.sessionId, data])

  // Get the active compound data, filtered by selected identifiers
  const activeCompoundData = useMemo(() => {
    if (!data || !activeCompound) return null
    const compound = data.compounds.find((c) => c.compound === activeCompound)
    if (!compound) return null
    return {
      ...compound,
      drivers: compound.drivers.filter((d) =>
        selectedIdentifiers.includes(d.identifier)
      ),
    }
  }, [data, activeCompound, selectedIdentifiers])

  // ── Single return: all states inside one div with ref ──

  const showSkeleton = !isVisible || (isLoading && !data)
  const showError = !showSkeleton && (isError)
  const showEmpty = !showSkeleton && !showError && (!data || data.compounds.length === 0)
  const showContent = !showSkeleton && !showError && !showEmpty && data

  return (
    <div ref={containerRef} className="content-defer">
      {showSkeleton && (
        <div className="card-panel animate-pulse">
          <div className="h-5 w-56 bg-f1gray/30 rounded mb-4" />
          <div className="flex gap-2 mb-4">
            <div className="h-8 w-36 bg-f1gray/20 rounded" />
            <div className="h-8 w-36 bg-f1gray/20 rounded" />
          </div>
          <div className="h-[400px] bg-f1gray/10 rounded-lg" />
        </div>
      )}

      {showError && (
        <div className="card-panel">
          <h3 className="text-base font-semibold text-white mb-2">
            Tyre Degradation Analysis
          </h3>
          <div className="flex items-center justify-center h-48 text-gray-500">
            <div className="text-center">
              <p className="text-sm">Unable to load tyre degradation data</p>
              <p className="text-xs mt-1 text-gray-600">
                {error instanceof Error ? error.message : 'Unknown error'}
              </p>
            </div>
          </div>
        </div>
      )}

      {showEmpty && (
        <div className="card-panel">
          <h3 className="text-base font-semibold text-white mb-2">
            Tyre Degradation Analysis
          </h3>
          <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
            No tyre degradation data available for this session
          </div>
        </div>
      )}

      {showContent && (
        <div
          className={`card-panel transition-opacity duration-300 ${
            isPlaceholderData ? 'opacity-60' : 'opacity-100'
          }`}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-white">
              Tyre Degradation Analysis
            </h3>
          </div>

          {/* Controls: Mode toggle + Driver/Team selector */}
          <div className="space-y-3 mb-4">
            <AnalysisModeToggle mode={mode} onModeChange={handleModeChange} />
            <DriverChipSelector
              identifiers={allIdentifiers}
              selectedIdentifiers={selectedIdentifiers}
              onSelectionChange={handleSelectionChange}
              mode={mode}
            />
          </div>

          {/* Compound tabs */}
          <CompoundTabs
            compounds={data.compoundOrder}
            activeCompound={activeCompound ?? data.compoundOrder[0]}
            onCompoundChange={handleCompoundChange}
          />

          {/* Active compound chart section */}
          <div className="mt-4">
            {activeCompoundData ? (
              <DegradationScatter
                compound={activeCompoundData.compound}
                drivers={activeCompoundData.drivers}
                mode={mode}
              />
            ) : (
              <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
                Select a compound to view degradation data
              </div>
            )}
          </div>

          {/* How to Read — collapsible guide (below chart, matching RacePaceBoxPlot pattern) */}
          <button
            onClick={() => setInfoOpen(!infoOpen)}
            className="flex items-center gap-2 mt-4 text-sm text-gray-500 hover:text-gray-300 transition-colors"
            type="button"
            aria-expanded={infoOpen}
          >
            <span
              className={`inline-block transition-transform duration-200 ${infoOpen ? 'rotate-90' : ''}`}
            >
              &#9656;
            </span>
            How to read this chart
          </button>
          {infoOpen && (
            <div className="mt-3 rounded-lg border border-white/10 bg-white/[0.02] p-4 space-y-4">
              {/* Scatter plot anatomy */}
              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Understanding the Scatter Plot
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    <span className="text-gray-400 font-medium">Each dot</span> represents
                    one racing lap, plotted against tyre age (laps since the most recent
                    pit stop). The y-axis shows fuel-adjusted lap time in seconds &mdash;
                    lower is faster.
                  </p>
                  <p>
                    As tyre age increases, lap times typically rise as grip degrades.
                    Dots from the same stint cluster together; gaps between clusters
                    indicate pit stops.
                  </p>
                </div>
              </div>

              {/* Trend lines */}
              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Trend Lines and Degradation Rate
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    <span className="text-gray-400 font-medium">Trend lines</span> show
                    a linear regression fit through each driver&apos;s data points. The
                    gradient (slope) is the degradation rate, measured in seconds per lap.
                  </p>
                  <p>
                    A steeper upward slope means faster tyre wear &mdash; the driver is
                    losing more time per lap as the stint progresses. A flatter line
                    indicates better tyre management.
                  </p>
                  <p className="text-gray-500/80">
                    Stints with fewer than 7 usable laps do not show a trend line, as
                    the sample is too small for a reliable regression.
                  </p>
                </div>
              </div>

              {/* Wear rate bars */}
              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Wear Rate Bars
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    <span className="text-gray-400 font-medium">Bars</span> are sorted
                    by degradation rate, with the highest (worst tyre management) at the
                    top. The value represents seconds lost per lap due to tyre wear. A
                    negative value means lap times improved over the stint, typically due
                    to track evolution outweighing tyre degradation.
                  </p>
                  <p>
                    Drivers or teams without sufficient data for regression are omitted
                    from this chart.
                  </p>
                </div>
              </div>

              {/* Driver vs Team mode */}
              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Driver vs Team Mode
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    <span className="text-gray-400 font-medium">Driver mode</span> compares
                    individual drivers, each with their own scatter points and regression
                    line.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Team mode</span> pools
                    both drivers&apos; laps to produce a team-level degradation view.
                    This reveals the team&apos;s overall tyre strategy rather than
                    individual variation.
                  </p>
                </div>
              </div>

              {/* Fuel correction */}
              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Fuel Correction
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    <span className="text-gray-400 font-medium">When enabled</span>,
                    each lap time is adjusted to remove the fuel-mass penalty, isolating
                    the tyre degradation trend. Without this correction, early-race laps
                    appear slower (heavier fuel load) and the true tyre wear is masked.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">When disabled</span>,
                    raw lap times are shown as recorded on track. Trend lines may appear
                    flat or downward-sloping because the fuel burn benefit offsets tyre
                    degradation.
                  </p>
                </div>
              </div>

              {/* Data filtering */}
              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Data Filtering
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    The first 2 laps of each stint are excluded from the regression line
                    (tyre warm-up period produces non-representative times). In-laps,
                    out-laps, safety car laps, and anomalous laps are excluded from
                    both the scatter plot and regression.
                  </p>
                </div>
              </div>

              {/* Interaction tips */}
              <div>
                <h4 className="text-sm font-semibold text-gray-300 mb-2">
                  Interacting with the Chart
                </h4>
                <div className="text-sm text-gray-500 space-y-1.5">
                  <p>
                    <span className="text-gray-400 font-medium">Hover</span> over any
                    dot for per-lap details: driver name, team, tyre age, fuel-adjusted
                    time, raw time, lap number, and stint number.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Driver chips</span> above
                    the chart filter which drivers are shown. Use &ldquo;Select
                    All&rdquo; and &ldquo;Clear&rdquo; for quick bulk selection.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Compound tabs</span> switch
                    between Hard, Medium, and Soft tyre views.
                  </p>
                  <p>
                    <span className="text-gray-400 font-medium">Scroll</span> to zoom,
                    drag to pan, double-click to reset the view.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
