'use client'

import { SectorComparison, MLInsight, LapSimilarityResponse, ClusteringResponse } from '@/../../packages/models/src/types'
import { useMLInsightsQuery, useLapSimilarityQuery, useDriverClusteringQuery } from '@/lib/hooks'
import { formatSimilarity, formatDelta } from '@/lib/formatters'
import { getTeamColor, getDriverInfo } from '@/lib/drivers'
import { useMemo } from 'react'

/** Insight type icons */
const INSIGHT_ICONS: Record<string, string> = {
  similarity: '🔗',
  cluster: '📊',
  braking: '🛑',
  sector: '⚡',
  speed: '🏎️',
  consistency: '📈',
  error: '⚠️',
  default: '💡',
}

interface AIInsightsProps {
  /** Session ID for ML queries */
  sessionId: string
  /** Sector comparison data for rule-based fallback */
  sectorData: SectorComparison[]
  /** Reference driver for comparisons */
  referenceDriver: string
  /** Selected drivers for ML analysis */
  selectedDrivers: string[]
}

/**
 * AI-powered insights panel using ML service endpoints.
 * Falls back to rule-based insights if ML service is unavailable.
 */
export function AIInsights({ 
  sessionId,
  sectorData, 
  referenceDriver,
  selectedDrivers,
}: AIInsightsProps) {
  // ML Queries
  const mlInsightsQuery = useMLInsightsQuery(sessionId, selectedDrivers)
  const clusteringQuery = useDriverClusteringQuery(sessionId, selectedDrivers)
  
  // Get pairwise similarities for first two non-reference drivers
  const comparisonDrivers = selectedDrivers.filter(d => d !== referenceDriver).slice(0, 2)
  const similarityQuery1 = useLapSimilarityQuery(
    sessionId,
    referenceDriver,
    comparisonDrivers[0] || ''
  )
  const similarityQuery2 = useLapSimilarityQuery(
    sessionId,
    referenceDriver,
    comparisonDrivers[1] || ''
  )

  // Determine loading state
  const isLoading = mlInsightsQuery.isLoading || clusteringQuery.isLoading

  // Generate rule-based fallback insights
  const fallbackInsights = useMemo(() => {
    return generateRuleBasedInsights(sectorData, referenceDriver)
  }, [sectorData, referenceDriver])

  // Combine ML insights with similarity data
  const mlInsights = useMemo<MLInsight[]>(() => {
    const insights: MLInsight[] = []

    // Add similarity insights
    if (similarityQuery1.data) {
      insights.push(createSimilarityInsight(similarityQuery1.data))
    }
    if (similarityQuery2.data) {
      insights.push(createSimilarityInsight(similarityQuery2.data))
    }

    // Add clustering insights
    if (clusteringQuery.data) {
      insights.push(...createClusteringInsights(clusteringQuery.data))
    }

    // Add insights from ML endpoint
    if (mlInsightsQuery.data?.insights) {
      insights.push(...mlInsightsQuery.data.insights)
    }

    return insights.slice(0, 5)
  }, [similarityQuery1.data, similarityQuery2.data, clusteringQuery.data, mlInsightsQuery.data])

  // Use ML insights if available, otherwise fallback
  const displayInsights = mlInsights.length > 0 ? mlInsights : fallbackInsights
  const isUsingFallback = mlInsights.length === 0

  return (
    <div className="card-panel border-f1red/30 bg-gradient-to-br from-f1red/5 to-transparent">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="flex items-center gap-2 text-lg font-heading font-semibold uppercase tracking-wide">
          <span className="text-f1red">✨</span>
          AI Insights
        </h2>
        {isLoading && (
          <span className="text-xs text-gray-500 animate-pulse">
            Analyzing...
          </span>
        )}
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton h-16 rounded-lg" />
          ))}
        </div>
      )}

      {/* Insights List */}
      {!isLoading && (
        <div className="space-y-3" role="list" aria-label="AI analysis insights">
          {displayInsights.map((insight, index) => (
            <InsightCard 
              key={index} 
              insight={typeof insight === 'string' 
                ? { type: 'default', message: insight } 
                : insight
              } 
            />
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
        <p>
          {isUsingFallback 
            ? 'Insights generated from sector time analysis.' 
            : 'ML-powered analysis using telemetry similarity and clustering.'
          }
        </p>
        {!isUsingFallback && (
          <span className="inline-flex items-center gap-1 text-f1red">
            <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            ML Enhanced
          </span>
        )}
      </div>
    </div>
  )
}

/** Individual insight card component */
function InsightCard({ insight }: { insight: MLInsight }) {
  const icon = INSIGHT_ICONS[insight.type] || INSIGHT_ICONS.default
  
  return (
    <div 
      className="rounded-lg border border-f1gray/50 bg-f1dark/60 p-4 transition-colors hover:border-f1gray"
      role="listitem"
    >
      <div className="flex items-start gap-3">
        <span className="text-lg flex-shrink-0" aria-hidden="true">{icon}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-200">{insight.message}</p>
          {insight.drivers && insight.drivers.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {insight.drivers.map((driver) => (
                <span
                  key={driver}
                  className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs"
                  style={{ backgroundColor: `${getTeamColor(driver)}30` }}
                >
                  <span 
                    className="h-2 w-2 rounded-full" 
                    style={{ backgroundColor: getTeamColor(driver) }}
                  />
                  {driver}
                </span>
              ))}
            </div>
          )}
        </div>
        {insight.confidence && (
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            insight.confidence === 'high' 
              ? 'bg-green-500/20 text-green-400' 
              : insight.confidence === 'medium'
              ? 'bg-yellow-500/20 text-yellow-400'
              : 'bg-gray-500/20 text-gray-400'
          }`}>
            {insight.confidence}
          </span>
        )}
      </div>
    </div>
  )
}

/** Create insight from similarity data */
function createSimilarityInsight(data: LapSimilarityResponse): MLInsight {
  const similarityPercent = data.similarity * 100
  const d1Info = getDriverInfo(data.driver1)
  const d2Info = getDriverInfo(data.driver2)
  
  let description = ''
  if (similarityPercent >= 90) {
    description = `Very similar driving styles, likely similar setups.`
  } else if (similarityPercent >= 75) {
    description = `Similar overall approach with some technique differences.`
  } else {
    description = `Different driving styles detected.`
  }

  // Add feature-specific detail if available
  if (data.feature_scores) {
    const lowestFeature = Object.entries(data.feature_scores)
      .filter(([key]) => key !== 'overall')
      .sort((a, b) => (a[1] || 1) - (b[1] || 1))[0]
    
    if (lowestFeature && lowestFeature[1] && lowestFeature[1] < 0.85) {
      description += ` Main difference in ${lowestFeature[0]} application.`
    }
  }

  return {
    type: 'similarity',
    message: `${data.driver1} & ${data.driver2}: ${formatSimilarity(data.similarity)} similar. ${description}`,
    confidence: similarityPercent >= 85 ? 'high' : similarityPercent >= 70 ? 'medium' : 'low',
    drivers: [data.driver1, data.driver2],
  }
}

/** Create insights from clustering data */
function createClusteringInsights(data: ClusteringResponse): MLInsight[] {
  // Guard: Check if data and clusters exist
  if (!data || !data.clusters || !Array.isArray(data.clusters)) return []
  
  const insights: MLInsight[] = []

  // Group drivers by cluster
  const clusterGroups = new Map<number, string[]>()
  data.clusters.forEach(c => {
    if (!c || typeof c.cluster !== 'number' || !c.driver) return
    const existing = clusterGroups.get(c.cluster) || []
    clusterGroups.set(c.cluster, [...existing, c.driver])
  })

  // Create insights for each cluster with multiple drivers
  clusterGroups.forEach((drivers, clusterId) => {
    if (drivers.length >= 2) {
      const description = data.cluster_descriptions?.[clusterId.toString()] 
        || 'Similar driving characteristics'
      
      insights.push({
        type: 'cluster',
        message: `${drivers.join(', ')} grouped together: ${description}`,
        confidence: 'medium',
        drivers,
      })
    }
  })

  return insights.slice(0, 2) // Limit cluster insights
}

/** Generate rule-based fallback insights */
function generateRuleBasedInsights(sectorData: SectorComparison[], referenceDriver: string): MLInsight[] {
  // Guard: Check if sectorData is valid
  if (!sectorData || !Array.isArray(sectorData) || sectorData.length === 0) {
    return [{ type: 'default', message: 'No data available for analysis' }]
  }

  const insights: MLInsight[] = []
  const refData = sectorData.find((d) => d?.driver === referenceDriver)
  
  if (!refData) {
    return [{ type: 'default', message: 'Reference driver data not available' }]
  }

  // Guard: Ensure refData has valid sector times
  if (typeof refData.sector1 !== 'number' || typeof refData.sector2 !== 'number' || 
      typeof refData.sector3 !== 'number' || typeof refData.totalTime !== 'number') {
    return [{ type: 'default', message: 'Incomplete sector data for reference driver' }]
  }

  // Analyze each driver vs reference
  sectorData.forEach((data) => {
    // Guard: Skip invalid data
    if (!data || !data.driver || data.driver === referenceDriver) return
    if (typeof data.sector1 !== 'number' || typeof data.sector2 !== 'number' ||
        typeof data.sector3 !== 'number' || typeof data.totalTime !== 'number') return

    const s1Delta = data.sector1 - refData.sector1
    const s2Delta = data.sector2 - refData.sector2
    const s3Delta = data.sector3 - refData.sector3
    const totalDelta = data.totalTime - refData.totalTime

    const deltas = [
      { sector: 'S1', delta: s1Delta },
      { sector: 'S2', delta: s2Delta },
      { sector: 'S3', delta: s3Delta },
    ]

    const maxLoss = deltas.reduce((prev, curr) => 
      curr.delta > prev.delta ? curr : prev
    , deltas[0])
    const maxGain = deltas.reduce((prev, curr) => 
      curr.delta < prev.delta ? curr : prev
    , deltas[0])

    if (Math.abs(totalDelta) > 0.01) {
      const isFaster = totalDelta < 0
      insights.push({
        type: 'sector',
        message: `${data.driver} is ${formatDelta(totalDelta)} vs ${referenceDriver}. ${
          isFaster 
            ? `Key advantage in ${maxGain.sector} (${formatDelta(maxGain.delta)}).`
            : `Main time loss in ${maxLoss.sector} (${formatDelta(maxLoss.delta)}).`
        }`,
        confidence: 'high',
        drivers: [data.driver, referenceDriver],
      })
    }
  })

  // Find fastest sectors with guards
  const validData = sectorData.filter(d => 
    d && typeof d.sector1 === 'number' && typeof d.sector2 === 'number' && 
    typeof d.sector3 === 'number' && d.driver
  )
  
  if (validData.length === 0) {
    return insights.length > 0 ? insights.slice(0, 5) : [{ type: 'default', message: 'Insufficient data for sector analysis' }]
  }

  const sectors = ['sector1', 'sector2', 'sector3'] as const
  const fastestDrivers = sectors.map((key, i) => {
    const fastest = validData.reduce((prev, curr) => 
      (curr[key] ?? Infinity) < (prev[key] ?? Infinity) ? curr : prev
    , validData[0])
    return { sector: `S${i + 1}`, driver: fastest?.driver ?? '' }
  })

  // Check if one driver has all purple sectors
  const uniqueFastestDrivers = [...new Set(fastestDrivers.map(f => f.driver).filter(Boolean))]
  if (uniqueFastestDrivers.length === 1 && uniqueFastestDrivers[0]) {
    insights.push({
      type: 'consistency',
      message: `${uniqueFastestDrivers[0]} set the fastest time in all three sectors - dominant performance.`,
      confidence: 'high',
      drivers: uniqueFastestDrivers,
    })
  } else if (uniqueFastestDrivers.length > 0) {
    insights.push({
      type: 'sector',
      message: `Fastest sectors: ${fastestDrivers.map(f => `${f.sector} (${f.driver})`).join(', ')}.`,
      confidence: 'high',
    })
  }

  return insights.slice(0, 5)
}

