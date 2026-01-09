'use client'

import type { CircuitOverview as CircuitOverviewType, CircuitStats } from '@/data/tracks/types'

interface CircuitOverviewProps {
  overview: CircuitOverviewType
  stats: CircuitStats
}

export function CircuitOverview({ overview, stats }: CircuitOverviewProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-white">{overview.grandPrixName}</h1>
            <span className="rounded-full bg-f1red/20 px-3 py-1 text-sm font-medium text-f1red">
              {overview.circuitType}
            </span>
          </div>
          <p className="mt-1 text-lg text-gray-400">{overview.circuitName}</p>
          <p className="text-sm text-gray-500">
            {overview.location} • First GP: {overview.firstGrandPrix}
          </p>
        </div>
      </div>

      {/* Description */}
      <div className="rounded-lg border border-f1gray/30 bg-f1dark/50 p-4">
        <p className="text-sm leading-relaxed text-gray-300">{overview.description}</p>
      </div>

      {/* Key Statistics Grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard
          label="Lap Length"
          value={`${stats.lapLength.km} km`}
          subValue={`${stats.lapLength.miles} mi`}
        />
        <StatCard
          label="Race Distance"
          value={`${stats.raceDistance.km.toFixed(0)} km`}
          subValue={`${stats.numberOfLaps} laps`}
        />
        <StatCard
          label="Corners"
          value={stats.numberOfCorners.toString()}
          subValue="turns"
        />
        <StatCard
          label="DRS Zones"
          value={stats.drsZones.toString()}
          subValue={stats.drsZones === 1 ? 'zone' : 'zones'}
        />
        <StatCard
          label="Lap Record"
          value={stats.lapRecord.time}
          subValue={stats.lapRecord.driver ? `${stats.lapRecord.driver} (${stats.lapRecord.year})` : 'TBD'}
        />
        {stats.tyreSpecs && (
          <StatCard
            label="Tyre Pressure"
            value={stats.tyreSpecs.minStartingPressures.front}
            subValue={`F / ${stats.tyreSpecs.minStartingPressures.rear} R`}
          />
        )}
      </div>
    </div>
  )
}

interface StatCardProps {
  label: string
  value: string
  subValue?: string
}

function StatCard({ label, value, subValue }: StatCardProps) {
  return (
    <div className="rounded-lg border border-f1gray/30 bg-f1dark/50 p-3 text-center">
      <p className="text-xs font-medium uppercase tracking-wider text-gray-500">{label}</p>
      <p className="mt-1 text-xl font-bold text-white">{value}</p>
      {subValue && <p className="text-xs text-gray-400">{subValue}</p>}
    </div>
  )
}
