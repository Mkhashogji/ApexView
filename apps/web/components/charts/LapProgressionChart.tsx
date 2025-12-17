'use client'

import { Lap } from '@/../../packages/models/src/types'
import { getTeamColor, getDriverInfo } from '@/lib/drivers'
import { formatLapTime } from '@/lib/formatters'
import dynamic from 'next/dynamic'
import { useMemo } from 'react'

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false })

interface LapProgressionChartProps {
  /** Lap data for selected drivers */
  laps: Lap[]
  /** Selected driver abbreviations */
  selectedDrivers: string[]
  /** Qualifying session part (Q1/Q2/Q3) for title */
  sessionPart?: string
}

/**
 * Scatter plot showing lap time progression across qualifying attempts.
 * Helps identify traffic issues, track evolution, and driver improvement.
 * 
 * Note: This is a placeholder implementation for future enhancement.
 */
export function LapProgressionChart({ 
  laps, 
  selectedDrivers,
  sessionPart = 'Q3',
}: LapProgressionChartProps) {
  // Group laps by driver and assign attempt numbers
  const processedData = useMemo(() => {
    // Guard: Check if laps and selectedDrivers exist
    if (!laps || !Array.isArray(laps) || laps.length === 0) return []
    if (!selectedDrivers || !Array.isArray(selectedDrivers) || selectedDrivers.length === 0) return []
    
    const driverLaps = new Map<string, Lap[]>()
    
    // Group laps by driver
    laps.forEach(lap => {
      // Guard: Validate lap data
      if (!lap || !lap.driver || typeof lap.lapTime !== 'number') return
      if (selectedDrivers.includes(lap.driver) && lap.lapTime > 0) {
        const existing = driverLaps.get(lap.driver) || []
        driverLaps.set(lap.driver, [...existing, lap])
      }
    })

    // Sort by lap number and assign attempt index
    const result: Array<{
      driver: string
      attemptNumber: number
      lapTime: number
      lapNumber: number
      isPersonalBest: boolean
      color: string
    }> = []

    driverLaps.forEach((driverLapList, driver) => {
      const sorted = driverLapList.sort((a, b) => (a.lapNumber ?? 0) - (b.lapNumber ?? 0))
      sorted.forEach((lap, index) => {
        result.push({
          driver,
          attemptNumber: index + 1,
          lapTime: lap.lapTime ?? 0,
          lapNumber: lap.lapNumber ?? 0,
          isPersonalBest: lap.isPersonalBest ?? false,
          color: getTeamColor(driver),
        })
      })
    })

    return result
  }, [laps, selectedDrivers])

  // Create traces for each driver
  const traces = useMemo(() => {
    // Guard: Check if selectedDrivers exists
    if (!selectedDrivers || !Array.isArray(selectedDrivers) || selectedDrivers.length === 0) return []
    
    return selectedDrivers.map(driver => {
      const driverData = processedData.filter(d => d.driver === driver)
      const driverInfo = getDriverInfo(driver)
      const color = getTeamColor(driver)

      return {
        x: driverData.map(d => d.attemptNumber),
        y: driverData.map(d => d.lapTime),
        type: 'scatter' as const,
        mode: 'lines+markers' as const,
        name: driverInfo?.fullName || driver,
        marker: {
          color: driverData.map(d => d.isPersonalBest ? '#A855F7' : color),
          size: driverData.map(d => d.isPersonalBest ? 12 : 8),
          symbol: driverData.map(d => d.isPersonalBest ? 'star' : 'circle'),
          line: {
            color: 'white',
            width: 1,
          },
        },
        line: {
          color,
          width: 2,
          dash: 'dot' as const,
        },
        hovertemplate: 
          `<b>${driverInfo?.fullName || driver}</b><br>` +
          `Attempt: %{x}<br>` +
          `Time: %{customdata}<br>` +
          `<extra></extra>`,
        customdata: driverData.map(d => formatLapTime(d.lapTime)),
      }
    })
  }, [selectedDrivers, processedData])

  // Calculate y-axis range
  const yRange = useMemo(() => {
    // Guard: Check if processedData exists and has content
    if (!processedData || processedData.length === 0) return undefined
    
    const times = processedData
      .map(d => d.lapTime)
      .filter(t => typeof t === 'number' && isFinite(t))
    
    // Guard: Need at least one valid time
    if (times.length === 0) return undefined
    
    const min = Math.min(...times)
    const max = Math.max(...times)
    const range = max - min
    const padding = range > 0 ? range * 0.1 : 1
    return [min - padding, max + padding]
  }, [processedData])

  if (processedData.length === 0) {
    return (
      <div 
        className="h-64 w-full rounded-lg border border-f1gray/50 bg-f1dark/50 p-4"
        role="img"
        aria-label="No lap progression data available"
      >
        <div className="flex h-full flex-col items-center justify-center text-gray-500">
          <svg className="h-12 w-12 mb-2 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-sm">No lap data available</p>
          <p className="text-xs mt-1">Select drivers to see lap progression</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {/* Chart */}
      <div 
        className="h-64 w-full"
        role="img"
        aria-label={`Lap progression chart for ${sessionPart}`}
      >
        <Plot
          data={traces}
          layout={{
            autosize: true,
            height: 256,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#9CA3AF', family: 'Inter, sans-serif', size: 11 },
            xaxis: {
              title: { text: 'Attempt #', standoff: 10 },
              gridcolor: '#374151',
              zeroline: false,
              dtick: 1,
            },
            yaxis: {
              title: { text: 'Lap Time (s)', standoff: 10 },
              gridcolor: '#374151',
              zeroline: false,
              range: yRange,
            },
            margin: { l: 60, r: 20, t: 10, b: 50 },
            hovermode: 'closest',
            legend: {
              orientation: 'h' as const,
              y: -0.3,
              x: 0.5,
              xanchor: 'center',
              bgcolor: 'rgba(0,0,0,0)',
              font: { size: 10 },
            },
            showlegend: selectedDrivers.length <= 4,
          }}
          config={{
            responsive: true,
            displayModeBar: false,
          }}
          style={{ width: '100%', height: '100%' }}
        />
      </div>

      {/* Legend for markers */}
      <div className="flex items-center justify-center gap-4 text-xs text-gray-500">
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full bg-purple-sector" />
          <span>Personal Best</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-gray-400" />
          <span>Normal Lap</span>
        </div>
      </div>

      {/* Placeholder notice */}
      <p className="text-center text-xs text-gray-600 italic">
        Future: Add outlier detection and track evolution analysis
      </p>
    </div>
  )
}
