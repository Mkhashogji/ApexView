'use client'

import { Component, type ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  panelName?: string
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

/**
 * Per-panel Error Boundary for graceful degradation.
 *
 * Catches runtime JavaScript errors (e.g., Plotly rendering failure,
 * unexpected data shape) and renders a fallback UI instead of crashing
 * the entire React tree.
 *
 * Usage in RaceContent.tsx:
 *   <ErrorBoundary key={`pit-${sessionId}`} panelName="Pit Stop Analysis">
 *     <PitStopPanel ... />
 *   </ErrorBoundary>
 *
 * The key={sessionId} pattern forces React to remount the boundary
 * when the Grand Prix changes, clearing any previous error state.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error(
      `[ErrorBoundary] ${this.props.panelName || 'Panel'} crashed:`,
      error,
      errorInfo.componentStack
    )
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <section className="card-panel">
          <h2 className="card-panel-header">
            {this.props.panelName ?? 'Panel'}
          </h2>
          <div className="h-[200px] flex items-center justify-center">
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 text-amber-400 mb-2">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
                <span className="text-sm font-medium">
                  Something went wrong rendering this panel
                </span>
              </div>
              <p className="text-xs text-gray-500">
                Other panels are unaffected. Try switching to a different Grand
                Prix.
              </p>
            </div>
          </div>
        </section>
      )
    }

    return this.props.children
  }
}
