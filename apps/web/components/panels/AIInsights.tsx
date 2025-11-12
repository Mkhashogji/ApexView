'use client'

import { SectorComparison } from '@/../../packages/models/src/types'

interface AIInsightsProps {
  sectorData: SectorComparison[]
  referenceDriver: string
}

export function AIInsights({ sectorData, referenceDriver }: AIInsightsProps) {
  // Generate insights based on sector data
  const generateInsights = () => {
    if (sectorData.length === 0) {
      return ['No data available for analysis']
    }

    const insights: string[] = []
    const refData = sectorData.find((d) => d.driver === referenceDriver)
    
    if (!refData) {
      return ['Reference driver data not available']
    }

    // Analyze each driver vs reference
    sectorData.forEach((data) => {
      if (data.driver === referenceDriver) return

      const s1Delta = data.sector1 - refData.sector1
      const s2Delta = data.sector2 - refData.sector2
      const s3Delta = data.sector3 - refData.sector3
      const totalDelta = data.totalTime - refData.totalTime

      // Find biggest gain/loss
      const deltas = [
        { sector: 'Sector 1', delta: s1Delta, name: 'S1' },
        { sector: 'Sector 2', delta: s2Delta, name: 'S2' },
        { sector: 'Sector 3', delta: s3Delta, name: 'S3' },
      ]

      const maxLoss = deltas.reduce((prev, curr) => 
        Math.abs(curr.delta) > Math.abs(prev.delta) && curr.delta > 0 ? curr : prev
      )
      const maxGain = deltas.reduce((prev, curr) => 
        Math.abs(curr.delta) > Math.abs(prev.delta) && curr.delta < 0 ? curr : prev
      )

      // Generate insights
      if (totalDelta > 0) {
        insights.push(
          `${data.driver} is ${totalDelta.toFixed(3)}s slower than ${referenceDriver}. ` +
          `Major time loss in ${maxLoss.sector} (+${maxLoss.delta.toFixed(3)}s).`
        )
        
        if (Math.abs(maxGain.delta) > 0.01) {
          insights.push(
            `${data.driver} shows strength in ${maxGain.sector}, ` +
            `gaining ${Math.abs(maxGain.delta).toFixed(3)}s on ${referenceDriver}.`
          )
        }
      } else {
        insights.push(
          `${data.driver} is ${Math.abs(totalDelta).toFixed(3)}s faster than ${referenceDriver}. ` +
          `Key advantage in ${maxGain.sector} (${Math.abs(maxGain.delta).toFixed(3)}s).`
        )
      }

      // Consistency insights
      const avgDelta = (Math.abs(s1Delta) + Math.abs(s2Delta) + Math.abs(s3Delta)) / 3
      if (avgDelta < 0.05) {
        insights.push(
          `${data.driver} shows consistent pace across all sectors relative to ${referenceDriver}.`
        )
      }
    })

    // Find overall fastest sectors
    const fastestS1 = sectorData.reduce((prev, curr) => 
      curr.sector1 < prev.sector1 ? curr : prev
    )
    const fastestS2 = sectorData.reduce((prev, curr) => 
      curr.sector2 < prev.sector2 ? curr : prev
    )
    const fastestS3 = sectorData.reduce((prev, curr) => 
      curr.sector3 < prev.sector3 ? curr : prev
    )

    // Purple sector insights
    const purpleSectors: string[] = []
    if (fastestS1.driver === fastestS1.driver) purpleSectors.push(`S1 (${fastestS1.driver})`)
    if (fastestS2.driver === fastestS2.driver) purpleSectors.push(`S2 (${fastestS2.driver})`)
    if (fastestS3.driver === fastestS3.driver) purpleSectors.push(`S3 (${fastestS3.driver})`)

    if (purpleSectors.length > 0) {
      insights.push(
        `Fastest sectors: ${purpleSectors.join(', ')}.`
      )
    }

    return insights.slice(0, 5) // Limit to 5 insights
  }

  const insights = generateInsights()

  return (
    <div className="rounded-lg border border-f1red/30 bg-f1red/10 p-6">
      <h2 className="mb-4 flex items-center gap-2 text-2xl font-semibold">
        <span className="text-f1red">✨</span>
        AI Insights
      </h2>
      <div className="space-y-3">
        {insights.map((insight, index) => (
          <div key={index} className="rounded border border-f1gray/50 bg-f1dark/50 p-4">
            <p className="text-sm text-gray-300">{insight}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 text-xs text-gray-500">
        <p>
          Insights generated from sector time analysis. For more detailed analysis, 
          examine the telemetry and delta charts above.
        </p>
      </div>
    </div>
  )
}

