'use client'

import type { BenchmarkLapTimes } from '@/data/tracks/types'

interface BenchmarkTimesProps {
  benchmarks: BenchmarkLapTimes
}

export function BenchmarkTimes({ benchmarks }: BenchmarkTimesProps) {
  return (
    <div className="rounded-lg border border-f1gray/30 bg-f1dark/50 p-4">
      <h3 className="mb-4 text-lg font-semibold text-white">Benchmark Lap Times</h3>
      
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Qualifying Reference */}
        <div className="rounded-lg border border-f1gray/30 bg-f1dark/80 p-4">
          <h4 className="mb-3 text-sm font-medium uppercase tracking-wider text-gray-400">
            Qualifying Reference ({benchmarks.qualifyingReference.year})
          </h4>
          <div className="space-y-2">
            {benchmarks.qualifyingReference.top5.map((entry) => (
              <div
                key={entry.position}
                className={`flex items-center justify-between rounded px-3 py-2 ${
                  entry.position === 1 ? 'bg-f1red/20' : 'bg-f1gray/20'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                      entry.position === 1
                        ? 'bg-f1red text-white'
                        : 'bg-f1gray/50 text-gray-300'
                    }`}
                  >
                    {entry.position}
                  </span>
                  <span className="font-medium text-white">{entry.driver}</span>
                </div>
                <span className={`font-mono text-sm ${entry.position === 1 ? 'text-f1red' : 'text-gray-300'}`}>
                  {entry.time}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Sector Benchmarks */}
        <div className="rounded-lg border border-f1gray/30 bg-f1dark/80 p-4">
          <h4 className="mb-3 text-sm font-medium uppercase tracking-wider text-gray-400">
            Sector Benchmarks ({benchmarks.sectorBenchmarks.session})
          </h4>
          <div className="space-y-2">
            {benchmarks.sectorBenchmarks.sectors.map((sector) => (
              <div
                key={sector.sector}
                className="flex items-center justify-between rounded bg-f1gray/20 px-3 py-2"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-bold ${
                      sector.sector === 1
                        ? 'bg-red-500/30 text-red-400'
                        : sector.sector === 2
                          ? 'bg-blue-500/30 text-blue-400'
                          : 'bg-yellow-500/30 text-yellow-400'
                    }`}
                  >
                    S{sector.sector}
                  </span>
                  <span className="text-sm text-gray-400">{sector.driver}</span>
                </div>
                <span className="font-mono text-sm text-white">{sector.time}</span>
              </div>
            ))}
            <div className="mt-2 border-t border-f1gray/30 pt-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Theoretical Best</span>
                <span className="font-mono text-sm font-medium text-purple-400">
                  {benchmarks.sectorBenchmarks.overallIdealLap}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Race Pace */}
        <div className="rounded-lg border border-f1gray/30 bg-f1dark/80 p-4">
          <h4 className="mb-3 text-sm font-medium uppercase tracking-wider text-gray-400">
            Race Pace Comparison
          </h4>
          <div className="space-y-4">
            {benchmarks.racePaceBenchmarks.map((benchmark) => (
              <div key={benchmark.year}>
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs text-gray-500">{benchmark.year}</span>
                  <span className="text-xs text-gray-500">Mean lap: {benchmark.meanLapTime}</span>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center justify-between rounded bg-f1red/20 px-3 py-1.5">
                    <span className="font-medium text-white">{benchmark.fastestDriver}</span>
                    <span className="text-sm text-green-400">Leader</span>
                  </div>
                  {benchmark.gaps.map((gap) => (
                    <div
                      key={gap.driver}
                      className="flex items-center justify-between rounded bg-f1gray/20 px-3 py-1.5"
                    >
                      <span className="text-gray-300">{gap.driver}</span>
                      <span className="font-mono text-sm text-red-400">{gap.gap}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Speed */}
        <div className="rounded-lg border border-f1gray/30 bg-f1dark/80 p-4">
          <h4 className="mb-3 text-sm font-medium uppercase tracking-wider text-gray-400">
            Top Speed Reference
          </h4>
          <div className="space-y-4">
            <div>
              <span className="text-xs text-gray-500">Qualifying</span>
              <div className="mt-1 flex items-center justify-between">
                <span className="text-gray-300">{benchmarks.topSpeedReference.qualifying.fastest.driver}</span>
                <span className="font-mono text-lg font-bold text-white">
                  {benchmarks.topSpeedReference.qualifying.fastest.speed}
                </span>
              </div>
              <p className="text-xs text-gray-500">Range: {benchmarks.topSpeedReference.qualifying.range}</p>
            </div>
            <div className="border-t border-f1gray/30 pt-3">
              <span className="text-xs text-gray-500">Race</span>
              <div className="mt-1 grid grid-cols-2 gap-2">
                <div className="rounded bg-green-500/10 px-2 py-1.5">
                  <span className="text-xs text-gray-500">With DRS</span>
                  <p className="text-sm font-medium text-green-400">
                    {benchmarks.topSpeedReference.race.withDRS}
                  </p>
                </div>
                <div className="rounded bg-f1gray/20 px-2 py-1.5">
                  <span className="text-xs text-gray-500">Without DRS</span>
                  <p className="text-sm font-medium text-gray-300">
                    {benchmarks.topSpeedReference.race.withoutDRS}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Pole Position History */}
      {benchmarks.polePositions.length > 0 && (
        <div className="mt-4 rounded-lg border border-f1gray/30 bg-f1dark/80 p-4">
          <h4 className="mb-3 text-sm font-medium uppercase tracking-wider text-gray-400">
            Pole Position History
          </h4>
          <div className="flex flex-wrap gap-3">
            {benchmarks.polePositions.map((pole, idx) => (
              <div
                key={idx}
                className="rounded border border-f1gray/30 bg-f1dark/50 px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-white">{pole.year}</span>
                  {pole.driver && (
                    <span className="rounded bg-f1gray/30 px-1.5 py-0.5 text-xs text-gray-300">
                      {pole.driver}
                    </span>
                  )}
                </div>
                <p className="font-mono text-lg font-medium text-f1red">{pole.time}</p>
                {pole.note && <p className="text-xs text-gray-500">{pole.note}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
