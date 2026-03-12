import Link from 'next/link'

interface FeatureCardProps {
  href: string
  title: string
  question: string
  capabilities: string[]
}

/**
 * Feature card linking to an analytical page.
 *
 * Uses the existing `card-panel` class with group-coordinated hover:
 * red border glow, title colour change, and arrow fade-in.
 * Question text uses flex-1 for consistent card heights.
 * Capability pills below a divider in font-mono.
 */
export default function FeatureCard({
  href,
  title,
  question,
  capabilities,
}: FeatureCardProps) {
  return (
    <Link
      href={href}
      className="card-panel group flex flex-col transition-all duration-200 hover:border-f1red hover:shadow-glow-red-sm focus-ring"
    >
      {/* Title + arrow */}
      <div className="flex items-center justify-between">
        <h3 className="font-heading text-lg font-bold uppercase tracking-wide text-white transition-colors duration-200 group-hover:text-f1red">
          {title}
        </h3>
        <span
          className="text-f1red opacity-0 transition-opacity duration-200 group-hover:opacity-100"
          aria-hidden="true"
        >
          &rarr;
        </span>
      </div>

      {/* Question — flex-1 ensures consistent card heights */}
      <p className="mt-3 flex-1 text-sm leading-relaxed text-gray-400">
        {question}
      </p>

      {/* Capability pills below divider */}
      <div className="mt-4 border-t border-f1gray/50 pt-3">
        <div className="flex flex-wrap gap-2">
          {capabilities.map((cap) => (
            <span
              key={cap}
              className="rounded-full border border-f1gray/50 bg-f1gray/10 px-3 py-1 font-mono text-xs text-gray-400"
            >
              {cap}
            </span>
          ))}
        </div>
      </div>
    </Link>
  )
}
