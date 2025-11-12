'use client'

import { QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import { queryClient } from '@/lib/queryClient'

/**
 * Providers component wraps the app with necessary context providers.
 * Must be a client component to use React Query.
 */
export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

