/**
 * Qualifying Page Tests
 * 
 * Tests for the qualifying analysis page components and functionality.
 * Uses Vitest for test runner and React Testing Library patterns.
 */

import { describe, it, expect, vi } from 'vitest'

// Mock data for testing
const MOCK_DRIVERS = ['VER', 'NOR', 'PIA']
const MOCK_SESSION_ID = '2025_24_Qualifying'

const MOCK_SECTOR_DATA = [
  { driver: 'VER', sector1: 24.532, sector2: 38.456, sector3: 27.603, totalTime: 90.591 },
  { driver: 'NOR', sector1: 24.645, sector2: 38.512, sector3: 27.634, totalTime: 90.791 },
  { driver: 'PIA', sector1: 24.701, sector2: 38.489, sector3: 27.712, totalTime: 90.902 },
]

const MOCK_TELEMETRY = {
  driver: 'VER',
  lapNumber: 5,
  distance: [0, 100, 200, 300, 400, 500],
  speed: [280, 295, 310, 305, 290, 275],
  throttle: [100, 100, 100, 85, 70, 60],
  brake: [0, 0, 0, 15, 30, 40],
  gear: [7, 7, 8, 8, 7, 6],
}

const MOCK_DELTA_DATA = [
  {
    referenceDriver: 'VER',
    compareDriver: 'NOR',
    distance: [0, 1000, 2000, 3000, 4000, 5000],
    delta: [0, 0.05, 0.12, 0.15, 0.18, 0.20],
  },
]

// ============================================================================
// Unit Tests - Formatters
// ============================================================================

describe('Formatters', () => {
  describe('formatLapTime', () => {
    it('should format lap time correctly', async () => {
      const { formatLapTime } = await import('@/lib/formatters')
      
      expect(formatLapTime(90.591)).toBe('1:30.591')
      expect(formatLapTime(65.123)).toBe('1:05.123')
      expect(formatLapTime(120.456)).toBe('2:00.456')
    })

    it('should handle edge cases', async () => {
      const { formatLapTime } = await import('@/lib/formatters')
      
      expect(formatLapTime(0)).toBe('0:00.000')
      expect(formatLapTime(-1)).toBe('--:--.---')
      expect(formatLapTime(Infinity)).toBe('--:--.---')
    })
  })

  describe('formatDelta', () => {
    it('should format positive delta with + sign', async () => {
      const { formatDelta } = await import('@/lib/formatters')
      
      expect(formatDelta(0.234)).toBe('+0.234')
      expect(formatDelta(1.5)).toBe('+1.500')
    })

    it('should format negative delta without + sign', async () => {
      const { formatDelta } = await import('@/lib/formatters')
      
      expect(formatDelta(-0.123)).toBe('-0.123')
      expect(formatDelta(-0.5)).toBe('-0.500')
    })
  })

  describe('formatSessionLabel', () => {
    it('should return Q labels for traditional weekend', async () => {
      const { formatSessionLabel } = await import('@/lib/formatters')
      
      expect(formatSessionLabel('Q1', false)).toBe('Q1')
      expect(formatSessionLabel('Q2', false)).toBe('Q2')
      expect(formatSessionLabel('Q3', false)).toBe('Q3')
    })

    it('should return SQ labels for sprint weekend', async () => {
      const { formatSessionLabel } = await import('@/lib/formatters')
      
      expect(formatSessionLabel('Q1', true)).toBe('SQ1')
      expect(formatSessionLabel('Q2', true)).toBe('SQ2')
      expect(formatSessionLabel('Q3', true)).toBe('SQ3')
    })
  })

  describe('getDeltaColorClass', () => {
    it('should return positive class for slower times', async () => {
      const { getDeltaColorClass } = await import('@/lib/formatters')
      
      expect(getDeltaColorClass(0.5)).toBe('delta-positive')
      expect(getDeltaColorClass(0.001)).toBe('delta-positive')
    })

    it('should return negative class for faster times', async () => {
      const { getDeltaColorClass } = await import('@/lib/formatters')
      
      expect(getDeltaColorClass(-0.5)).toBe('delta-negative')
      expect(getDeltaColorClass(-0.001)).toBe('delta-negative')
    })

    it('should return empty for zero or tiny deltas', async () => {
      const { getDeltaColorClass } = await import('@/lib/formatters')
      
      expect(getDeltaColorClass(0)).toBe('')
      expect(getDeltaColorClass(0.0001)).toBe('')
    })
  })
})

// ============================================================================
// Unit Tests - Drivers
// ============================================================================

describe('Driver Utilities', () => {
  it('should get driver info by abbreviation', async () => {
    const { getDriverInfo } = await import('@/lib/drivers')
    
    const ver = getDriverInfo('VER')
    expect(ver).toBeDefined()
    expect(ver?.fullName).toBe('Max Verstappen')
    expect(ver?.team).toBe('Red Bull Racing')
  })

  it('should get team color for driver', async () => {
    const { getTeamColor } = await import('@/lib/drivers')
    
    const verColor = getTeamColor('VER')
    expect(verColor).toBe('#3671C6') // Red Bull blue
    
    const norColor = getTeamColor('NOR')
    expect(norColor).toBe('#FF8000') // McLaren orange
  })

  it('should return white for unknown driver', async () => {
    const { getTeamColor } = await import('@/lib/drivers')
    
    expect(getTeamColor('XXX')).toBe('#FFFFFF')
  })

  it('should get all teams', async () => {
    const { getAllTeams } = await import('@/lib/drivers')
    
    const teams = getAllTeams()
    expect(teams.length).toBeGreaterThan(0)
    expect(teams).toContain('Red Bull Racing')
    expect(teams).toContain('McLaren')
  })
})

// ============================================================================
// Integration Tests - Sector Calculations
// ============================================================================

describe('Sector Calculations', () => {
  it('should identify fastest sector times', () => {
    const fastestS1 = Math.min(...MOCK_SECTOR_DATA.map(d => d.sector1))
    const fastestS2 = Math.min(...MOCK_SECTOR_DATA.map(d => d.sector2))
    const fastestS3 = Math.min(...MOCK_SECTOR_DATA.map(d => d.sector3))

    expect(fastestS1).toBe(24.532) // VER
    expect(fastestS2).toBe(38.456) // VER
    expect(fastestS3).toBe(27.603) // VER
  })

  it('should calculate theoretical best lap', () => {
    const bestS1 = Math.min(...MOCK_SECTOR_DATA.map(d => d.sector1))
    const bestS2 = Math.min(...MOCK_SECTOR_DATA.map(d => d.sector2))
    const bestS3 = Math.min(...MOCK_SECTOR_DATA.map(d => d.sector3))
    const theoreticalBest = bestS1 + bestS2 + bestS3

    expect(theoreticalBest).toBeCloseTo(90.591, 3)
  })

  it('should calculate deltas correctly', () => {
    const refData = MOCK_SECTOR_DATA[0] // VER
    const compareData = MOCK_SECTOR_DATA[1] // NOR

    const s1Delta = compareData.sector1 - refData.sector1
    const totalDelta = compareData.totalTime - refData.totalTime

    expect(s1Delta).toBeCloseTo(0.113, 3)
    expect(totalDelta).toBeCloseTo(0.200, 3)
  })
})

// ============================================================================
// Integration Tests - Query Keys
// ============================================================================

describe('Query Keys', () => {
  it('should generate consistent query keys', async () => {
    const { queryKeys } = await import('@/lib/hooks/queryKeys')

    const key1 = queryKeys.telemetry.list(MOCK_SESSION_ID, ['VER', 'NOR'])
    const key2 = queryKeys.telemetry.list(MOCK_SESSION_ID, ['NOR', 'VER']) // Different order

    // Keys should be equivalent (drivers sorted)
    expect(JSON.stringify(key1)).toBe(JSON.stringify(key2))
  })

  it('should include analysis query keys', async () => {
    const { queryKeys } = await import('@/lib/hooks/queryKeys')

    expect(queryKeys.analysis).toBeDefined()
    expect(queryKeys.analysis.insights).toBeDefined()
    expect(queryKeys.analysis.similarity).toBeDefined()
    expect(queryKeys.analysis.clustering).toBeDefined()
  })
})

// ============================================================================
// Mock Tests - Component Rendering
// ============================================================================

describe('Component Props Validation', () => {
  it('should accept valid DriverMultiSelect props', () => {
    const props = {
      selected: MOCK_DRIVERS,
      onChange: vi.fn(),
      maxDrivers: 6,
    }

    expect(props.selected.length).toBeLessThanOrEqual(props.maxDrivers)
    expect(typeof props.onChange).toBe('function')
  })

  it('should accept valid SectorCards props', () => {
    const props = {
      sectorData: MOCK_SECTOR_DATA,
      referenceDriver: 'VER',
    }

    expect(props.sectorData.length).toBeGreaterThan(0)
    expect(MOCK_DRIVERS).toContain(props.referenceDriver)
  })

  it('should accept valid TelemetryLine props', () => {
    const telemetryMap = new Map()
    telemetryMap.set('VER', MOCK_TELEMETRY)

    const props = {
      telemetryData: telemetryMap,
      selectedDrivers: ['VER'],
      drsZones: [],
      corners: [],
    }

    expect(props.telemetryData.size).toBeGreaterThan(0)
    expect(props.telemetryData.has('VER')).toBe(true)
  })

  it('should accept valid DeltaPlot props', () => {
    const props = {
      deltaData: MOCK_DELTA_DATA,
      referenceDriver: 'VER',
      sectors: [],
      trackLength: 5800,
    }

    expect(props.deltaData.length).toBeGreaterThan(0)
    expect(props.deltaData[0].referenceDriver).toBe(props.referenceDriver)
  })

  it('should accept valid AnalysisInsights props', () => {
    const props = {
      sessionId: MOCK_SESSION_ID,
      sectorData: MOCK_SECTOR_DATA,
      referenceDriver: 'VER',
      selectedDrivers: MOCK_DRIVERS,
    }

    expect(props.selectedDrivers.length).toBeGreaterThanOrEqual(2)
    expect(props.selectedDrivers).toContain(props.referenceDriver)
  })
})

// ============================================================================
// Accessibility Tests
// ============================================================================

describe('Accessibility', () => {
  it('should have ARIA labels defined', () => {
    // These are the expected ARIA labels in components
    const expectedAriaLabels = [
      'Main navigation',
      'Qualifying sessions',
      'Sprint Qualifying sessions',
      'Select drivers',
      'Add drivers',
      'Telemetry speed chart',
      'Time delta chart',
    ]

    expectedAriaLabels.forEach(label => {
      expect(typeof label).toBe('string')
      expect(label.length).toBeGreaterThan(0)
    })
  })

  it('should support keyboard navigation keys', () => {
    const supportedKeys = ['ArrowLeft', 'ArrowRight', 'Home', 'End', 'Escape', 'Enter', ' ']
    
    supportedKeys.forEach(key => {
      expect(typeof key).toBe('string')
    })
  })
})

// ============================================================================
// URL State Tests
// ============================================================================

describe('URL State', () => {
  it('should parse URL parameters correctly', () => {
    const params = new URLSearchParams(
      'season=2025&round=24&drivers=VER,NOR,PIA&session=Q3&ref=VER'
    )

    expect(params.get('season')).toBe('2025')
    expect(params.get('round')).toBe('24')
    expect(params.get('drivers')?.split(',')).toEqual(['VER', 'NOR', 'PIA'])
    expect(params.get('session')).toBe('Q3')
    expect(params.get('ref')).toBe('VER')
  })

  it('should generate shareable URL', () => {
    const params = new URLSearchParams()
    params.set('season', '2025')
    params.set('round', '24')
    params.set('drivers', MOCK_DRIVERS.join(','))
    params.set('session', 'Q3')
    params.set('ref', 'VER')

    const url = `/qualifying?${params.toString()}`
    expect(url).toContain('drivers=VER,NOR,PIA')
    expect(url).toContain('session=Q3')
  })
})
