import type { DRSZone } from '@/../../packages/models/src/types'

/**
 * Represents a renderable DRS zone segment for visualization.
 * Wrap-around zones that cross the start/finish line are split into two segments.
 */
export interface DrsSegment {
  zoneNumber: number
  segmentIndex: number
  start: number
  end: number
}

/**
 * Converts DRS zones to renderable segments, handling wrap-around zones
 * that cross the start/finish line.
 * 
 * @param drsZones - Array of DRS zone definitions from track data
 * @param trackLength - Total track length in meters
 * @returns Array of segments ready for visualization
 * 
 * @example
 * // Suzuka's wrap-around zone becomes two segments:
 * // Input:  { activationPoint: 5700, endPoint: 400, wrapAround: true }
 * // Output: [{ start: 5700, end: 5807 }, { start: 0, end: 400 }]
 */
export function getDrsSegments(
  drsZones: DRSZone[],
  trackLength: number
): DrsSegment[] {
  const segments: DrsSegment[] = []

  drsZones.forEach((zone) => {
    if (zone.wrapAround) {
      // Wrap-around zone: split into two segments
      // Segment 1: From activation point to end of lap
      segments.push({
        zoneNumber: zone.zoneNumber,
        segmentIndex: 0,
        start: zone.activationPoint,
        end: trackLength,
      })
      // Segment 2: From start of lap to end point
      segments.push({
        zoneNumber: zone.zoneNumber,
        segmentIndex: 1,
        start: 0,
        end: zone.endPoint,
      })
    } else {
      // Standard zone: single segment
      segments.push({
        zoneNumber: zone.zoneNumber,
        segmentIndex: 0,
        start: zone.activationPoint,
        end: zone.endPoint,
      })
    }
  })

  return segments
}

/**
 * Checks if a given distance is within any DRS zone.
 * Handles wrap-around zones correctly.
 * 
 * @param distance - Distance along the track in meters
 * @param drsZones - Array of DRS zone definitions
 * @param trackLength - Total track length in meters
 * @returns True if the distance is within a DRS zone
 */
export function isInDrsZone(
  distance: number,
  drsZones: DRSZone[],
  trackLength: number
): boolean {
  return drsZones.some((zone) => {
    if (zone.wrapAround) {
      // Check both segments of wrap-around zone
      return (
        (distance >= zone.activationPoint && distance <= trackLength) ||
        (distance >= 0 && distance <= zone.endPoint)
      )
    }
    // Standard zone check
    return distance >= zone.activationPoint && distance <= zone.endPoint
  })
}

