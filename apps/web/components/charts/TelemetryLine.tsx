'use client'

import { Telemetry, DRSZone, Corner } from '@/../../packages/models/src/types'
import { getTeamColor, getDriverInfo, getDriverTCam, getTeammateDrivers } from '@/lib/drivers'
import { getDrsSegments } from '@/lib/utils/drsZones'
import Plot from './PlotlyLazy'
import { useState, useMemo, useCallback } from 'react'

/** Available telemetry channels */
type TelemetryChannel = 'speed' | 'throttle' | 'brake' | 'gear' | 'rpm'

/** Channel configuration */
interface ChannelConfig {
  label: string
  unit: string
  range?: [number, number]
  color?: string
}

interface TelemetryLineProps {
  /** Telemetry data mapped by driver abbreviation */
  telemetryData: Map<string, Telemetry>
  /** Selected driver abbreviations */
  selectedDrivers: string[]
  /** DRS zones for annotation overlay */
  drsZones?: DRSZone[]
  /** Corner positions for x-axis annotations */
  corners?: Corner[]
  /** Track length in meters */
  trackLength?: number
  /** Callback for zoom/pan sync with other charts */
  onRangeChange?: (xRange: [number, number] | null) => void
  /** External x-axis range for sync */
  xRange?: [number, number] | null
}

/** Channel configurations */
const CHANNEL_CONFIG: Record<TelemetryChannel, ChannelConfig> = {
  speed: { label: 'Speed', unit: 'km/h', range: [0, 370] },
  throttle: { label: 'Throttle', unit: '%', range: [0, 100] },
  brake: { label: 'Brake', unit: '%', range: [0, 100] },
  gear: { label: 'Gear', unit: '', range: [0, 9] },
  rpm: { label: 'RPM', unit: '', range: [0, 15000] },
}

/** All available channels */
const ALL_CHANNELS: TelemetryChannel[] = ['speed', 'throttle', 'brake', 'gear', 'rpm']

/** Primary channels shown by default */
const PRIMARY_CHANNELS: TelemetryChannel[] = ['speed', 'throttle', 'brake']

/**
 * Helper function to determine line style based on T-Cam designation
 * When both teammates are selected, use solid for black T-Cam and dashed for yellow T-Cam
 */
function getLineStyle(driver: string, selectedDrivers: string[]): { dash: 'solid' | 'dash'; width: number } {
  const teammates = getTeammateDrivers(driver)
  const selectedTeammates = teammates.filter(t => selectedDrivers.includes(t))
  
  // Only apply T-Cam styling if both teammates are selected
  if (selectedTeammates.length <= 1) {
    return { dash: 'solid', width: 2 }
  }
  
  const tCam = getDriverTCam(driver)
  return tCam === 'black'
    ? { dash: 'solid', width: 2.5 }
    : { dash: 'dash', width: 2 }
}

export function TelemetryLine({ 
  telemetryData, 
  selectedDrivers,
  drsZones = [],
  corners = [],
  trackLength,
  onRangeChange,
  xRange,
}: TelemetryLineProps) {
  const [activeChannel, setActiveChannel] = useState<TelemetryChannel>('speed')
  const [showAllChannels, setShowAllChannels] = useState(false)
  const [showGuide, setShowGuide] = useState(false)

  // Get available channels based on data
  const availableChannels = useMemo(() => {
    // Guard: Check if telemetryData exists and has content
    if (!telemetryData || telemetryData.size === 0) return PRIMARY_CHANNELS
    if (!selectedDrivers || selectedDrivers.length === 0) return PRIMARY_CHANNELS
    
    const firstDriver = selectedDrivers.find(d => telemetryData.has(d))
    if (!firstDriver) return PRIMARY_CHANNELS
    
    const data = telemetryData.get(firstDriver)
    if (!data) return PRIMARY_CHANNELS
    
    return ALL_CHANNELS.filter(channel => {
      switch (channel) {
        case 'rpm': return data.rpm && Array.isArray(data.rpm) && data.rpm.length > 0
        case 'gear': return data.gear && Array.isArray(data.gear) && data.gear.length > 0
        default: return true
      }
    })
  }, [telemetryData, selectedDrivers])

  // Memoize traces for performance
  const traces = useMemo(() => {
    // Guard: Ensure we have valid data to process
    if (!telemetryData || telemetryData.size === 0) return []
    if (!selectedDrivers || selectedDrivers.length === 0) return []
    
    return selectedDrivers
      .filter((driver) => telemetryData.has(driver))
      .map((driver) => {
        const data = telemetryData.get(driver)
        // Guard: Skip if no data for this driver
        if (!data) return null
        
        const color = getTeamColor(driver)
        const driverInfo = getDriverInfo(driver)
        const config = CHANNEL_CONFIG[activeChannel]

        let yData: number[] = []
        switch (activeChannel) {
          case 'speed': yData = data.speed || []; break
          case 'throttle': yData = data.throttle || []; break
          case 'brake': yData = data.brake || []; break
          case 'gear': yData = data.gear || []; break
          case 'rpm': yData = data.rpm || []; break
        }

        // Get line style based on T-Cam (solid for black, dash for yellow when teammates selected)
        const lineStyle = getLineStyle(driver, selectedDrivers)

        return {
          x: data.distance || [],
          y: yData,
          type: 'scatter' as const,
          mode: 'lines' as const,
          name: driver,
          line: { 
            color, 
            ...lineStyle 
          },
          hovertemplate: `<b>${driverInfo?.fullName || driver}</b><br>` +
            `Distance: %{x:.0f}m<br>` +
            `${config.label}: %{y:.1f}${config.unit}<extra></extra>`,
        }
      })
      .filter((trace): trace is NonNullable<typeof trace> => trace !== null)
  }, [telemetryData, selectedDrivers, activeChannel])

  // Generate DRS zone shapes (handles wrap-around zones that cross start/finish)
  const drsShapes = useMemo(() => {
    if (!drsZones.length) return []
    
    const config = CHANNEL_CONFIG[activeChannel]
    const yMin = config.range?.[0] ?? 0
    const yMax = config.range?.[1] ?? 100

    // Use trackLength if provided, otherwise estimate from data
    const effectiveTrackLength = trackLength || 
      Math.max(...Array.from(telemetryData.values()).flatMap(d => d.distance || []), 5000)

    // Convert DRS zones to segments (handles wrap-around zones)
    const segments = getDrsSegments(drsZones, effectiveTrackLength)

    return segments.map((segment) => ({
      type: 'rect' as const,
      xref: 'x' as const,
      yref: 'y' as const,
      x0: segment.start,
      x1: segment.end,
      y0: yMin,
      y1: yMax,
      fillcolor: 'rgba(34, 197, 94, 0.1)',
      line: { width: 0 },
      layer: 'below' as const,
    }))
  }, [drsZones, activeChannel, trackLength, telemetryData])

  // Generate corner annotations
  const cornerAnnotations = useMemo(() => {
    if (!corners.length) return []

    return corners.map((corner) => ({
      x: corner.distance,
      y: 0,
      xref: 'x' as const,
      yref: 'paper' as const,
      text: `T${corner.cornerNumber}`,
      showarrow: false,
      font: { size: 9, color: '#6B7280' },
      yshift: -25,
    }))
  }, [corners])

  // Handle relayout event for zoom/pan sync
  const handleRelayout = useCallback((event: Record<string, unknown>) => {
    if (!onRangeChange) return

    if ('xaxis.range[0]' in event && 'xaxis.range[1]' in event) {
      const x0 = event['xaxis.range[0]'] as number
      const x1 = event['xaxis.range[1]'] as number
      onRangeChange([x0, x1])
    } else if ('xaxis.autorange' in event) {
      onRangeChange(null) // Reset to auto
    }
  }, [onRangeChange])

  const config = CHANNEL_CONFIG[activeChannel]
  const displayChannels = showAllChannels ? availableChannels : PRIMARY_CHANNELS

  if (telemetryData.size === 0) {
    return (
      <div 
        className="h-96 w-full rounded-lg border border-f1gray/50 bg-f1dark/50 p-4"
        role="img"
        aria-label="No telemetry data available"
      >
        <div className="flex h-full items-center justify-center text-gray-500">
          <p>No telemetry data available</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Channel selector */}
      <div className="flex flex-wrap items-center gap-2">
        {displayChannels.map((channel) => (
          <button
            key={channel}
            onClick={() => setActiveChannel(channel)}
            disabled={!availableChannels.includes(channel)}
            className={`
              rounded-md px-4 py-2 text-sm font-medium transition-all duration-200
              focus-ring
              ${activeChannel === channel
                ? 'bg-f1red text-white shadow-glow-red-sm'
                : availableChannels.includes(channel)
                ? 'bg-f1gray/50 text-gray-300 hover:bg-f1gray hover:text-white'
                : 'bg-f1gray/20 text-gray-600 cursor-not-allowed'
              }
            `}
            aria-pressed={activeChannel === channel}
            aria-label={`Show ${CHANNEL_CONFIG[channel].label} trace`}
          >
            {CHANNEL_CONFIG[channel].label}
          </button>
        ))}
        
        {/* Toggle more channels */}
        {availableChannels.length > PRIMARY_CHANNELS.length && (
          <button
            onClick={() => setShowAllChannels(!showAllChannels)}
            className="ml-2 text-xs text-gray-400 hover:text-white transition-colors"
          >
            {showAllChannels ? '− Less' : '+ More'}
          </button>
        )}

        {/* DRS zone legend */}
        {drsZones.length > 0 && (
          <div className="ml-auto flex items-center gap-2 text-xs text-gray-400">
            <span className="h-3 w-6 rounded bg-drs-zone/20 border border-drs-zone/30" />
            <span>DRS Zone</span>
          </div>
        )}
      </div>

      {/* Plotly chart */}
      <div 
        className="h-96 w-full"
        role="img"
        aria-label={`Telemetry ${config.label} chart comparing ${selectedDrivers.join(', ')}`}
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
              title: { text: `${config.label}${config.unit ? ` (${config.unit})` : ''}`, standoff: 10 },
              gridcolor: '#374151',
              zeroline: false,
              zerolinecolor: '#4B5563',
              range: config.range,
            },
            margin: { l: 65, r: 20, t: 20, b: 70 },
            hovermode: 'x unified',
            legend: {
              orientation: 'h' as const,
              y: -0.25,
              x: 0.5,
              xanchor: 'center',
              bgcolor: 'rgba(0,0,0,0)',
              font: { size: 11 },
            },
            shapes: drsShapes,
            annotations: cornerAnnotations,
          }}
          config={{
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
            displaylogo: false,
            toImageButtonOptions: {
              format: 'png',
              filename: `telemetry_${activeChannel}`,
              scale: 2,
            },
          }}
          style={{ width: '100%', height: '100%' }}
          onRelayout={handleRelayout}
        />
      </div>

      {/* How to read this chart */}
      <button
        onClick={() => setShowGuide(!showGuide)}
        className="text-xs text-gray-500 hover:text-gray-400 transition-colors flex items-center gap-1"
        type="button"
        aria-expanded={showGuide}
      >
        <span
          className="inline-block transition-transform duration-200"
          style={{ transform: showGuide ? 'rotate(90deg)' : 'rotate(0deg)' }}
        >
          &#9656;
        </span>
        How to read this chart
      </button>
      {showGuide && (
        <div className="mt-2 p-3 rounded border border-white/10 bg-white/[0.02] text-sm text-gray-500 space-y-2">
          <div>
            <span className="text-gray-400 font-medium">What this shows: </span>
            Each line represents one driver&apos;s telemetry data over the full lap distance. Lines are coloured by team.
          </div>
          <div>
            <span className="text-gray-400 font-medium">Channels: </span>
            Speed (km/h) = velocity throughout the lap. Throttle/Brake (0-100%) = driver inputs. Gear (1-8). RPM = engine revolutions.
          </div>
          <div>
            <span className="text-gray-400 font-medium">DRS zones: </span>
            Green shaded regions mark official DRS activation zones where drivers can reduce aerodynamic drag for higher straight-line speed.
          </div>
          <div>
            <span className="text-gray-400 font-medium">Teammate styling: </span>
            When both teammates are selected, the #1 driver uses a solid line and the #2 driver uses a dashed line (based on T-Cam designation).
          </div>
          <div>
            <span className="text-gray-400 font-medium">Zoom &amp; sync: </span>
            Click-drag to zoom into a section. Double-click to reset. Zooming this chart also adjusts the delta chart below to the same track section.
          </div>
        </div>
      )}
    </div>
  )
}

