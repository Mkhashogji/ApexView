import { DriverInfo } from '@/../../packages/models/src/types'
import driversData from '@/data/drivers.json'

// Guard: Ensure drivers data is valid
const rawDrivers = driversData?.drivers
export const DRIVERS_2025: DriverInfo[] = Array.isArray(rawDrivers) ? rawDrivers : []

// Backward compatibility alias
export const DRIVERS_2024 = DRIVERS_2025

/**
 * T-Cam designation for 2025 season
 * In F1, the #1 driver typically has a black T-Cam, #2 driver has yellow
 * This is used to differentiate teammates when both are selected on telemetry charts
 */
export const DRIVER_TCAM: Record<string, 'black' | 'yellow'> = {
  // Red Bull Racing
  'VER': 'black',
  'TSU': 'yellow',
  // Ferrari
  'LEC': 'black',
  'HAM': 'yellow',
  // Mercedes
  'RUS': 'black',
  'ANT': 'yellow',
  // McLaren
  'NOR': 'black',
  'PIA': 'yellow',
  // Aston Martin
  'ALO': 'black',
  'STR': 'yellow',
  // Alpine
  'GAS': 'black',
  'COL': 'yellow',
  // Haas F1 Team
  'OCO': 'black',
  'BEA': 'yellow',
  // RB
  'LAW': 'black',
  'HAD': 'yellow',
  // Williams
  'ALB': 'black',
  'SAI': 'yellow',
  // Kick Sauber
  'HUL': 'black',
  'BOR': 'yellow',
}

export function getDriverInfo(abbreviation: string): DriverInfo | undefined {
  if (!abbreviation || !DRIVERS_2025 || DRIVERS_2025.length === 0) return undefined
  return DRIVERS_2025.find((driver) => driver?.abbreviation === abbreviation)
}

export function getTeamColor(abbreviation: string): string {
  if (!abbreviation) return '#FFFFFF'
  const driver = getDriverInfo(abbreviation)
  return driver?.teamColor || '#FFFFFF'
}

export function getDriversByTeam(team: string): DriverInfo[] {
  if (!team || !DRIVERS_2025 || DRIVERS_2025.length === 0) return []
  return DRIVERS_2025.filter((driver) => driver?.team === team)
}

export function getAllTeams(): string[] {
  if (!DRIVERS_2025 || DRIVERS_2025.length === 0) return []
  const teams = new Set(DRIVERS_2025.map((driver) => driver?.team).filter(Boolean) as string[])
  return Array.from(teams)
}

/**
 * Get the T-Cam designation for a driver
 * Black T-Cam = primary driver (solid line)
 * Yellow T-Cam = secondary driver (dashed line)
 */
export function getDriverTCam(abbreviation: string): 'black' | 'yellow' {
  if (!abbreviation) return 'black'
  return DRIVER_TCAM[abbreviation] || 'black'
}

/**
 * Get all teammate drivers for a given driver
 * Returns abbreviations of all drivers on the same team
 */
export function getTeammateDrivers(driverCode: string): string[] {
  const driver = getDriverInfo(driverCode)
  if (!driver || !driver.team) return []
  return getDriversByTeam(driver.team).map(d => d.abbreviation)
}

/**
 * Resolve team color for either a driver abbreviation or a team name.
 * In driver mode, identifier is a driver abbreviation (e.g., 'VER') — direct lookup.
 * In team mode, identifier is a team name (e.g., 'Red Bull Racing') — resolve via
 * first driver on that team.
 *
 * Used by Phase 3 Tyre Degradation components where the analysis mode
 * determines whether identifiers are drivers or teams.
 */
export function getTeamColorForMode(
  identifier: string,
  mode: 'driver' | 'team',
): string {
  if (mode === 'driver') {
    return getTeamColor(identifier)
  }
  // In team mode, identifier is team name — get first driver on that team
  const teamDrivers = getDriversByTeam(identifier)
  return teamDrivers.length > 0
    ? getTeamColor(teamDrivers[0].abbreviation)
    : '#FFFFFF'
}

