'use client'

import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { queryKeys } from './queryKeys'
import { getCircuitSVGFilename } from '@/lib/circuitMap'

// =============================================================================
// Types
// =============================================================================

/**
 * Parsed SVG data extracted from a circuit track map.
 *
 * Contains the `d` attribute of each sector path plus the SVG viewBox
 * for correct aspect ratio rendering.
 *
 * Gumroad f1-track-vectors SVGs contain pre-drawn sector paths (3 pairs
 * of gray outline + colored overlay) — no stroke-dasharray computation
 * is needed. The three sector paths together form the complete circuit.
 */
export interface CircuitSVGData {
  /** Sector 1 path d-attribute */
  sector1PathD: string
  /** Sector 2 path d-attribute */
  sector2PathD: string
  /** Sector 3 path d-attribute */
  sector3PathD: string
  /** SVG viewBox attribute for correct aspect ratio */
  viewBox: string
}

// =============================================================================
// SVG Fetch + Parse
// =============================================================================

/**
 * Fetch an SVG file from public/tracks/ and parse it into CircuitSVGData.
 * Returns null if the SVG is unavailable or cannot be parsed.
 */
async function fetchAndParseCircuitSVG(
  round: number
): Promise<CircuitSVGData | null> {
  const filename = getCircuitSVGFilename(round)
  if (!filename) return null

  try {
    const response = await fetch(`/tracks/${filename}.svg`)
    if (!response.ok) return null

    const svgText = await response.text()
    return parseCircuitSVG(svgText)
  } catch {
    // Network error, CORS, etc. — graceful degradation
    return null
  }
}

/**
 * Parse SVG text to extract sector paths.
 *
 * Uses browser-native DOMParser to extract path `d` attributes.
 * No dangerouslySetInnerHTML — paths are rendered as JSX <path> elements.
 *
 * Gumroad SVGs have NO class/id on path elements. Each sector is drawn
 * as a pair of paths (thick gray outline + thin colored overlay) with
 * identical d-attributes. We select by stroke colour:
 *   S1 = #EF4444 (red), S2 = #3B82F6 (blue), S3 = #FBBF24 (amber)
 *
 * The three sector paths together form the complete circuit — there is
 * no separate full-track-outline path.
 */
function parseCircuitSVG(svgText: string): CircuitSVGData | null {
  const parser = new DOMParser()
  const doc = parser.parseFromString(svgText, 'image/svg+xml')

  // Check for parse errors
  const parseError = doc.querySelector('parsererror')
  if (parseError) return null

  const svgEl = doc.querySelector('svg')
  if (!svgEl) return null

  const viewBox = svgEl.getAttribute('viewBox') ?? '0 0 800 600'

  // ─── Extract sector path d-attributes by stroke colour ──────────
  // Gumroad SVGs use consistent stroke colours across all 24 circuits.
  // Each sector is drawn twice (gray + colored) with the same d-attr.
  const s1Path = doc.querySelector('path[stroke="#EF4444"]')?.getAttribute('d')
  const s2Path = doc.querySelector('path[stroke="#3B82F6"]')?.getAttribute('d')
  const s3Path = doc.querySelector('path[stroke="#FBBF24"]')?.getAttribute('d')

  // All three sector paths must be present for valid rendering
  if (!s1Path || !s2Path || !s3Path) return null

  return {
    sector1PathD: s1Path,
    sector2PathD: s2Path,
    sector3PathD: s3Path,
    viewBox,
  }
}

// =============================================================================
// Query Hook
// =============================================================================

/**
 * React Query hook for fetching and parsing a circuit SVG track map.
 *
 * SVGs are static assets that never change — uses Infinity staleTime.
 * Parsed SVG data is kept in cache for 1 hour to avoid re-parsing.
 *
 * @param round - F1 round number (1-24)
 * @param enabled - Typically from useVisibility() for deferred loading
 */
export function useCircuitSVGQuery(round: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.practice.circuitSVG(round),
    queryFn: () => fetchAndParseCircuitSVG(round),
    enabled: round > 0 && enabled,
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60, // 1 hour cache
    placeholderData: keepPreviousData,
  })
}
