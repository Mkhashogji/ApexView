/**
 * Lightweight Circuit SVG Filename Lookup
 *
 * Maps F1 round numbers to SVG track map filenames in public/tracks/.
 * Filenames match the Gumroad f1-track-vectors bundle naming convention.
 *
 * This is intentionally separated from the full Track Intelligence module
 * (304 KiB) to keep imports lightweight — the SectorMapPanel only needs
 * the filename string to fetch the SVG asset.
 *
 * Pattern follows data/tracks/race-lookup.ts (circuitName + fuelEffectPerKg).
 */

const CIRCUIT_SVG_MAP: Record<number, string> = {
  1:  'australia',       // Australian GP
  2:  'china',           // Chinese GP
  3:  'japan',           // Japanese GP
  4:  'bahrain',         // Bahrain GP
  5:  'saudi_arabia',    // Saudi Arabian GP
  6:  'miami',           // Miami GP
  7:  'imola',           // Emilia Romagna GP
  8:  'monaco',          // Monaco GP
  9:  'spain',           // Spanish GP
  10: 'canada',          // Canadian GP
  11: 'austria',         // Austrian GP
  12: 'silverstone',     // British GP
  13: 'spa',             // Belgian GP
  14: 'hungary',         // Hungarian GP
  15: 'netherlands',     // Dutch GP
  16: 'monza',           // Italian GP
  17: 'azerbaijan',      // Azerbaijan GP
  18: 'singapore',       // Singapore GP
  19: 'usa',             // United States GP
  20: 'mexico',          // Mexican GP
  21: 'brazil',          // Brazilian GP
  22: 'las_vegas',       // Las Vegas GP
  23: 'qatar',           // Qatar GP
  24: 'abudhabi',        // Abu Dhabi GP
}

/**
 * Get SVG filename for a round number.
 * Returns undefined if the round is not mapped (e.g., new circuit added mid-season).
 */
export function getCircuitSVGFilename(round: number): string | undefined {
  return CIRCUIT_SVG_MAP[round]
}
