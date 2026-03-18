import type { Metadata } from 'next'
import TransparencyContent from './TransparencyContent'

export const metadata: Metadata = {
  title: 'Transparency & Attribution | ApexView',
  description:
    'How ApexView works, where the data comes from, analysis methodology, ' +
    'privacy practices, and attribution. An independent academic project ' +
    'using publicly available Formula 1 data.',
}

export default function TransparencyPage() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <header className="border-l-4 border-f1red pl-4">
        <h1 className="font-heading text-3xl font-bold uppercase tracking-tight text-white md:text-4xl">
          Transparency & Attribution
        </h1>
        <p className="mt-2 text-gray-400">
          How this platform works, where the data comes from, and what the analysis means.
        </p>
      </header>

      <TransparencyContent />
    </div>
  )
}
