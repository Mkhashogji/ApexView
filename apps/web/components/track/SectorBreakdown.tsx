'use client'

import { useState } from 'react'
import type { SectorBreakdown as SectorBreakdownType } from '@/data/tracks/types'

interface SectorBreakdownProps {
  sectors: [SectorBreakdownType, SectorBreakdownType, SectorBreakdownType]
}

export function SectorBreakdown({ sectors }: SectorBreakdownProps) {
  const [expandedSector, setExpandedSector] = useState<number | null>(null)

  return (
    <div className="rounded-lg border border-f1gray/30 bg-f1dark/50 p-4">
      <h3 className="mb-4 text-lg font-semibold text-white">Sector Breakdown</h3>
      
      <div className="grid gap-4 md:grid-cols-3">
        {sectors.map((sector) => (
          <SectorCard
            key={sector.sector}
            sector={sector}
            isExpanded={expandedSector === sector.sector}
            onToggle={() => setExpandedSector(
              expandedSector === sector.sector ? null : sector.sector
            )}
          />
        ))}
      </div>
    </div>
  )
}

interface SectorCardProps {
  sector: SectorBreakdownType
  isExpanded: boolean
  onToggle: () => void
}

function SectorCard({ sector, isExpanded, onToggle }: SectorCardProps) {
  return (
    <div
      className="cursor-pointer rounded-lg border border-f1gray/30 bg-f1dark/80 transition-all hover:border-f1gray/50 overflow-hidden flex flex-col"
      onClick={onToggle}
    >
      {/* Header with sector color */}
      <div
        className="rounded-t-lg px-4 py-2 flex-shrink-0"
        style={{ backgroundColor: `${sector.color}20`, borderBottom: `2px solid ${sector.color}` }}
      >
        <div className="flex items-center justify-between">
          <span className="text-lg font-bold" style={{ color: sector.color }}>
            Sector {sector.sector}
          </span>
          <span className="text-sm text-gray-400">{sector.corners}</span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 flex flex-col flex-1">
        {/* Description - flex-1 to take available space */}
        <div className="flex-1">
          <p className={`text-sm leading-relaxed text-gray-300 ${
            isExpanded ? '' : 'line-clamp-4'
          }`}>{sector.description}</p>

          {/* Expandable Details */}
          {isExpanded && (
            <div className="mt-3">
              {/* Key Features */}
              <div className="mb-4">
                <h5 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-500">
                  Key Features
                </h5>
                <ul className="space-y-1.5">
                  {sector.keyFeatures.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm leading-relaxed text-gray-400">
                      <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full" style={{ backgroundColor: sector.color }} />
                      <span className="break-words">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Critical Corners */}
              <div>
                <h5 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-500">
                  Critical Corners
                </h5>
                <ul className="space-y-1.5">
                  {sector.criticalCorners.map((corner, idx) => (
                    <li key={idx} className="text-sm font-medium leading-relaxed text-gray-300 break-words">
                      {corner}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Expand indicator - always at bottom */}
        <button
          className="mt-4 flex w-full items-center justify-center gap-1 text-xs text-gray-500 hover:text-gray-300 pt-3 border-t border-f1gray/20 flex-shrink-0"
          onClick={(e) => {
            e.stopPropagation()
            onToggle()
          }}
        >
          {isExpanded ? 'Show less' : 'Show more'}
          <svg
            className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>
    </div>
  )
}
