'use client'

import type { CircuitCharacteristics, EnergyProfile, CharacteristicRating } from '@/data/tracks/types'

interface CharacteristicsBarsProps {
  characteristics: CircuitCharacteristics
  energyProfile: EnergyProfile
}

const CHARACTERISTIC_LABELS: Record<keyof CircuitCharacteristics, string> = {
  traction: 'Traction',
  tyreStress: 'Tyre Stress',
  asphaltGrip: 'Asphalt Grip',
  asphaltAbrasion: 'Asphalt Abrasion',
  braking: 'Braking',
  lateral: 'Lateral',
  downforce: 'Downforce',
  trackEvolution: 'Track Evolution',
}

const CHARACTERISTIC_DESCRIPTIONS: Record<keyof CircuitCharacteristics, string> = {
  traction: 'Rear tyre stress from acceleration',
  tyreStress: 'Overall tyre degradation severity',
  asphaltGrip: 'Surface grip level',
  asphaltAbrasion: 'Surface roughness on tyres',
  braking: 'Braking zone intensity',
  lateral: 'Cornering force demands',
  downforce: 'Aerodynamic load requirements',
  trackEvolution: 'Grip improvement over weekend',
}

export function CharacteristicsBars({ characteristics, energyProfile }: CharacteristicsBarsProps) {
  const characteristicEntries = Object.entries(characteristics) as [keyof CircuitCharacteristics, CharacteristicRating][]

  return (
    <div className="rounded-lg border border-f1gray/30 bg-f1dark/50 p-4">
      <h3 className="mb-4 text-lg font-semibold text-white">Circuit Characteristics</h3>
      
      {/* Pirelli-style Rating Bars */}
      <div className="grid gap-3 md:grid-cols-2">
        {characteristicEntries.map(([key, value]) => (
          <CharacteristicBar
            key={key}
            label={CHARACTERISTIC_LABELS[key]}
            description={CHARACTERISTIC_DESCRIPTIONS[key]}
            rating={value}
            isHighlighted={value === 5}
          />
        ))}
      </div>

      {/* Energy Profile */}
      <div className="mt-6 border-t border-f1gray/30 pt-4">
        <h4 className="mb-3 text-sm font-medium uppercase tracking-wider text-gray-400">
          Energy Demand Profile
        </h4>
        <div className="flex flex-wrap gap-4">
          <EnergyIndicator label="Longitudinal" level={energyProfile.longitudinal} />
          <EnergyIndicator label="Lateral" level={energyProfile.lateral} />
        </div>
      </div>
    </div>
  )
}

interface CharacteristicBarProps {
  label: string
  description: string
  rating: CharacteristicRating
  isHighlighted?: boolean
}

function CharacteristicBar({ label, description, rating, isHighlighted }: CharacteristicBarProps) {
  return (
    <div className="group">
      <div className="mb-1 flex items-center justify-between">
        <span className={`text-sm font-medium ${isHighlighted ? 'text-f1red' : 'text-gray-300'}`}>
          {label}
        </span>
        <span className={`text-xs font-bold ${isHighlighted ? 'text-f1red' : 'text-gray-400'}`}>
          {rating}/5
        </span>
      </div>
      
      {/* Rating Bar */}
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((level) => (
          <div
            key={level}
            className={`h-2 flex-1 rounded-sm transition-colors ${
              level <= rating
                ? isHighlighted
                  ? 'bg-f1red'
                  : rating >= 4
                    ? 'bg-yellow-500'
                    : 'bg-blue-500'
                : 'bg-f1gray/30'
            }`}
          />
        ))}
      </div>
      
      {/* Hover Description */}
      <p className="mt-1 text-xs text-gray-500 opacity-0 transition-opacity group-hover:opacity-100">
        {description}
      </p>
    </div>
  )
}

interface EnergyIndicatorProps {
  label: string
  level: string
}

function EnergyIndicator({ label, level }: EnergyIndicatorProps) {
  const getLevelColor = (lvl: string) => {
    switch (lvl) {
      case 'Maximum':
        return 'text-f1red bg-f1red/20'
      case 'High':
        return 'text-orange-400 bg-orange-400/20'
      case 'Medium':
        return 'text-yellow-400 bg-yellow-400/20'
      case 'Low':
        return 'text-blue-400 bg-blue-400/20'
      case 'Minimum':
        return 'text-green-400 bg-green-400/20'
      default:
        return 'text-gray-400 bg-gray-400/20'
    }
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-gray-400">{label}:</span>
      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${getLevelColor(level)}`}>
        {level}
      </span>
    </div>
  )
}
