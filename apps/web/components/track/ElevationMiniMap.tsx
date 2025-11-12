'use client'

export function ElevationMiniMap() {
  return (
    <div className="flex h-64 w-full items-center justify-center rounded border border-f1gray/50 bg-f1dark/50">
      <div className="text-center text-gray-500">
        <p className="text-lg">Elevation Profile</p>
        <p className="mt-2 text-sm">
          Height variation over track distance
        </p>
        <p className="mt-1 text-xs text-gray-600">
          SVG/Canvas integration placeholder
        </p>
      </div>
    </div>
  )
}

