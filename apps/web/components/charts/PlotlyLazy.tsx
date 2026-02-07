'use client'

import dynamic from 'next/dynamic'
import type { ComponentType } from 'react'

/** Props accepted by the lazy Plot component */
export interface PlotProps {
  data: Array<Record<string, unknown>>
  layout?: Record<string, unknown>
  config?: Record<string, unknown>
  style?: React.CSSProperties
  className?: string
  onRelayout?: (event: Record<string, unknown>) => void
  onHover?: (event: Record<string, unknown>) => void
  onClick?: (event: Record<string, unknown>) => void
  useResizeHandler?: boolean
}

// Create Plot component using the minimal plotly.js distribution
// This reduces the bundle from ~3.5 MiB (full) to ~300 KiB (basic-min)
const PlotlyLazy = dynamic(
  () =>
    Promise.all([
      import('plotly.js-basic-dist-min'),
      import('react-plotly.js/factory'),
    ]).then(([Plotly, { default: createPlotlyComponent }]) =>
      createPlotlyComponent(Plotly.default || Plotly)
    ) as Promise<ComponentType<PlotProps>>,
  {
    ssr: false,
    loading: () => (
      <div className="h-96 w-full flex items-center justify-center rounded-lg border border-f1gray/50 bg-f1dark/50">
        <div className="text-center">
          <div className="h-8 w-8 mx-auto rounded-full border-2 border-f1red border-t-transparent animate-spin" />
          <p className="mt-3 text-sm text-gray-500">Loading chart...</p>
        </div>
      </div>
    ),
  }
)

export default PlotlyLazy
