'use client'

import { Telemetry } from '@/../../packages/models/src/types'
import { getTeamColor } from '@/lib/drivers'
import dynamic from 'next/dynamic'
import { useState } from 'react'

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false })

interface TelemetryLineProps {
  telemetryData: Map<string, Telemetry>
  selectedDrivers: string[]
}

type TelemetryChannel = 'speed' | 'throttle' | 'brake'

export function TelemetryLine({ telemetryData, selectedDrivers }: TelemetryLineProps) {
  const [activeChannel, setActiveChannel] = useState<TelemetryChannel>('speed')

  if (telemetryData.size === 0) {
    return (
      <div className="h-96 w-full rounded border border-f1gray/50 bg-f1dark/50 p-4">
        <div className="flex h-full items-center justify-center text-gray-500">
          <p>No telemetry data available</p>
        </div>
      </div>
    )
  }

  // Prepare data for selected channel
  const traces = selectedDrivers
    .filter((driver) => telemetryData.has(driver))
    .map((driver) => {
      const data = telemetryData.get(driver)!
      const color = getTeamColor(driver)

      let yData: number[]
      let yLabel: string

      switch (activeChannel) {
        case 'speed':
          yData = data.speed
          yLabel = 'Speed (km/h)'
          break
        case 'throttle':
          yData = data.throttle
          yLabel = 'Throttle (%)'
          break
        case 'brake':
          yData = data.brake
          yLabel = 'Brake (%)'
          break
      }

      return {
        x: data.distance,
        y: yData,
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: driver,
        line: {
          color: color,
          width: 2,
        },
        hovertemplate: `<b>${driver}</b><br>Distance: %{x:.0f}m<br>${yLabel}: %{y:.1f}<extra></extra>`,
      }
    })

  const channelConfig: Record<TelemetryChannel, { label: string; unit: string; range?: [number, number] }> = {
    speed: { label: 'Speed', unit: 'km/h', range: [0, 350] },
    throttle: { label: 'Throttle', unit: '%', range: [0, 100] },
    brake: { label: 'Brake', unit: '%', range: [0, 100] },
  }

  const config = channelConfig[activeChannel]

  return (
    <div className="space-y-4">
      {/* Channel selector */}
      <div className="flex gap-2">
        {(['speed', 'throttle', 'brake'] as TelemetryChannel[]).map((channel) => (
          <button
            key={channel}
            onClick={() => setActiveChannel(channel)}
            className={`rounded px-4 py-2 text-sm font-medium transition-colors ${
              activeChannel === channel
                ? 'bg-f1red text-white'
                : 'bg-f1gray text-gray-400 hover:bg-f1gray/80'
            }`}
          >
            {channelConfig[channel].label}
          </button>
        ))}
      </div>

      {/* Plotly chart */}
      <div className="h-96 w-full">
        <Plot
          data={traces}
          layout={{
            autosize: true,
            height: 384,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#9CA3AF', family: 'Inter, sans-serif' },
            xaxis: {
              title: 'Distance (m)',
              gridcolor: '#374151',
              zeroline: false,
            },
            yaxis: {
              title: `${config.label} (${config.unit})`,
              gridcolor: '#374151',
              zeroline: false,
              range: config.range,
            },
            margin: { l: 60, r: 40, t: 40, b: 60 },
            hovermode: 'x unified',
            legend: {
              orientation: 'h' as const,
              y: -0.2,
              x: 0.5,
              xanchor: 'center',
            },
          }}
          config={{
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            displaylogo: false,
          }}
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    </div>
  )
}

