'use client'

/**
 * Footer component with data source attribution.
 */
export function Footer() {
  const currentYear = new Date().getFullYear()
  
  return (
    <footer 
      className="border-t border-f1gray bg-f1dark/95 mt-auto"
      role="contentinfo"
    >
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-400">
          {/* Data source attribution */}
          <div className="flex items-center gap-2">
            <span>Data source:</span>
            <a 
              href="https://github.com/theOehrly/Fast-F1"
              target="_blank"
              rel="noopener noreferrer"
              className="text-f1red hover:underline"
            >
              FastF1
            </a>
            <span className="text-gray-600">(cached)</span>
          </div>
          
          {/* Copyright */}
          <div>
            <span>&copy; Mohamed Hani B Khashogji {currentYear}</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
