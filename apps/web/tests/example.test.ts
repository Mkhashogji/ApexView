import { describe, it, expect } from 'vitest'
import { formatLapTime, formatSpeed } from '../lib/formatters'

describe('formatters', () => {
  it('should format lap time correctly', () => {
    expect(formatLapTime(92.837)).toBe('1:32.837')
    expect(formatLapTime(64.123)).toBe('1:04.123')
  })

  it('should format speed correctly', () => {
    expect(formatSpeed(342.5)).toBe('342.5 km/h')
    expect(formatSpeed(150)).toBe('150.0 km/h')
  })
})

