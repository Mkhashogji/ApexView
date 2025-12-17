import { QualifyingSessionPart } from '@/../../packages/models/src/types'

// ============================================================================
// Lap Time Formatters
// ============================================================================

/**
 * Format lap time in seconds to MM:SS.mmm format
 * @example formatLapTime(90.591) => "1:30.591"
 */
export function formatLapTime(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return '--:--.---'
  const mins = Math.floor(seconds / 60)
  const secs = (seconds % 60).toFixed(3)
  return `${mins}:${secs.padStart(6, '0')}`
}

/**
 * Format sector time in seconds to SS.mmm format
 * @example formatSectorTime(24.532) => "24.532"
 */
export function formatSectorTime(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return '--.---'
  return seconds.toFixed(3)
}

// ============================================================================
// Delta Formatters
// ============================================================================

/**
 * Format delta time with sign and appropriate precision
 * @example formatDelta(0.234) => "+0.234"
 * @example formatDelta(-0.123) => "-0.123"
 */
export function formatDelta(seconds: number): string {
  if (!isFinite(seconds)) return '-'
  const sign = seconds >= 0 ? '+' : ''
  return `${sign}${seconds.toFixed(3)}`
}

/**
 * Get CSS class for delta value coloring
 * @returns 'delta-positive' (red/slower), 'delta-negative' (green/faster), or empty
 */
export function getDeltaColorClass(seconds: number): string {
  if (!isFinite(seconds) || Math.abs(seconds) < 0.001) return ''
  return seconds > 0 ? 'delta-positive' : 'delta-negative'
}

/**
 * Format delta with color class information
 * Returns object with formatted string and color class
 */
export function formatDeltaWithColor(seconds: number): { 
  formatted: string
  colorClass: string
  isSlower: boolean
} {
  return {
    formatted: formatDelta(seconds),
    colorClass: getDeltaColorClass(seconds),
    isSlower: seconds > 0,
  }
}

// ============================================================================
// Session Formatters
// ============================================================================

/**
 * Format session label based on qualifying part and weekend type
 * @example formatSessionLabel('Q3', false) => "Q3"
 * @example formatSessionLabel('Q3', true) => "SQ3"
 */
export function formatSessionLabel(
  sessionPart: 'Q1' | 'Q2' | 'Q3',
  isSprintWeekend: boolean
): QualifyingSessionPart {
  if (isSprintWeekend) {
    return `S${sessionPart}` as QualifyingSessionPart
  }
  return sessionPart
}

/**
 * Get all qualifying session parts for a weekend type
 */
export function getQualifyingSessionParts(isSprintWeekend: boolean): QualifyingSessionPart[] {
  if (isSprintWeekend) {
    return ['SQ1', 'SQ2', 'SQ3']
  }
  return ['Q1', 'Q2', 'Q3']
}

// ============================================================================
// Speed & Distance Formatters
// ============================================================================

/**
 * Format speed in km/h
 * @example formatSpeed(325.5) => "325.5 km/h"
 */
export function formatSpeed(kmh: number): string {
  if (!isFinite(kmh)) return '-- km/h'
  return `${kmh.toFixed(1)} km/h`
}

/**
 * Format distance in meters or kilometers
 * @example formatDistance(500) => "500 m"
 * @example formatDistance(5800) => "5.80 km"
 */
export function formatDistance(meters: number): string {
  if (!isFinite(meters)) return '-- m'
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(2)} km`
  }
  return `${meters.toFixed(0)} m`
}

// ============================================================================
// Percentage & Similarity Formatters
// ============================================================================

/**
 * Format percentage value
 * @example formatPercentage(92.5) => "92.5%"
 */
export function formatPercentage(value: number): string {
  if (!isFinite(value)) return '--%'
  return `${value.toFixed(1)}%`
}

/**
 * Format similarity score (0-1) as percentage
 * @example formatSimilarity(0.925) => "92.5%"
 */
export function formatSimilarity(score: number): string {
  if (!isFinite(score)) return '--%'
  return `${(score * 100).toFixed(1)}%`
}

// ============================================================================
// Driver Formatters
// ============================================================================

/**
 * Format driver name for display (abbreviation or full name)
 */
export function formatDriverName(
  abbreviation: string, 
  fullName?: string,
  style: 'abbr' | 'full' | 'both' = 'abbr'
): string {
  switch (style) {
    case 'full':
      return fullName || abbreviation
    case 'both':
      return fullName ? `${abbreviation} - ${fullName}` : abbreviation
    default:
      return abbreviation
  }
}

