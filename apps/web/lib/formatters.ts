export function formatLapTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = (seconds % 60).toFixed(3)
  return `${mins}:${secs.padStart(6, '0')}`
}

export function formatSpeed(kmh: number): string {
  return `${kmh.toFixed(1)} km/h`
}

export function formatDistance(meters: number): string {
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(2)} km`
  }
  return `${meters.toFixed(0)} m`
}

export function formatDelta(seconds: number): string {
  const sign = seconds >= 0 ? '+' : ''
  return `${sign}${seconds.toFixed(3)}s`
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`
}

