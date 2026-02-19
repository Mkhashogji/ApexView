/**
 * Lightweight Race Page Track Lookup
 *
 * Provides ONLY the two fields the Race page needs from Track Intelligence:
 *   - circuitName: for chart title display
 *   - fuelEffectPerKg: for fuel correction calculation
 *
 * This avoids importing the full Track Intelligence module (304 KiB) which
 * contains detailed circuit descriptions, corner data, sector breakdowns,
 * strategic insights, etc. that the Race page never uses.
 *
 * Values are kept in sync with the individual circuit files in this directory.
 */

interface RaceTrackInfo {
  circuitName: string
  fuelEffectPerKg: number
}

const RACE_TRACK_LOOKUP: Record<number, RaceTrackInfo> = {
  1:  { circuitName: 'Albert Park Grand Prix Circuit',                   fuelEffectPerKg: 0.032 },
  2:  { circuitName: 'Shanghai International Circuit',                   fuelEffectPerKg: 0.032 },
  3:  { circuitName: 'Suzuka International Racing Course',               fuelEffectPerKg: 0.029 },
  4:  { circuitName: 'Bahrain International Circuit',                    fuelEffectPerKg: 0.034 },
  5:  { circuitName: 'Jeddah Corniche Circuit',                          fuelEffectPerKg: 0.031 },
  6:  { circuitName: 'Miami International Autodrome',                    fuelEffectPerKg: 0.033 },
  7:  { circuitName: 'Autodromo Internazionale Enzo e Dino Ferrari',     fuelEffectPerKg: 0.031 },
  8:  { circuitName: 'Circuit de Monaco',                                fuelEffectPerKg: 0.036 },
  9:  { circuitName: 'Circuit de Barcelona-Catalunya',                   fuelEffectPerKg: 0.033 },
  10: { circuitName: 'Circuit Gilles Villeneuve',                        fuelEffectPerKg: 0.034 },
  11: { circuitName: 'Red Bull Ring',                                    fuelEffectPerKg: 0.031 },
  12: { circuitName: 'Silverstone Circuit',                              fuelEffectPerKg: 0.028 },
  13: { circuitName: 'Circuit de Spa-Francorchamps',                     fuelEffectPerKg: 0.029 },
  14: { circuitName: 'Hungaroring',                                      fuelEffectPerKg: 0.035 },
  15: { circuitName: 'Circuit Zandvoort',                                fuelEffectPerKg: 0.032 },
  16: { circuitName: 'Autodromo Nazionale Monza',                        fuelEffectPerKg: 0.028 },
  17: { circuitName: 'Baku City Circuit',                                fuelEffectPerKg: 0.032 },
  18: { circuitName: 'Marina Bay Street Circuit',                        fuelEffectPerKg: 0.036 },
  19: { circuitName: 'Circuit of the Americas',                          fuelEffectPerKg: 0.033 },
  20: { circuitName: 'Autódromo Hermanos Rodríguez',                     fuelEffectPerKg: 0.031 },
  21: { circuitName: 'Autódromo José Carlos Pace',                       fuelEffectPerKg: 0.033 },
  22: { circuitName: 'Las Vegas Strip Circuit',                          fuelEffectPerKg: 0.031 },
  23: { circuitName: 'Lusail International Circuit',                     fuelEffectPerKg: 0.032 },
  24: { circuitName: 'Yas Marina Circuit',                               fuelEffectPerKg: 0.033 },
}

/** Get fuel correction factor for a given round. Returns 0.032 default if round not found. */
export function getRaceFuelEffect(round: number): number {
  return RACE_TRACK_LOOKUP[round]?.fuelEffectPerKg ?? 0.032
}

/** Get circuit name for a given round. Returns undefined if round not found. */
export function getRaceCircuitName(round: number): string | undefined {
  return RACE_TRACK_LOOKUP[round]?.circuitName
}
