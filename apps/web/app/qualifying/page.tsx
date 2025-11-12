'use client'

import { useState, useEffect } from 'react'
import { DriverMultiSelect } from '@/components/filters/DriverMultiSelect'
import { SessionSwitch } from '@/components/filters/SessionSwitch'
import { TelemetryLine } from '@/components/charts/TelemetryLine'
import { DeltaPlot } from '@/components/charts/DeltaPlot'
import { SectorCards } from '@/components/panels/SectorCards'
import { AIInsights } from '@/components/panels/AIInsights'
import { fetchTelemetry, fetchDelta, fetchSectors } from '@/lib/api'
import { Telemetry, DeltaData, SectorComparison } from '@/../../packages/models/src/types'

export default function QualifyingPage() {
  // State
  const [selectedDrivers, setSelectedDrivers] = useState<string[]>(['VER', 'NOR', 'HAM'])
  const [referenceDriver, setReferenceDriver] = useState<string>('VER')
  const [season] = useState<number>(2025)
  const [round] = useState<number>(1)
  const [sessionId] = useState<string>('2025_1_Qualifying')
  
  const [telemetryData, setTelemetryData] = useState<Map<string, Telemetry>>(new Map())
  const [deltaData, setDeltaData] = useState<DeltaData[]>([])
  const [sectorData, setSectorData] = useState<SectorComparison[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch data when drivers change
  useEffect(() => {
    const loadData = async () => {
      if (selectedDrivers.length === 0) return

      setLoading(true)
      setError(null)

      try {
        // Fetch telemetry
        const telemetry = await fetchTelemetry(sessionId, selectedDrivers)
        const telemetryMap = new Map<string, Telemetry>()
        telemetry.forEach((t) => {
          telemetryMap.set(t.driver, t)
        })
        setTelemetryData(telemetryMap)

        // Fetch sectors
        const sectors = await fetchSectors(sessionId, selectedDrivers)
        setSectorData(sectors)

        // Fetch delta analysis
        const compareDrivers = selectedDrivers.filter((d) => d !== referenceDriver)
        if (compareDrivers.length > 0) {
          const deltas = await fetchDelta(sessionId, referenceDriver, compareDrivers)
          setDeltaData(deltas)
        } else {
          setDeltaData([])
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data')
        console.error('Error loading data:', err)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [selectedDrivers, referenceDriver, sessionId])

  // Update reference driver if it's not in selected drivers
  useEffect(() => {
    if (!selectedDrivers.includes(referenceDriver) && selectedDrivers.length > 0) {
      setReferenceDriver(selectedDrivers[0])
    }
  }, [selectedDrivers, referenceDriver])

  return (
    <div className="space-y-6">
      <div className="border-l-4 border-f1red pl-4">
        <h1 className="text-4xl font-bold">Qualifying Analysis</h1>
        <p className="mt-2 text-gray-400">
          Multi-driver lap comparison with delta charts and sector analysis
        </p>
        <p className="mt-1 text-sm text-gray-500">
          Season {season} - Round {round} - Qualifying
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 rounded-lg border border-f1gray bg-f1gray/20 p-4">
        <DriverMultiSelect
          selected={selectedDrivers}
          onChange={setSelectedDrivers}
        />
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Reference Driver:</label>
          <select
            value={referenceDriver}
            onChange={(e) => setReferenceDriver(e.target.value)}
            className="rounded bg-f1dark px-3 py-2 text-sm"
          >
            {selectedDrivers.map((driver) => (
              <option key={driver} value={driver}>
                {driver}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Loading/Error States */}
      {loading && (
        <div className="rounded-lg border border-f1gray bg-f1gray/20 p-6 text-center">
          <p>Loading data...</p>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-500 bg-red-500/20 p-6 text-center">
          <p className="text-red-400">Error: {error}</p>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Sector Cards */}
          <SectorCards
            sectorData={sectorData}
            referenceDriver={referenceDriver}
          />

          {/* Telemetry Comparison */}
          <div className="rounded-lg border border-f1gray bg-f1gray/20 p-6">
            <h2 className="mb-4 text-2xl font-semibold">Speed Trace</h2>
            <TelemetryLine
              telemetryData={telemetryData}
              selectedDrivers={selectedDrivers}
            />
          </div>

          {/* Delta Plot */}
          <div className="rounded-lg border border-f1gray bg-f1gray/20 p-6">
            <h2 className="mb-4 text-2xl font-semibold">Delta to Reference</h2>
            <DeltaPlot
              deltaData={deltaData}
              referenceDriver={referenceDriver}
            />
          </div>

          {/* AI Insights */}
          <AIInsights
            sectorData={sectorData}
            referenceDriver={referenceDriver}
          />
        </>
      )}
    </div>
  )
}

