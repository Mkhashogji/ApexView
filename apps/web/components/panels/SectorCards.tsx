'use client'

import { SectorComparison, TheoreticalBestLap } from '@/../../packages/models/src/types'
import { getTeamColor, getDriverInfo } from '@/lib/drivers'
import { formatLapTime, formatSectorTime, formatDelta, getDeltaColorClass } from '@/lib/formatters'
import { useMemo } from 'react'

interface SectorCardsProps {
  sectorData: SectorComparison[]
  referenceDriver: string
  /** Pole position time for delta comparison */
  poleTime?: number
}

/** Sector card data structure */
interface SectorFastest {
  sectorNumber: number
  time: number
  driver: string
  color: string
}

export function SectorCards({ sectorData, referenceDriver, poleTime }: SectorCardsProps) {
  // Filter out invalid data
  const validSectorData = useMemo(() => {
    // Guard: Check if sectorData exists and is an array
    if (!sectorData || !Array.isArray(sectorData)) return []
    
    return sectorData.filter(
      (d) => 
        d &&
        typeof d.sector1 === 'number' && isFinite(d.sector1) &&
        typeof d.sector2 === 'number' && isFinite(d.sector2) &&
        typeof d.sector3 === 'number' && isFinite(d.sector3) &&
        typeof d.totalTime === 'number' && isFinite(d.totalTime)
    )
  }, [sectorData])

  // Find fastest in each sector
  const sectorFastests = useMemo<SectorFastest[]>(() => {
    // Guard: Need at least one valid entry to find fastest
    if (!validSectorData || validSectorData.length === 0) return []

    const sectors = [
      { key: 'sector1' as const, num: 1 },
      { key: 'sector2' as const, num: 2 },
      { key: 'sector3' as const, num: 3 },
    ]

    return sectors.map(({ key, num }) => {
      // Use first element as initial value to avoid reduce on empty array
      const fastest = validSectorData.reduce((prev, curr) => {
        if (!prev) return curr
        if (!curr) return prev
        return (curr[key] ?? Infinity) < (prev[key] ?? Infinity) ? curr : prev
      }, validSectorData[0])
      
      return {
        sectorNumber: num,
        time: fastest?.[key] ?? 0,
        driver: fastest?.driver ?? '',
        color: getTeamColor(fastest?.driver ?? ''),
      }
    })
  }, [validSectorData])

  // Calculate theoretical best lap for each driver
  const theoreticalBestLaps = useMemo<TheoreticalBestLap[]>(() => {
    // Guard: Need valid data to calculate
    if (!validSectorData || validSectorData.length === 0) return []

    // Get overall fastest sectors with guards against empty arrays
    const s1Times = validSectorData.map(d => d.sector1).filter(t => typeof t === 'number' && isFinite(t))
    const s2Times = validSectorData.map(d => d.sector2).filter(t => typeof t === 'number' && isFinite(t))
    const s3Times = validSectorData.map(d => d.sector3).filter(t => typeof t === 'number' && isFinite(t))
    
    // Guard: If any sector has no valid times, return empty
    if (s1Times.length === 0 || s2Times.length === 0 || s3Times.length === 0) return []
    
    const bestS1 = Math.min(...s1Times)
    const bestS2 = Math.min(...s2Times)
    const bestS3 = Math.min(...s3Times)
    const theoreticalBest = bestS1 + bestS2 + bestS3

    return validSectorData.map(d => ({
      driver: d.driver ?? '',
      bestSector1: d.sector1 ?? 0,
      bestSector2: d.sector2 ?? 0,
      bestSector3: d.sector3 ?? 0,
      theoreticalTime: (d.sector1 ?? 0) + (d.sector2 ?? 0) + (d.sector3 ?? 0),
      actualBestTime: d.totalTime ?? 0,
      potentialGain: (d.totalTime ?? 0) - theoreticalBest,
    })).sort((a, b) => a.actualBestTime - b.actualBestTime)
  }, [validSectorData])

  // Overall theoretical best lap
  const overallTheoreticalBest = useMemo(() => {
    // Guard: Need exactly 3 sector fastests
    if (!sectorFastests || sectorFastests.length !== 3) return null
    
    const time = sectorFastests.reduce((sum, s) => sum + (s?.time ?? 0), 0)
    
    // Guard: Calculate pole position safely
    const totalTimes = validSectorData
      ?.map(d => d.totalTime)
      .filter(t => typeof t === 'number' && isFinite(t)) ?? []
    
    const polePosition = totalTimes.length > 0 ? Math.min(...totalTimes) : null
    
    return {
      time,
      deltaToPole: polePosition !== null ? time - polePosition : null,
    }
  }, [sectorFastests, validSectorData])

  // Reference driver data
  const refData = useMemo(() => 
    validSectorData.find((d) => d.driver === referenceDriver),
    [validSectorData, referenceDriver]
  )

  // Calculate delta helper
  const calculateDelta = (time: number, refTime: number) => {
    const delta = time - refTime
    return {
      value: delta,
      formatted: formatDelta(delta),
      colorClass: getDeltaColorClass(delta),
      isSlower: delta > 0,
    }
  }

  // Check if a time is the fastest for that sector
  const isFastestSector = (driver: string, sectorNum: number) => {
    const sectorFastest = sectorFastests.find(s => s.sectorNumber === sectorNum)
    return sectorFastest?.driver === driver
  }

  if (validSectorData.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        <p>No sector data available</p>
        <p className="text-xs mt-1 text-gray-600">Select drivers with valid lap times</p>
      </div>
    )
  }

  // Get fastest times for each sector (for showing absolute vs delta)
  const fastestS1 = sectorFastests.find(s => s.sectorNumber === 1)?.time ?? 0
  const fastestS2 = sectorFastests.find(s => s.sectorNumber === 2)?.time ?? 0
  const fastestS3 = sectorFastests.find(s => s.sectorNumber === 3)?.time ?? 0

  return (
    <div className="space-y-4">
      {/* Compact Sector Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm" role="table">
          <thead>
            <tr className="border-b border-f1gray text-gray-400 text-xs uppercase tracking-wide">
              <th className="pb-2 text-left font-medium">Driver</th>
              <th className="pb-2 text-right font-medium">S1</th>
              <th className="pb-2 text-right font-medium">S2</th>
              <th className="pb-2 text-right font-medium">S3</th>
            </tr>
          </thead>
          <tbody>
            {theoreticalBestLaps.map((data) => (
                <tr 
                  key={data.driver} 
                  className="border-b border-f1gray/20"
                >
                  {/* Driver */}
                  <td className="py-2">
                    <div className="flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: getTeamColor(data.driver) }}
                        aria-hidden="true"
                      />
                      <span className="font-medium text-sm">{data.driver}</span>
                    </div>
                  </td>
                  
                  {/* Sector 1 - Absolute time for fastest, delta for others */}
                  <td className={`py-2 text-right font-mono text-sm ${
                    isFastestSector(data.driver, 1) ? 'text-purple-sector font-bold' : ''
                  }`}>
                    {isFastestSector(data.driver, 1)
                      ? formatSectorTime(data.bestSector1)
                      : <span className={getDeltaColorClass(data.bestSector1 - fastestS1)}>
                          {formatDelta(data.bestSector1 - fastestS1)}
                        </span>
                    }
                  </td>
                  
                  {/* Sector 2 */}
                  <td className={`py-2 text-right font-mono text-sm ${
                    isFastestSector(data.driver, 2) ? 'text-purple-sector font-bold' : ''
                  }`}>
                    {isFastestSector(data.driver, 2)
                      ? formatSectorTime(data.bestSector2)
                      : <span className={getDeltaColorClass(data.bestSector2 - fastestS2)}>
                          {formatDelta(data.bestSector2 - fastestS2)}
                        </span>
                    }
                  </td>
                  
                  {/* Sector 3 */}
                  <td className={`py-2 text-right font-mono text-sm ${
                    isFastestSector(data.driver, 3) ? 'text-purple-sector font-bold' : ''
                  }`}>
                    {isFastestSector(data.driver, 3)
                      ? formatSectorTime(data.bestSector3)
                      : <span className={getDeltaColorClass(data.bestSector3 - fastestS3)}>
                          {formatDelta(data.bestSector3 - fastestS3)}
                        </span>
                    }
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Fastest Sectors Summary */}
      <div className="text-xs text-gray-400 space-y-1">
        <p className="font-medium text-gray-300">Fastest sectors:</p>
        <p>
          S1 <span className="text-purple-sector font-medium">{sectorFastests[0]?.driver}</span>
          {' | '}
          S2 <span className="text-purple-sector font-medium">{sectorFastests[1]?.driver}</span>
          {' | '}
          S3 <span className="text-purple-sector font-medium">{sectorFastests[2]?.driver}</span>
        </p>
      </div>

      {/* Theoretical Best Lap */}
      {overallTheoreticalBest && (
        <div className="pt-3 border-t border-f1gray/30">
          <p className="text-xs text-gray-400 uppercase tracking-wide">Theoretical Best</p>
          <p className="font-mono text-lg font-bold text-purple-sector mt-1">
            {formatLapTime(overallTheoreticalBest.time)}
          </p>
          {overallTheoreticalBest.deltaToPole !== null && (
            <p className={`font-mono text-sm ${
              overallTheoreticalBest.deltaToPole < 0 ? 'text-delta-negative' : 'text-gray-400'
            }`}>
              {formatDelta(overallTheoreticalBest.deltaToPole)} vs pole
            </p>
          )}
        </div>
      )}
    </div>
  )
}

