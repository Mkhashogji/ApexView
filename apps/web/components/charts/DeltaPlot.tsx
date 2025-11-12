'use client'

import { DeltaData } from '@/../../packages/models/src/types'
import { getTeamColor } from '@/lib/drivers'
import dynamic from 'next/dynamic'

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false })

interface DeltaPlotProps {
  deltaData: DeltaData[]
  referenceDriver: string
}

export function DeltaPlot({ deltaData, referenceDriver }: DeltaPlotProps) {
  if (deltaData.length === 0) {
    return (
      <div className="h-96 w-full rounded border border-f1gray/50 bg-f1dark/50 p-4">
        <div className="flex h-full items-center justify-center text-gray-500">
          <p>No delta data available. Select drivers to compare with {referenceDriver}.</p>
        </div>
      </div>
    )
  }

  // Create traces for each driver comparison
  const traces = deltaData.map((delta) => {
    const color = getTeamColor(delta.compareDriver)
    
    // Separate positive and negative deltas for different colors
    const positiveIndices: number[] = []
    const negativeIndices: number[] = []
    
    delta.delta.forEach((d, i) => {
      if (d >= 0) {
        positiveIndices.push(i)
      } else {
        negativeIndices.push(i)
      }
    })

    return [
      // Positive delta (slower - red)
      {
        x: positiveIndices.map(i => delta.distance[i]),
        y: positiveIndices.map(i => delta.delta[i]),
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: `${delta.compareDriver} (slower)`,
        fill: 'tozeroy' as const,
        fillcolor: 'rgba(239, 68, 68, 0.3)',
        line: {
          color: '#EF4444',
          width: 2,
        },
        hovertemplate: `<b>${delta.compareDriver}</b><br>Distance: %{x:.0f}m<br>Delta: +%{y:.3f}s<extra></extra>`,
        showlegend: false,
      },
      // Negative delta (faster - green)
      {
        x: negativeIndices.map(i => delta.distance[i]),
        y: negativeIndices.map(i => delta.delta[i]),
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: `${delta.compareDriver} (faster)`,
        fill: 'tozeroy' as const,
        fillcolor: 'rgba(34, 197, 94, 0.3)',
        line: {
          color: '#22C55E',
          width: 2,
        },
        hovertemplate: `<b>${delta.compareDriver}</b><br>Distance: %{x:.0f}m<br>Delta: %{y:.3f}s<extra></extra>`,
        showlegend: false,
      },
      // Full line for legend
      {
        x: delta.distance,
        y: delta.delta,
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: delta.compareDriver,
        line: {
          color: color,
          width: 0,
        },
        showlegend: true,
        hoverinfo: 'skip' as const,
      },
    ]
  }).flat()

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="h-3 w-12 rounded bg-red-500/30" />
          <span className="text-gray-400">Slower than {referenceDriver}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-12 rounded bg-green-500/30" />
          <span className="text-gray-400">Faster than {referenceDriver}</span>
        </div>
      </div>

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
              title: 'Time Delta (seconds)',
              gridcolor: '#374151',
              zeroline: true,
              zerolinecolor: '#6B7280',
              zerolinewidth: 2,
            },
            margin: { l: 60, r: 40, t: 40, b: 60 },
            hovermode: 'x unified',
            legend: {
              orientation: 'h' as const,
              y: -0.2,
              x: 0.5,
              xanchor: 'center',
            },
            shapes: [
              {
                type: 'line' as const,
                x0: 0,
                x1: 1,
                xref: 'paper' as const,
                y0: 0,
                y1: 0,
                line: {
                  color: '#6B7280',
                  width: 2,
                  dash: 'dash' as const,
                },
              },
            ],
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

      <div className="text-sm text-gray-400">
        <p>
          <strong>How to read:</strong> Positive values (red area) indicate the driver is slower than{' '}
          {referenceDriver}. Negative values (green area) indicate the driver is faster.
        </p>
      </div>
    </div>
  )
}

