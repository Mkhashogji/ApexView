'use client'

import { SectorComparison } from '@/../../packages/models/src/types'
import { getTeamColor } from '@/lib/drivers'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface SectorCardsProps {
  sectorData: SectorComparison[]
  referenceDriver: string
}

export function SectorCards({ sectorData, referenceDriver }: SectorCardsProps) {
  if (sectorData.length === 0) {
    return (
      <div className="rounded-lg border border-f1gray bg-f1gray/20 p-6 text-center text-gray-500">
        No sector data available
      </div>
    )
  }

  // Filter out invalid data (entries with undefined sector times)
  const validSectorData = sectorData.filter(
    (d) => 
      d.sector1 != null && 
      d.sector2 != null && 
      d.sector3 != null && 
      d.totalTime != null
  )

  if (validSectorData.length === 0) {
    return (
      <div className="rounded-lg border border-f1gray bg-f1gray/20 p-6 text-center text-gray-500">
        No valid sector data available
      </div>
    )
  }

  // Find reference driver data
  const refData = validSectorData.find((d) => d.driver === referenceDriver)
  
  // Calculate deltas for each sector
  const calculateDelta = (time: number, refTime: number) => {
    const delta = time - refTime
    return {
      value: Math.abs(delta),
      formatted: delta >= 0 ? `+${delta.toFixed(3)}` : delta.toFixed(3),
      isSlower: delta > 0,
    }
  }

  // Find fastest in each sector
  const fastestSector1 = Math.min(...validSectorData.map((d) => d.sector1))
  const fastestSector2 = Math.min(...validSectorData.map((d) => d.sector2))
  const fastestSector3 = Math.min(...validSectorData.map((d) => d.sector3))

  return (
    <div className="space-y-4">
      {/* Sector Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Sector 1 */}
        <div className="rounded-lg border border-f1gray bg-f1gray/20 p-4">
          <h3 className="text-sm font-medium text-gray-400">Sector 1</h3>
          <p className="mt-2 text-2xl font-bold">{fastestSector1.toFixed(3)}s</p>
          <div className="mt-2 flex items-center gap-2">
            <div
              className="h-3 w-3 rounded-full"
              style={{
                backgroundColor: getTeamColor(
                  validSectorData.find((d) => d.sector1 === fastestSector1)?.driver || ''
                ),
              }}
            />
            <span className="text-sm text-gray-400">
              {validSectorData.find((d) => d.sector1 === fastestSector1)?.driver}
            </span>
          </div>
        </div>

        {/* Sector 2 */}
        <div className="rounded-lg border border-f1gray bg-f1gray/20 p-4">
          <h3 className="text-sm font-medium text-gray-400">Sector 2</h3>
          <p className="mt-2 text-2xl font-bold">{fastestSector2.toFixed(3)}s</p>
          <div className="mt-2 flex items-center gap-2">
            <div
              className="h-3 w-3 rounded-full"
              style={{
                backgroundColor: getTeamColor(
                  validSectorData.find((d) => d.sector2 === fastestSector2)?.driver || ''
                ),
              }}
            />
            <span className="text-sm text-gray-400">
              {validSectorData.find((d) => d.sector2 === fastestSector2)?.driver}
            </span>
          </div>
        </div>

        {/* Sector 3 */}
        <div className="rounded-lg border border-f1gray bg-f1gray/20 p-4">
          <h3 className="text-sm font-medium text-gray-400">Sector 3</h3>
          <p className="mt-2 text-2xl font-bold">{fastestSector3.toFixed(3)}s</p>
          <div className="mt-2 flex items-center gap-2">
            <div
              className="h-3 w-3 rounded-full"
              style={{
                backgroundColor: getTeamColor(
                  validSectorData.find((d) => d.sector3 === fastestSector3)?.driver || ''
                ),
              }}
            />
            <span className="text-sm text-gray-400">
              {validSectorData.find((d) => d.sector3 === fastestSector3)?.driver}
            </span>
          </div>
        </div>
      </div>

      {/* Detailed Comparison Table */}
      {refData && (
        <div className="rounded-lg border border-f1gray bg-f1gray/20 p-6">
          <h3 className="mb-4 text-lg font-semibold">
            Sector Comparison (vs {referenceDriver})
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-f1gray">
                  <th className="pb-2 text-left">Driver</th>
                  <th className="pb-2 text-right">Sector 1</th>
                  <th className="pb-2 text-right">Δ</th>
                  <th className="pb-2 text-right">Sector 2</th>
                  <th className="pb-2 text-right">Δ</th>
                  <th className="pb-2 text-right">Sector 3</th>
                  <th className="pb-2 text-right">Δ</th>
                  <th className="pb-2 text-right">Total</th>
                  <th className="pb-2 text-right">Δ</th>
                </tr>
              </thead>
              <tbody>
                {validSectorData.map((data) => {
                  const delta1 = calculateDelta(data.sector1, refData.sector1)
                  const delta2 = calculateDelta(data.sector2, refData.sector2)
                  const delta3 = calculateDelta(data.sector3, refData.sector3)
                  const deltaTotal = calculateDelta(data.totalTime, refData.totalTime)

                  return (
                    <tr key={data.driver} className="border-b border-f1gray/50">
                      <td className="py-2">
                        <div className="flex items-center gap-2">
                          <div
                            className="h-3 w-3 rounded-full"
                            style={{ backgroundColor: getTeamColor(data.driver) }}
                          />
                          <span className="font-medium">{data.driver}</span>
                        </div>
                      </td>
                      <td className="py-2 text-right">{data.sector1.toFixed(3)}s</td>
                      <td
                        className={`py-2 text-right text-xs ${
                          data.driver === referenceDriver
                            ? 'text-gray-500'
                            : delta1.isSlower
                            ? 'text-red-400'
                            : 'text-green-400'
                        }`}
                      >
                        {data.driver === referenceDriver ? '-' : delta1.formatted}
                      </td>
                      <td className="py-2 text-right">{data.sector2.toFixed(3)}s</td>
                      <td
                        className={`py-2 text-right text-xs ${
                          data.driver === referenceDriver
                            ? 'text-gray-500'
                            : delta2.isSlower
                            ? 'text-red-400'
                            : 'text-green-400'
                        }`}
                      >
                        {data.driver === referenceDriver ? '-' : delta2.formatted}
                      </td>
                      <td className="py-2 text-right">{data.sector3.toFixed(3)}s</td>
                      <td
                        className={`py-2 text-right text-xs ${
                          data.driver === referenceDriver
                            ? 'text-gray-500'
                            : delta3.isSlower
                            ? 'text-red-400'
                            : 'text-green-400'
                        }`}
                      >
                        {data.driver === referenceDriver ? '-' : delta3.formatted}
                      </td>
                      <td className="py-2 text-right font-bold">{data.totalTime.toFixed(3)}s</td>
                      <td
                        className={`py-2 text-right text-sm font-medium ${
                          data.driver === referenceDriver
                            ? 'text-gray-500'
                            : deltaTotal.isSlower
                            ? 'text-red-400'
                            : 'text-green-400'
                        }`}
                      >
                        {data.driver === referenceDriver ? '-' : deltaTotal.formatted}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

