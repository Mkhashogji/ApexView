import type { TelemetryPoint } from './types'

/**
 * Calculate similarity between two laps using simple heuristics.
 * This is a lightweight ML-inspired feature for lap comparison.
 */

export function calculateLapSimilarity(
  lap1: TelemetryPoint[],
  lap2: TelemetryPoint[]
): number {
  /**
   * Calculate similarity score (0-1) between two laps.
   * Uses euclidean distance of normalized telemetry features.
   */
  
  if (lap1.length === 0 || lap2.length === 0) {
    return 0
  }

  // Simple feature extraction: average speed, throttle, brake
  const features1 = extractFeatures(lap1)
  const features2 = extractFeatures(lap2)

  // Calculate euclidean distance
  const distance = Math.sqrt(
    Object.keys(features1).reduce((sum, key) => {
      const diff = features1[key as keyof typeof features1] - features2[key as keyof typeof features2]
      return sum + diff * diff
    }, 0)
  )

  // Convert to similarity (0-1 scale)
  const similarity = 1 / (1 + distance)
  return similarity
}

function extractFeatures(telemetry: TelemetryPoint[]) {
  const avgSpeed = telemetry.reduce((sum, p) => sum + p.speed, 0) / telemetry.length
  const avgThrottle = telemetry.reduce((sum, p) => sum + p.throttle, 0) / telemetry.length
  const avgBrake = telemetry.reduce((sum, p) => sum + p.brake, 0) / telemetry.length
  
  const maxSpeed = Math.max(...telemetry.map(p => p.speed))
  const minSpeed = Math.min(...telemetry.map(p => p.speed))

  return {
    avgSpeed: avgSpeed / 350,  // normalize by max F1 speed
    avgThrottle: avgThrottle / 100,
    avgBrake: avgBrake / 100,
    speedRange: (maxSpeed - minSpeed) / 350,
  }
}

export function findSimilarLaps(
  referenceLap: TelemetryPoint[],
  candidateLaps: TelemetryPoint[][],
  threshold: number = 0.85
): number[] {
  /**
   * Find indices of laps similar to reference lap.
   */
  return candidateLaps
    .map((lap, index) => ({
      index,
      similarity: calculateLapSimilarity(referenceLap, lap),
    }))
    .filter(item => item.similarity >= threshold)
    .map(item => item.index)
}

