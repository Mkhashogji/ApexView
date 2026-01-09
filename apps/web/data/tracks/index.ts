/**
 * Track Intelligence Data Index
 * 
 * Central export for all track intelligence data.
 * Data is indexed by round number for easy lookup.
 */

import type { TrackIntelligence } from './types'
import { australiaTrackIntelligence } from './australia'
import { chinaTrackIntelligence } from './china'
import { suzukaTrackIntelligence } from './suzuka'
import { bahrainTrackIntelligence } from './bahrain'
import { jeddahTrackIntelligence } from './jeddah'
import { miamiTrackIntelligence } from './miami'
import { imolaTrackIntelligence } from './imola'
import { monacoTrackIntelligence } from './monaco'
import { spainTrackIntelligence } from './spain'
import { canadaTrackIntelligence } from './canada'
import { austriaTrackIntelligence } from './austria'
import { silverstoneTrackIntelligence } from './silverstone'
import { belgiumTrackIntelligence } from './belgium'
import { hungaryTrackIntelligence } from './hungary'
import { zandvoortTrackIntelligence } from './zandvoort'
import { monzaTrackIntelligence } from './monza'
import { azerbaijanTrackIntelligence } from './azerbaijan'
import { singaporeTrackIntelligence } from './singapore'
import { usaTrackIntelligence } from './usa'
import { mexicoTrackIntelligence } from './mexico'
import { brazilTrackIntelligence } from './brazil'
import { lasVegasTrackIntelligence } from './las-vegas'
import { qatarTrackIntelligence } from './qatar'
import { abuDhabiTrackIntelligence } from './abu-dhabi'

// Re-export types for convenience
export * from './types'

// Re-export individual track data
export { australiaTrackIntelligence } from './australia'
export { chinaTrackIntelligence } from './china'
export { suzukaTrackIntelligence } from './suzuka'
export { bahrainTrackIntelligence } from './bahrain'
export { jeddahTrackIntelligence } from './jeddah'
export { miamiTrackIntelligence } from './miami'
export { imolaTrackIntelligence } from './imola'
export { monacoTrackIntelligence } from './monaco'
export { spainTrackIntelligence } from './spain'
export { canadaTrackIntelligence } from './canada'
export { austriaTrackIntelligence } from './austria'
export { silverstoneTrackIntelligence } from './silverstone'
export { belgiumTrackIntelligence } from './belgium'
export { hungaryTrackIntelligence } from './hungary'
export { zandvoortTrackIntelligence } from './zandvoort'
export { monzaTrackIntelligence } from './monza'
export { azerbaijanTrackIntelligence } from './azerbaijan'
export { singaporeTrackIntelligence } from './singapore'
export { usaTrackIntelligence } from './usa'
export { mexicoTrackIntelligence } from './mexico'
export { brazilTrackIntelligence } from './brazil'
export { lasVegasTrackIntelligence } from './las-vegas'
export { qatarTrackIntelligence } from './qatar'
export { abuDhabiTrackIntelligence } from './abu-dhabi'

/**
 * Track intelligence data indexed by round number.
 * Add new circuits here as they are implemented.
 */
export const TRACK_INTELLIGENCE: Record<number, TrackIntelligence> = {
  1: australiaTrackIntelligence,   // Australian GP
  2: chinaTrackIntelligence,       // Chinese GP
  3: suzukaTrackIntelligence,      // Japanese GP
  4: bahrainTrackIntelligence,     // Bahrain GP
  5: jeddahTrackIntelligence,      // Saudi Arabian GP
  6: miamiTrackIntelligence,       // Miami GP
  7: imolaTrackIntelligence,       // Emilia Romagna GP
  8: monacoTrackIntelligence,      // Monaco GP
  9: spainTrackIntelligence,       // Spanish GP
  10: canadaTrackIntelligence,     // Canadian GP
  11: austriaTrackIntelligence,    // Austrian GP
  12: silverstoneTrackIntelligence, // British GP
  13: belgiumTrackIntelligence,    // Belgian GP
  14: hungaryTrackIntelligence,    // Hungarian GP
  15: zandvoortTrackIntelligence,  // Dutch GP
  16: monzaTrackIntelligence,      // Italian GP
  17: azerbaijanTrackIntelligence, // Azerbaijan GP
  18: singaporeTrackIntelligence,  // Singapore GP
  19: usaTrackIntelligence,        // United States GP
  20: mexicoTrackIntelligence,     // Mexican GP
  21: brazilTrackIntelligence,     // Brazilian GP
  22: lasVegasTrackIntelligence,   // Las Vegas GP
  23: qatarTrackIntelligence,      // Qatar GP
  24: abuDhabiTrackIntelligence,   // Abu Dhabi GP
}

/**
 * Get track intelligence data by round number.
 * Returns undefined if no editorial data is available for the circuit.
 */
export function getTrackIntelligence(round: number): TrackIntelligence | undefined {
  return TRACK_INTELLIGENCE[round]
}

/**
 * Check if track intelligence data is available for a round.
 */
export function hasTrackIntelligence(round: number): boolean {
  return round in TRACK_INTELLIGENCE
}

/**
 * Get all rounds that have track intelligence data.
 */
export function getAvailableTrackIntelligenceRounds(): number[] {
  return Object.keys(TRACK_INTELLIGENCE).map(Number).sort((a, b) => a - b)
}
