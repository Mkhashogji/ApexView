'use client'

import { useState } from 'react'
import type { TechnicalInsights as TechnicalInsightsType, OvertakingAnalysis, DRSZoneDetail } from '@/data/tracks/types'

interface TechnicalInsightsProps {
  technicalInsights: TechnicalInsightsType
  overtakingAnalysis: OvertakingAnalysis
  drsZones: DRSZoneDetail[]
}

export function TechnicalInsights({ technicalInsights, overtakingAnalysis, drsZones }: TechnicalInsightsProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>('aero')

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section)
  }

  return (
    <div className="rounded-lg border border-f1gray/30 bg-f1dark/50 p-4">
      <h3 className="mb-4 text-lg font-semibold text-white">Technical Insights</h3>
      
      <div className="space-y-3">
        {/* Aerodynamic Setup */}
        <CollapsibleSection
          title="Aerodynamic Setup"
          icon={<AeroIcon />}
          isExpanded={expandedSection === 'aero'}
          onToggle={() => toggleSection('aero')}
        >
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Wing Level:</span>
              <WingLevelBadge level={technicalInsights.aerodynamicSetup.wingLevel} />
            </div>
            <p className="text-sm text-gray-300">{technicalInsights.aerodynamicSetup.explanation}</p>
          </div>
        </CollapsibleSection>

        {/* Tyre Management */}
        <CollapsibleSection
          title="Tyre Management"
          icon={<TyreIcon />}
          isExpanded={expandedSection === 'tyre'}
          onToggle={() => toggleSection('tyre')}
        >
          <div className="space-y-3">
            <div>
              <span className="text-xs font-medium uppercase tracking-wider text-gray-500">Compounds</span>
              <div className="mt-1 flex flex-wrap gap-2">
                {technicalInsights.tyreManagement.compounds.map((compound, idx) => (
                  <span key={idx} className="rounded bg-f1gray/30 px-2 py-1 text-xs text-gray-300">
                    {compound}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Primary Wear:</span>
              <span className="text-sm font-medium text-yellow-400">
                {technicalInsights.tyreManagement.primaryWearMechanism}
              </span>
            </div>
            <p className="text-sm text-gray-300">{technicalInsights.tyreManagement.explanation}</p>
            {technicalInsights.tyreManagement.strategicNote && (
              <div className="rounded bg-f1red/10 px-3 py-2">
                <p className="text-sm font-medium text-f1red">
                  {technicalInsights.tyreManagement.strategicNote}
                </p>
              </div>
            )}
          </div>
        </CollapsibleSection>

        {/* Surface Characteristics */}
        <CollapsibleSection
          title="Surface Characteristics"
          icon={<SurfaceIcon />}
          isExpanded={expandedSection === 'surface'}
          onToggle={() => toggleSection('surface')}
        >
          <div className="space-y-2">
            {technicalInsights.surfaceCharacteristics.resurfaced && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Resurfaced:</span>
                <span className="text-sm text-white">{technicalInsights.surfaceCharacteristics.resurfaced}</span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Grip Level:</span>
              <span className="text-sm text-white">{technicalInsights.surfaceCharacteristics.gripLevel}</span>
            </div>
            {technicalInsights.surfaceCharacteristics.impact && (
              <p className="text-sm text-gray-300">{technicalInsights.surfaceCharacteristics.impact}</p>
            )}
          </div>
        </CollapsibleSection>

        {/* Overtaking */}
        <CollapsibleSection
          title="Overtaking Analysis"
          icon={<OvertakeIcon />}
          isExpanded={expandedSection === 'overtake'}
          onToggle={() => toggleSection('overtake')}
        >
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <div>
                <span className="text-xs text-gray-500">Difficulty</span>
                <DifficultyBadge difficulty={overtakingAnalysis.difficulty} />
              </div>
              <div>
                <span className="text-xs text-gray-500">Primary Zone</span>
                <p className="text-sm font-medium text-white">{overtakingAnalysis.primaryZone}</p>
              </div>
            </div>
            <div>
              <span className="text-xs font-medium uppercase tracking-wider text-gray-500">Factors</span>
              <ul className="mt-1 space-y-1">
                {overtakingAnalysis.factors.map((factor, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-400">
                    <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-f1red" />
                    {factor}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded bg-blue-500/10 px-3 py-2">
              <p className="text-sm text-blue-300">{overtakingAnalysis.recommendation}</p>
            </div>
          </div>
        </CollapsibleSection>

        {/* DRS Zones */}
        <CollapsibleSection
          title={`DRS Zone${drsZones.length > 1 ? 's' : ''}`}
          icon={<DRSIcon />}
          isExpanded={expandedSection === 'drs'}
          onToggle={() => toggleSection('drs')}
        >
          <div className="space-y-3">
            {drsZones.map((zone) => (
              <div key={zone.zone} className="rounded border border-f1gray/30 bg-f1dark/80 p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-medium text-green-400">Zone {zone.zone}</span>
                  <EffectivenessBadge effectiveness={zone.effectiveness} />
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <span className="text-gray-500">Detection</span>
                    <p className="text-gray-300">{zone.detectionPoint}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Activation</span>
                    <p className="text-gray-300">{zone.activationPoint}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">End</span>
                    <p className="text-gray-300">{zone.deactivationPoint}</p>
                  </div>
                </div>
                <p className="mt-2 text-sm text-gray-400">{zone.description}</p>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      </div>
    </div>
  )
}

// Collapsible Section Component
interface CollapsibleSectionProps {
  title: string
  icon: React.ReactNode
  isExpanded: boolean
  onToggle: () => void
  children: React.ReactNode
}

function CollapsibleSection({ title, icon, isExpanded, onToggle, children }: CollapsibleSectionProps) {
  return (
    <div className="rounded-lg border border-f1gray/30 bg-f1dark/80">
      <button
        className="flex w-full items-center justify-between px-4 py-3 text-left"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3">
          <span className="text-gray-400">{icon}</span>
          <span className="font-medium text-white">{title}</span>
        </div>
        <svg
          className={`h-4 w-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div
        className={`transition-all duration-300 ${
          isExpanded ? 'max-h-[1000px] opacity-100' : 'max-h-0 overflow-hidden opacity-0'
        }`}
      >
        <div className="border-t border-f1gray/30 px-4 py-3 pb-4">{children}</div>
      </div>
    </div>
  )
}

// Badge Components
function WingLevelBadge({ level }: { level: string }) {
  const getColor = () => {
    if (level.includes('High') || level === 'Maximum') return 'text-orange-400 bg-orange-400/20'
    if (level.includes('Medium')) return 'text-yellow-400 bg-yellow-400/20'
    return 'text-blue-400 bg-blue-400/20'
  }
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${getColor()}`}>{level}</span>
}

function DifficultyBadge({ difficulty }: { difficulty: string }) {
  const getColor = () => {
    switch (difficulty) {
      case 'Very High': return 'text-red-400'
      case 'High': return 'text-orange-400'
      case 'Medium': return 'text-yellow-400'
      case 'Low': return 'text-green-400'
      case 'Very Low': return 'text-blue-400'
      default: return 'text-gray-400'
    }
  }
  return <p className={`text-sm font-medium ${getColor()}`}>{difficulty}</p>
}

function EffectivenessBadge({ effectiveness }: { effectiveness: string }) {
  const getColor = () => {
    switch (effectiveness) {
      case 'Very High': return 'text-green-400 bg-green-400/20'
      case 'High': return 'text-green-400 bg-green-400/20'
      case 'Medium': return 'text-yellow-400 bg-yellow-400/20'
      case 'Low': return 'text-red-400 bg-red-400/20'
      default: return 'text-gray-400 bg-gray-400/20'
    }
  }
  return <span className={`rounded px-2 py-0.5 text-xs font-medium ${getColor()}`}>{effectiveness}</span>
}

// Icons
function AeroIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  )
}

function TyreIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <circle cx="12" cy="12" r="9" strokeWidth={1.5} />
      <circle cx="12" cy="12" r="4" strokeWidth={1.5} />
    </svg>
  )
}

function SurfaceIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
    </svg>
  )
}

function OvertakeIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7l4-4m0 0l4 4m-4-4v18" />
    </svg>
  )
}

function DRSIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  )
}
