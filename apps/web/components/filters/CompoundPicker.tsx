'use client'

import { useState } from 'react'

const COMPOUNDS = [
  { id: 'SOFT', name: 'Soft', color: '#FF3333' },
  { id: 'MEDIUM', name: 'Medium', color: '#FFEB3B' },
  { id: 'HARD', name: 'Hard', color: '#F5F5F5' },
  { id: 'INTERMEDIATE', name: 'Intermediate', color: '#43A047' },
  { id: 'WET', name: 'Wet', color: '#1976D2' },
]

export function CompoundPicker() {
  const [selectedCompounds, setSelectedCompounds] = useState<string[]>([])

  const toggleCompound = (compoundId: string) => {
    setSelectedCompounds(prev =>
      prev.includes(compoundId)
        ? prev.filter(id => id !== compoundId)
        : [...prev, compoundId]
    )
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-400">Tyre Compounds</label>
      <div className="mt-2 flex flex-wrap gap-2">
        {COMPOUNDS.map(compound => (
          <button
            key={compound.id}
            onClick={() => toggleCompound(compound.id)}
            className={`rounded-md border px-3 py-1 text-sm transition-colors ${
              selectedCompounds.includes(compound.id)
                ? 'border-transparent text-black'
                : 'border-f1gray text-gray-400 hover:border-gray-400'
            }`}
            style={{
              backgroundColor: selectedCompounds.includes(compound.id) ? compound.color : 'transparent',
            }}
          >
            {compound.name}
          </button>
        ))}
      </div>
    </div>
  )
}

