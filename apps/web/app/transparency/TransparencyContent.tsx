/**
 * Transparency & Attribution page content.
 *
 * Server Component — purely static HTML with anchor links.
 * No client-side interactivity, no hooks, no state.
 */

const TOC_LINKS = [
  { id: 'disclaimer', label: 'Project Disclaimer' },
  { id: 'data-sources', label: 'Data Sources' },
  { id: 'methodology', label: 'Analysis Methodology' },
  { id: 'privacy', label: 'Privacy' },
  { id: 'attribution', label: 'Attribution' },
  { id: 'intellectual-property', label: 'Intellectual Property' },
] as const

export default function TransparencyContent() {
  return (
    <div className="space-y-6">
      {/* Table of contents */}
      <nav aria-label="Page sections">
        <ul className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
          {TOC_LINKS.map((link) => (
            <li key={link.id}>
              <a
                href={`#${link.id}`}
                className="text-gray-400 transition-colors hover:text-white"
              >
                {link.label}
              </a>
            </li>
          ))}
        </ul>
      </nav>

      {/* Section 1: Project Disclaimer */}
      <section id="disclaimer" className="card-panel scroll-mt-20">
        <h2 className="card-panel-header">Project Disclaimer</h2>
        <div className="space-y-3 text-sm leading-relaxed text-gray-300">
          <p>
            ApexView is an independent academic project created as a computer science
            and data engineering portfolio piece. It is not affiliated with, endorsed by,
            or connected to Formula 1, the Fédération Internationale de
            l&apos;Automobile (FIA), Formula One Management (FOM), or any Formula 1
            team or constructor.
          </p>
          <p>
            This platform has no commercial intent. It is not monetised, does not sell
            data, and does not offer paid services. The project exists solely as a
            technical demonstration of data engineering, full-stack development, and
            analytical system design.
          </p>
          <p>
            All analysis presented on this platform represents the author&apos;s
            independent computational interpretation of publicly available data. The
            results are not official, not verified by any governing body, and should not
            be treated as authoritative race analysis.
          </p>
        </div>
      </section>

      {/* Section 2: Data Sources & Limitations */}
      <section id="data-sources" className="card-panel scroll-mt-20">
        <h2 className="card-panel-header">Data Sources & Limitations</h2>
        <div className="space-y-4 text-sm leading-relaxed text-gray-300">
          <p>
            All telemetry and timing data is sourced from the{' '}
            <a
              href="https://github.com/theOehrly/Fast-F1"
              target="_blank"
              rel="noopener noreferrer"
              className="text-f1red hover:underline"
            >
              FastF1
            </a>{' '}
            Python library, which accesses publicly broadcast Formula 1 session data.
            No private team telemetry, proprietary data feeds, or confidential
            information is used at any point in the data pipeline.
          </p>

          <div>
            <h3 className="mb-2 font-heading text-base font-medium text-white">
              What the data includes
            </h3>
            <ul className="list-disc list-inside space-y-1 text-gray-300">
              <li>Publicly broadcast telemetry — speed, throttle position, brake application, gear, and DRS status</li>
              <li>Official FIA timing — lap times, sector times, and speed trap readings</li>
              <li>Session metadata — tyre compounds, pit stop durations, lap classifications, and driver status</li>
            </ul>
          </div>

          <div>
            <h3 className="mb-2 font-heading text-base font-medium text-white">
              What the data does not include
            </h3>
            <ul className="list-disc list-inside space-y-1 text-gray-300">
              <li>Internal team telemetry or high-resolution sensor data</li>
              <li>Aerodynamic load measurements, ride height, or damper positions</li>
              <li>Tyre pressure, surface temperature, or core temperature readings</li>
              <li>Engine modes, power unit settings, or energy deployment maps</li>
              <li>Car setup parameters (wing angles, suspension geometry, differential settings)</li>
              <li>Team radio communications or strategic context</li>
            </ul>
          </div>

          <p className="text-gray-400">
            Public broadcast data has lower sampling rates and fewer channels than
            what Formula 1 teams access through their internal systems. Teams work with
            hundreds of additional sensor channels at higher frequency. Conclusions
            drawn from public data should be understood within that context.
          </p>
        </div>
      </section>

      {/* Section 3: Analysis Methodology */}
      <section id="methodology" className="card-panel scroll-mt-20">
        <h2 className="card-panel-header">Analysis Methodology</h2>
        <div className="space-y-4 text-sm leading-relaxed text-gray-300">
          <p>
            The platform applies statistical and computational techniques to public
            data. These produce informative approximations rather than exact
            engineering measurements. Where uncertainty exists, the platform
            communicates it through confidence indicators, or omits the result entirely
            following the principle of displaying accurate data or no data — never
            misleading data.
          </p>

          {/* Delta Analysis */}
          <div className="border-l-2 border-f1gray pl-4">
            <h3 className="mb-1 font-heading text-sm font-medium text-white">
              Delta Analysis
            </h3>
            <p>
              Telemetry from two drivers is aligned using relative distance
              normalisation (mapping each driver&apos;s lap to a 0–1 scale), then
              scaled so the integrated time difference matches the official FIA lap
              time gap. The shape of the delta curve comes from telemetry speed data;
              the overall magnitude is anchored to official timing.
            </p>
          </div>

          {/* Corner Analysis */}
          <div className="border-l-2 border-f1gray pl-4">
            <h3 className="mb-1 font-heading text-sm font-medium text-white">
              Corner Analysis
            </h3>
            <p>
              Brake points are identified using a two-stage detection algorithm. The
              first stage finds where the brake signal clearly activates (above 50%).
              The second stage refines backward using deceleration calculated from
              speed changes (v² kinematics), locating where heavy deceleration first
              begins. Circuit-specific deceleration thresholds (ranging from −4.0 to
              −6.5 m/s²) account for different braking characteristics across tracks.
            </p>
            <p className="mt-1.5">
              Confidence labels reflect how closely the two detection methods agreed:
              High means they aligned within 20 metres, Medium within 40 metres, and
              Low means they diverged beyond 40 metres, indicating approximate zone
              boundaries.
            </p>
          </div>

          {/* Technique Profiles */}
          <div className="border-l-2 border-f1gray pl-4">
            <h3 className="mb-1 font-heading text-sm font-medium text-white">
              Technique Profiles
            </h3>
            <p>
              Driver performance is ranked across five dimensions (braking, apex,
              exit, consistency, straight-line) using session-relative percentiles. A
              driver at P15 in braking was in the top 15% of that specific session —
              this is not an absolute measurement. Percentiles are only meaningful
              within the context of a single session and are not comparable across
              different sessions or circuits.
            </p>
          </div>

          {/* Fuel Correction */}
          <div className="border-l-2 border-f1gray pl-4">
            <h3 className="mb-1 font-heading text-sm font-medium text-white">
              Fuel Correction
            </h3>
            <p>
              Race and practice lap times can be adjusted for estimated fuel load
              using circuit-specific depletion rates ranging from 0.028 to 0.036
              seconds per kilogram. These are estimates based on circuit
              characteristics, not measured fuel loads from team data. The correction
              can be toggled on or off by the user.
            </p>
          </div>

          {/* Outlier Detection */}
          <div className="border-l-2 border-f1gray pl-4">
            <h3 className="mb-1 font-heading text-sm font-medium text-white">
              Outlier Detection
            </h3>
            <p>
              Statistical outlier filtering uses interquartile range (IQR) fences
              combined with a secondary threshold of 1.10× the driver&apos;s median
              lap time, applied per driver per tyre compound. This removes anomalous
              laps (incidents, traffic, errors) but may occasionally exclude
              legitimate performance variation at the margins.
            </p>
          </div>

          {/* Degradation Estimates */}
          <div className="border-l-2 border-f1gray pl-4">
            <h3 className="mb-1 font-heading text-sm font-medium text-white">
              Degradation Estimates
            </h3>
            <p>
              Tyre degradation hints in practice sessions compare the average of a
              stint&apos;s last two laps against its first two laps — a simple
              arithmetic indicator requiring at least four valid laps. This does not
              account for fuel burn, traffic conditions, or track evolution within the
              stint.
            </p>
          </div>
        </div>
      </section>

      {/* Section 4: Privacy */}
      <section id="privacy" className="card-panel scroll-mt-20">
        <h2 className="card-panel-header">Privacy</h2>
        <div className="space-y-3 text-sm leading-relaxed text-gray-300">
          <p>
            ApexView does not collect, store, or process any personal data. There are
            no user accounts, no login system, and no registration process.
          </p>
          <p>
            The application does not use cookies, tracking pixels, analytics services,
            or any form of user behaviour monitoring. No third-party analytics or
            advertising tools are integrated.
          </p>
          <p>
            Pages are server-rendered and served as static content. The application
            makes API calls only to its own backend to retrieve Formula 1 session
            data. No user data is sent to external services.
          </p>
        </div>
      </section>

      {/* Section 5: Attribution */}
      <section id="attribution" className="card-panel scroll-mt-20">
        <h2 className="card-panel-header">Attribution & Acknowledgements</h2>
        <div className="space-y-3 text-sm leading-relaxed text-gray-300">
          <p>
            <a
              href="https://github.com/theOehrly/Fast-F1"
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-f1red hover:underline"
            >
              FastF1
            </a>{' '}
            — MIT-licensed Python library by theOehrly. This library provides the
            data access layer for all telemetry and timing information on the platform.
          </p>
          <p>
            The underlying data originates from FIA and Formula One Management public
            broadcasts. FastF1 provides structured access to this publicly available
            information.
          </p>
          <p>
            This project is built with open-source technologies including{' '}
            <span className="text-gray-200">Next.js</span>,{' '}
            <span className="text-gray-200">FastAPI</span>,{' '}
            <span className="text-gray-200">Plotly.js</span>,{' '}
            <span className="text-gray-200">NumPy</span>, and{' '}
            <span className="text-gray-200">SciPy</span>. The author acknowledges the
            broader open-source ecosystem that makes projects like this possible.
          </p>
        </div>
      </section>

      {/* Section 6: Intellectual Property */}
      <section id="intellectual-property" className="card-panel scroll-mt-20">
        <h2 className="card-panel-header">Intellectual Property</h2>
        <div className="space-y-3 text-sm leading-relaxed text-gray-300">
          <p>
            Formula 1, F1, the F1 logo, and related marks are trademarks of Formula
            One Licensing BV. The FIA name and logo are trademarks of the Fédération
            Internationale de l&apos;Automobile. Circuit names, driver names, and team
            names are the property of their respective owners.
          </p>
          <p>
            These names and marks are used on this platform solely for identification
            and analytical purposes within an academic and educational context. No
            ownership of these marks is claimed or implied.
          </p>
        </div>
      </section>
    </div>
  )
}
