'use client'

import type { StrategicInsights, WeatherProfile } from '@/data/tracks/types'

interface StrategicNotesProps {
  strategicInsights: StrategicInsights
  weatherProfile: WeatherProfile
}

export function StrategicNotes({ strategicInsights, weatherProfile }: StrategicNotesProps) {
  return (
    <div className="rounded-lg border border-f1gray/30 bg-f1dark/50 p-4">
      <h3 className="mb-4 text-lg font-semibold text-white">Strategic Analysis</h3>
      
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Pit Strategy */}
        <div className="rounded-lg border border-f1gray/30 bg-f1dark/80 p-4">
          <div className="mb-3 flex items-center gap-2">
            <PitIcon />
            <h4 className="font-medium text-white">Pit Strategy</h4>
          </div>
          <div className="mb-3 rounded bg-f1red/10 px-3 py-2">
            <p className="text-sm font-medium text-f1red">{strategicInsights.pitStopWindow.typical}</p>
          </div>
          <ul className="space-y-2">
            {strategicInsights.pitStopWindow.factors.map((factor, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-gray-400">
                <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-yellow-500" />
                {factor}
              </li>
            ))}
          </ul>
        </div>

        {/* Key Strategic Factors */}
        <div className="rounded-lg border border-f1gray/30 bg-f1dark/80 p-4">
          <div className="mb-3 flex items-center gap-2">
            <StrategyIcon />
            <h4 className="font-medium text-white">Key Factors</h4>
          </div>
          <ul className="space-y-2">
            {strategicInsights.keyStrategicFactors.map((factor, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                <span className="mt-0.5 text-f1red">•</span>
                {factor}
              </li>
            ))}
          </ul>
        </div>

        {/* Safety Car & Historical Notes */}
        <div className="rounded-lg border border-f1gray/30 bg-f1dark/80 p-4">
          <div className="mb-3 flex items-center gap-2">
            <SafetyCarIcon />
            <h4 className="font-medium text-white">Safety Car</h4>
          </div>
          <div className="mb-3">
            <span className="text-sm text-gray-400">Likelihood: </span>
            <span className="text-sm font-medium text-yellow-400">
              {strategicInsights.safetyCarLikelihood}
            </span>
          </div>
          {strategicInsights.historicalNotes.length > 0 && (
            <div>
              <span className="text-xs font-medium uppercase tracking-wider text-gray-500">
                Historical Notes
              </span>
              <ul className="mt-2 space-y-1">
                {strategicInsights.historicalNotes.map((note, idx) => (
                  <li key={idx} className="text-sm text-gray-400">
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Weather Profile */}
        <div className="rounded-lg border border-f1gray/30 bg-f1dark/80 p-4">
          <div className="mb-3 flex items-center gap-2">
            <WeatherIcon />
            <h4 className="font-medium text-white">Weather Profile</h4>
          </div>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div className="min-w-0 overflow-hidden rounded bg-f1gray/20 px-2 py-1.5">
                <span className="text-xs text-gray-500">Conditions</span>
                <p className="break-words text-sm text-white">{weatherProfile.typical.conditions}</p>
              </div>
              <div className="min-w-0 overflow-hidden rounded bg-f1gray/20 px-2 py-1.5">
                <span className="text-xs text-gray-500">Rain</span>
                <p className="break-words text-sm text-white">{weatherProfile.typical.rainProbability}</p>
              </div>
            </div>
            <div>
              <span className="text-xs text-gray-500">Temperature Range</span>
              <div className="mt-1 flex items-center gap-2">
                <span className="rounded bg-blue-500/20 px-2 py-0.5 text-xs text-blue-400">
                  {weatherProfile.typical.airTemperature.min}
                </span>
                <span className="text-gray-500">→</span>
                <span className="rounded bg-orange-500/20 px-2 py-0.5 text-xs text-orange-400">
                  {weatherProfile.typical.airTemperature.max}
                </span>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Race time: {weatherProfile.typical.airTemperature.raceTime}
              </p>
            </div>
            <div>
              <span className="text-xs text-gray-500">Wind</span>
              <p className="text-sm text-gray-300">{weatherProfile.typical.wind}</p>
            </div>
            <p className="text-sm text-gray-400">{weatherProfile.impact}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Icons
function PitIcon() {
  return (
    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    </svg>
  )
}

function StrategyIcon() {
  return (
    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
    </svg>
  )
}

function SafetyCarIcon() {
  return (
    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  )
}

function WeatherIcon() {
  return (
    <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
    </svg>
  )
}
