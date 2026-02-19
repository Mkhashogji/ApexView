/**
 * F1 tyre compound color mappings and display utilities.
 * Used by Race Pace box plot (Phase 2) and Tyre Degradation (Phase 3).
 */

/** Compound abbreviations (full name → short form) */
export const COMPOUND_SHORT: Record<string, string> = {
  SOFT: 'S',
  MEDIUM: 'M',
  HARD: 'H',
  INTERMEDIATE: 'I',
  WET: 'W',
}

/** Compound colors keyed by abbreviation (matches Plotly trace naming) */
export const COMPOUND_COLOR: Record<string, string> = {
  S: '#FF3333',
  M: '#FCD34D',
  H: '#FFFFFF',
  I: '#4ADE80',
  W: '#60A5FA',
}

/** Compound colors keyed by full name (for Phase 3 compound tabs) */
export const COMPOUND_COLORS_FULL: Record<string, string> = {
  SOFT: '#FF3333',
  MEDIUM: '#FCD34D',
  HARD: '#FFFFFF',
  INTERMEDIATE: '#4ADE80',
  WET: '#60A5FA',
}

/** Human-readable display names */
export const COMPOUND_DISPLAY_NAMES: Record<string, string> = {
  SOFT: 'Soft',
  MEDIUM: 'Medium',
  HARD: 'Hard',
  INTERMEDIATE: 'Intermediate',
  WET: 'Wet',
}

/**
 * Get compound color from either full name or abbreviation.
 * @example getCompoundColor('SOFT') => '#FF3333'
 * @example getCompoundColor('S') => '#FF3333'
 */
export function getCompoundColor(compound: string): string {
  const upper = compound.toUpperCase()
  return COMPOUND_COLORS_FULL[upper] ?? COMPOUND_COLOR[upper] ?? '#9CA3AF'
}
