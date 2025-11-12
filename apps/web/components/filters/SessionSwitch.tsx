'use client'

import { useState } from 'react'

type SessionType = 'traditional' | 'sprint'

export function SessionSwitch() {
  const [sessionType, setSessionType] = useState<SessionType>('traditional')

  return (
    <div>
      <label className="block text-sm font-medium text-gray-400">Session Format</label>
      <div className="mt-2 flex rounded-md border border-f1gray">
        <button
          onClick={() => setSessionType('traditional')}
          className={`px-4 py-2 text-sm transition-colors ${
            sessionType === 'traditional'
              ? 'bg-f1red text-white'
              : 'bg-transparent text-gray-400 hover:text-white'
          }`}
        >
          Traditional
        </button>
        <button
          onClick={() => setSessionType('sprint')}
          className={`px-4 py-2 text-sm transition-colors ${
            sessionType === 'sprint'
              ? 'bg-f1red text-white'
              : 'bg-transparent text-gray-400 hover:text-white'
          }`}
        >
          Sprint
        </button>
      </div>
    </div>
  )
}

