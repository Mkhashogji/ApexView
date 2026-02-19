'use client'

import { useRef, useState, useEffect, type RefObject } from 'react'

interface UseVisibilityOptions {
  /**
   * Root margin for IntersectionObserver.
   * Default '200px' starts loading when panel is 200px below viewport,
   * giving the API call time to complete before the user scrolls to it.
   */
  rootMargin?: string
}

interface UseVisibilityResult {
  /** Attach to the panel's outermost container div */
  containerRef: RefObject<HTMLDivElement>
  /** True once the element has entered (or approached) the viewport */
  isVisible: boolean
}

/**
 * Tracks whether a container element has entered the viewport.
 *
 * Once visible, stays visible permanently — the observer disconnects.
 * Scrolling the panel back out of view does NOT reset visibility.
 * This prevents data loss and unnecessary refetches.
 *
 * Usage:
 *   const { containerRef, isVisible } = useVisibility()
 *   const { data } = useMyQuery(sessionId, isVisible) // pass as enabled
 *
 *   return <div ref={containerRef}>{...}</div>
 */
export function useVisibility(
  options: UseVisibilityOptions = {}
): UseVisibilityResult {
  const { rootMargin = '200px' } = options
  const containerRef = useRef<HTMLDivElement>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    if (isVisible) return // Already visible, no need to observe

    const element = containerRef.current
    if (!element) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          observer.disconnect()
        }
      },
      { rootMargin }
    )

    observer.observe(element)

    return () => observer.disconnect()
  }, [rootMargin, isVisible])

  return { containerRef, isVisible }
}
