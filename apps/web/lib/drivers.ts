import { DriverInfo } from '@/../../packages/models/src/types'
import driversData from '@/data/drivers.json'

export const DRIVERS_2025: DriverInfo[] = driversData.drivers

// Backward compatibility alias
export const DRIVERS_2024 = DRIVERS_2025

export function getDriverInfo(abbreviation: string): DriverInfo | undefined {
  return DRIVERS_2025.find((driver) => driver.abbreviation === abbreviation)
}

export function getTeamColor(abbreviation: string): string {
  const driver = getDriverInfo(abbreviation)
  return driver?.teamColor || '#FFFFFF'
}

export function getDriversByTeam(team: string): DriverInfo[] {
  return DRIVERS_2025.filter((driver) => driver.team === team)
}

export function getAllTeams(): string[] {
  const teams = new Set(DRIVERS_2025.map((driver) => driver.team))
  return Array.from(teams)
}

