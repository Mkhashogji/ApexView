'use client'

import { DeltaData, SectorInfo } from '@/../../packages/models/src/types'
import { getTeamColor, getDriverInfo } from '@/lib/drivers'
import { formatDelta } from '@/lib/formatters'
import Plot from './PlotlyLazy'
import { useMemo, useCallback } from 'react'

interface DeltaPlotProps {
  /** Delta data for each driver comparison */
  deltaData: DeltaData[]
  /** Reference driver abbreviation */
  referenceDriver: string
  /** Sector boundaries for vertical lines */
  sectors?: SectorInfo[]
  /** Track length for end-of-lap annotation */
  trackLength?: number
  /** Callback for zoom/pan sync with other charts */
  onRangeChange?: (xRange: [number, number] | null) => void
  /** External x-axis range for sync */
  xRange?: [number, number] | null
}

export function DeltaPlot({ 
  deltaData, 
  referenceDriver,
  sectors = [],
  trackLength,
  onRangeChange,
  xRange,
}: DeltaPlotProps) {

  // Calculate final deltas for each driver
  const finalDeltas = useMemo(() => {
    // Guard: Check if deltaData exists and is an array
    if (!deltaData || !Array.isArray(deltaData) || deltaData.length === 0) return []
    
    return deltaData
      .filter(delta => delta && delta.delta && Array.isArray(delta.delta))
      .map((delta) => {
        const deltaArray = delta.delta || []
        const lastDelta = deltaArray.length > 0 ? deltaArray[deltaArray.length - 1] : 0
        return {
          driver: delta.compareDriver || '',
          delta: lastDelta ?? 0,
          color: getTeamColor(delta.compareDriver || ''),
        }
      })
  }, [deltaData])

  // Determine y-axis range based on data
  const yRange = useMemo(() => {
    // Guard: Check if deltaData is valid
    if (!deltaData || !Array.isArray(deltaData) || deltaData.length === 0) return [-1, 1]
    
    let minDelta = 0
    let maxDelta = 0
    
    deltaData.forEach((d) => {
      // Guard: Check if delta array exists
      if (d && d.delta && Array.isArray(d.delta)) {
        d.delta.forEach((val) => {
          if (typeof val === 'number' && isFinite(val)) {
            minDelta = Math.min(minDelta, val)
            maxDelta = Math.max(maxDelta, val)
          }
        })
      }
    })
    
    // Add padding and round to nice values
    const padding = Math.max(0.1, (maxDelta - minDelta) * 0.1)
    return [
      Math.floor((minDelta - padding) * 10) / 10,
      Math.ceil((maxDelta + padding) * 10) / 10,
    ]
  }, [deltaData])

  // Create traces for each driver comparison
  const traces = useMemo(() => {
    // Guard: Check if deltaData is valid
    if (!deltaData || !Array.isArray(deltaData) || deltaData.length === 0) return []
    
    return deltaData
      .filter(delta => delta && delta.delta && Array.isArray(delta.delta) && delta.distance)
      .map((delta) => {
        const color = getTeamColor(delta.compareDriver || '')
        const driverInfo = getDriverInfo(delta.compareDriver || '')
        const deltaArray = delta.delta || []
        
        // Main delta line with team color
        return {
          x: delta.distance || [],
          y: deltaArray,
          type: 'scatter' as const,
          mode: 'lines' as const,
          name: driverInfo?.fullName || delta.compareDriver || 'Unknown',
          fill: 'tozeroy' as const,
          fillcolor: deltaArray.some(d => typeof d === 'number' && d > 0) 
            ? 'rgba(239, 68, 68, 0.15)' 
            : 'rgba(34, 197, 94, 0.15)',
          line: { color, width: 2 },
          hovertemplate: 
            `<b>${driverInfo?.fullName || delta.compareDriver || 'Unknown'}</b><br>` +
            `Distance: %{x:.0f}m<br>` +
            `Delta: %{y:+.3f}s<extra></extra>`,
        }
      })
  }, [deltaData])

  // Generate sector boundary shapes
  const sectorShapes = useMemo(() => {
    if (!sectors.length) return []
    
    return sectors.slice(0, -1).map((sector) => ({
      type: 'line' as const,
      xref: 'x' as const,
      yref: 'paper' as const,
      x0: sector.endDistance,
      x1: sector.endDistance,
      y0: 0,
      y1: 1,
      line: {
        color: '#4B5563',
        width: 1,
        dash: 'dot' as const,
      },
    }))
  }, [sectors])

  // Generate sector label annotations
  const sectorAnnotations = useMemo(() => {
    if (!sectors.length) return []
    
    return sectors.map((sector, i) => ({
      x: (sector.startDistance + sector.endDistance) / 2,
      y: 1,
      xref: 'x' as const,
      yref: 'paper' as const,
      text: `S${sector.sectorNumber}`,
      showarrow: false,
      font: { size: 10, color: '#6B7280' },
      yshift: 10,
    }))
  }, [sectors])

  // Generate final delta annotations
  const deltaAnnotations = useMemo(() => {
    if (!trackLength || finalDeltas.length === 0) return []
    
    return finalDeltas.map((fd, i) => ({
      x: trackLength,
      y: fd.delta,
      xref: 'x' as const,
      yref: 'y' as const,
      text: `${fd.driver}: ${formatDelta(fd.delta)}`,
      showarrow: true,
      arrowhead: 0,
      arrowsize: 0.5,
      arrowcolor: fd.color,
      ax: 50,
      ay: i * 20 - (finalDeltas.length * 10),
      font: { 
        size: 11, 
        color: fd.delta > 0 ? '#EF4444' : '#22C55E',
      },
      bgcolor: 'rgba(21, 21, 30, 0.8)',
      borderpad: 4,
    }))
  }, [trackLength, finalDeltas])

  // Handle relayout event for zoom/pan sync
  const handleRelayout = useCallback((event: Record<string, unknown>) => {
    if (!onRangeChange) return

    if ('xaxis.range[0]' in event && 'xaxis.range[1]' in event) {
      const x0 = event['xaxis.range[0]'] as number
      const x1 = event['xaxis.range[1]'] as number
      onRangeChange([x0, x1])
    } else if ('xaxis.autorange' in event) {
      onRangeChange(null)
    }
  }, [onRangeChange])

  if (deltaData.length === 0) {
    return (
      <div 
        className="h-96 w-full rounded-lg border border-f1gray/50 bg-f1dark/50 p-4"
        role="img"
        aria-label="No delta data available"
      >
        <div className="flex h-full flex-col items-center justify-center text-gray-500">
          <p>No delta data available</p>
          <p className="text-sm mt-1">Select additional drivers to compare with {referenceDriver}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Legend */}
      <div className="flex flex-wrap items-center justify-between gap-4 text-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="h-3 w-8 rounded bg-delta-positive/30" />
            <span className="text-gray-400">Slower than {referenceDriver}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-8 rounded bg-delta-negative/30" />
            <span className="text-gray-400">Faster</span>
          </div>
        </div>
        
        {/* Final delta summary */}
        <div className="flex items-center gap-3">
          {finalDeltas.map((fd) => (
            <span 
              key={fd.driver}
              className={`font-mono text-sm font-medium ${fd.delta > 0 ? 'text-delta-positive' : 'text-delta-negative'}`}
            >
              {fd.driver}: {formatDelta(fd.delta)}
            </span>
          ))}
        </div>
      </div>

      {/* Plotly chart */}
      <div 
        className="h-96 w-full"
        role="img"
        aria-label={`Time delta chart comparing drivers to ${referenceDriver}`}
      >
        <Plot
          data={traces}
          layout={{
            autosize: true,
            height: 384,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#9CA3AF', family: 'Inter, sans-serif', size: 12 },
            xaxis: {
              title: { text: 'Distance (m)', standoff: 20 },
              gridcolor: '#374151',
              zeroline: false,
              range: xRange || undefined,
              tickformat: ',.0f',
            },
            yaxis: {
              title: { text: 'Time Delta (s)', standoff: 10 },
              gridcolor: '#374151',
              zeroline: true,
              zerolinecolor: '#6B7280',
              zerolinewidth: 2,
              range: yRange,
              tickformat: '+.2f',
            },
            margin: { l: 65, r: 80, t: 20, b: 70 },
            hovermode: 'x unified',
            legend: {
              orientation: 'h' as const,
              y: -0.25,
              x: 0.5,
              xanchor: 'center',
              bgcolor: 'rgba(0,0,0,0)',
              font: { size: 11 },
            },
            shapes: [
              // Zero line
              {
                type: 'line' as const,
                x0: 0,
                x1: 1,
                xref: 'paper' as const,
                y0: 0,
                y1: 0,
                line: {
                  color: '#9CA3AF',
                  width: 1.5,
                  dash: 'dash' as const,
                },
              },
              // Sector boundaries
              ...sectorShapes,
            ],
            annotations: [
              ...sectorAnnotations,
              ...deltaAnnotations,
            ],
          }}
          config={{
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
            displaylogo: false,
            toImageButtonOptions: {
              format: 'png',
              filename: `delta_vs_${referenceDriver}`,
              scale: 2,
            },
          }}
          style={{ width: '100%', height: '100%' }}
          onRelayout={handleRelayout}
        />
      </div>

      {/* Help text */}
      <p className="text-xs text-gray-500">
        <strong>Tip:</strong> Positive values (above zero) mean the driver is losing time compared to {referenceDriver}. 
        Negative values mean they are gaining time.
      </p>
    </div>
  )
}

