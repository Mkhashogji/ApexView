# Frontend Development Rules

## Technology Stack

- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **State**: React hooks, URL state for shareability
- **Charts**: Plotly.js and Recharts
- **Testing**: Vitest + React Testing Library

## Code Style

### TypeScript

```typescript
// ✅ Good: Explicit types, clear naming
interface DriverSelectionProps {
  selectedDrivers: string[]
  onDriverChange: (drivers: string[]) => void
  maxSelection?: number
}

export function DriverSelection({ 
  selectedDrivers, 
  onDriverChange,
  maxSelection = 6 
}: DriverSelectionProps) {
  // Implementation
}

// ❌ Bad: Any types, unclear names
function Comp({ data, onChange }: any) {
  // Implementation
}
```

### Component Structure

```typescript
'use client' // Only if client-side interactivity needed

import { useState } from 'react'
import type { ComponentProps } from './types'

// 1. Type definitions
interface MyComponentProps {
  // Props
}

// 2. Component
export function MyComponent({ prop1, prop2 }: MyComponentProps) {
  // 3. Hooks
  const [state, setState] = useState()
  
  // 4. Effects
  useEffect(() => {}, [])
  
  // 5. Event handlers
  const handleClick = () => {}
  
  // 6. Render
  return (
    <div>
      {/* JSX */}
    </div>
  )
}
```

### File Naming

- Components: `PascalCase.tsx` (e.g., `DriverMultiSelect.tsx`)
- Utilities: `camelCase.ts` (e.g., `formatters.ts`)
- Types: `types.ts` or inline with component
- Pages: `page.tsx` (Next.js convention)

## Next.js Patterns

### Server vs Client Components

```typescript
// Server component (default)
// - No useState, useEffect, or event handlers
// - Can directly fetch data
// - Better performance
export default async function Page() {
  const data = await fetchData()
  return <div>{data}</div>
}

// Client component
// - Use 'use client' directive
// - For interactivity, state, effects
'use client'
export function InteractiveChart() {
  const [zoom, setZoom] = useState(1)
  return <div onWheel={handleZoom}>...</div>
}
```

### Data Fetching

```typescript
// ✅ Good: Fetch in server component or API route
async function getData() {
  const res = await fetch('http://api:8000/sessions', {
    next: { revalidate: 3600 } // Cache for 1 hour
  })
  if (!res.ok) throw new Error('Failed to fetch')
  return res.json()
}

// ✅ Good: Use client-side fetch for user actions
'use client'
function Component() {
  const loadData = async () => {
    const data = await fetch('/api/sessions').then(r => r.json())
    setData(data)
  }
}
```

### Loading & Error States

```typescript
// loading.tsx - Shows while page loads
export default function Loading() {
  return <Skeleton />
}

// error.tsx - Shows on error
'use client'
export default function Error({ error, reset }: {
  error: Error
  reset: () => void
}) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={reset}>Try again</button>
    </div>
  )
}
```

## Styling with Tailwind

### Best Practices

```typescript
// ✅ Good: Utility classes, conditional styling
<div className={`
  rounded-lg border border-f1gray bg-f1gray/20 p-6
  ${isActive ? 'ring-2 ring-f1red' : ''}
  ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-f1gray/30'}
`}>
  Content
</div>

// ✅ Good: Extract repeated patterns
const cardClass = "rounded-lg border border-f1gray bg-f1gray/20 p-6"

// ❌ Bad: Inline styles (use Tailwind instead)
<div style={{ padding: '24px', backgroundColor: '#38383F' }}>
```

### Responsive Design

```typescript
<div className="
  grid gap-4
  grid-cols-1        /* mobile */
  md:grid-cols-2     /* tablet */
  lg:grid-cols-3     /* desktop */
">
  {items.map(item => <Card key={item.id} />)}
</div>
```

### Theme Colors

```typescript
// Use custom colors from tailwind.config.js
<div className="bg-f1dark text-white border-f1gray">
  <span className="text-f1red">Red Bull</span>
  <span className="text-ferrari">Ferrari</span>
</div>
```

## State Management

### Local State

```typescript
// ✅ Good: useState for component-local state
const [selectedDrivers, setSelectedDrivers] = useState<string[]>(['VER'])

// ✅ Good: useReducer for complex state
const [state, dispatch] = useReducer(reducer, initialState)
```

### URL State (Shareable)

```typescript
'use client'
import { useSearchParams, useRouter } from 'next/navigation'

function QualifyingPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  
  // Read from URL
  const drivers = searchParams.get('drivers')?.split(',') || []
  
  // Update URL
  const updateDrivers = (newDrivers: string[]) => {
    const params = new URLSearchParams(searchParams)
    params.set('drivers', newDrivers.join(','))
    router.push(`?${params.toString()}`)
  }
}
```

### Prop Drilling Avoidance

```typescript
// ✅ Good: Context for deeply nested props
const SessionContext = createContext<SessionData | null>(null)

export function SessionProvider({ children, session }: Props) {
  return (
    <SessionContext.Provider value={session}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  const context = useContext(SessionContext)
  if (!context) throw new Error('useSession must be used within SessionProvider')
  return context
}
```

## Performance Optimization

### Lazy Loading

```typescript
// ✅ Good: Lazy load heavy components
const TelemetryChart = dynamic(() => import('./TelemetryChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false // Don't render on server if not needed
})
```

### Memoization

```typescript
// ✅ Good: Memoize expensive calculations
const processedData = useMemo(() => {
  return expensiveCalculation(rawData)
}, [rawData])

// ✅ Good: Memoize callbacks to prevent re-renders
const handleDriverSelect = useCallback((driver: string) => {
  setSelectedDrivers(prev => [...prev, driver])
}, [])
```

### Virtual Scrolling

```typescript
// For large lists (> 100 items)
import { useVirtualizer } from '@tanstack/react-virtual'

function LargeList({ items }) {
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  })
  
  // Render only visible items
}
```

## Chart Configuration

### Plotly.js

```typescript
import Plot from 'react-plotly.js'

function TelemetryChart({ data }: Props) {
  return (
    <Plot
      data={[
        {
          x: data.map(p => p.distance),
          y: data.map(p => p.speed),
          type: 'scatter',
          mode: 'lines',
          line: { color: DRIVER_COLORS[driver] },
        }
      ]}
      layout={{
        title: 'Speed Trace',
        xaxis: { title: 'Distance (m)' },
        yaxis: { title: 'Speed (km/h)' },
        plot_bgcolor: '#15151E',
        paper_bgcolor: '#15151E',
        font: { color: '#fff' },
        hovermode: 'x unified',
      }}
      config={{
        responsive: true,
        displayModeBar: true,
      }}
    />
  )
}
```

## Error Handling

### Try-Catch for Async Operations

```typescript
async function fetchData() {
  try {
    const response = await fetch('/api/data')
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    return await response.json()
  } catch (error) {
    console.error('Failed to fetch data:', error)
    throw error // Re-throw for error boundary
  }
}
```

### Error Boundaries

```typescript
// Use Next.js error.tsx or custom boundary
class ErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught:', error, errorInfo)
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback />
    }
    return this.props.children
  }
}
```

## Accessibility

### Semantic HTML

```typescript
// ✅ Good: Semantic elements
<nav>
  <a href="/">Home</a>
</nav>

<main>
  <article>Content</article>
</main>

// ❌ Bad: Div soup
<div className="nav">
  <div className="link">Home</div>
</div>
```

### ARIA Labels

```typescript
<button
  aria-label="Select Max Verstappen"
  onClick={() => selectDriver('VER')}
>
  VER
</button>

<input
  type="text"
  aria-describedby="search-help"
/>
<span id="search-help">Search by driver name or number</span>
```

### Keyboard Navigation

```typescript
// Ensure all interactive elements are keyboard accessible
<button
  onClick={handleClick}
  onKeyDown={(e) => e.key === 'Enter' && handleClick()}
  tabIndex={0}
>
  Click me
</button>
```

## Testing

### Component Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { DriverSelect } from './DriverSelect'

describe('DriverSelect', () => {
  it('renders driver options', () => {
    render(<DriverSelect drivers={['VER', 'HAM']} />)
    expect(screen.getByText('VER')).toBeInTheDocument()
  })
  
  it('calls onChange when driver selected', () => {
    const handleChange = vi.fn()
    render(<DriverSelect onChange={handleChange} />)
    
    fireEvent.click(screen.getByText('VER'))
    expect(handleChange).toHaveBeenCalledWith(['VER'])
  })
})
```

### Test Coverage Goals

- Critical user paths: 80%+ coverage
- Utility functions: 90%+ coverage
- UI components: Test behavior, not implementation

## Common Patterns

### API Calls

```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL

export async function fetchSessions(season: number, round: number) {
  const res = await fetch(`${API_BASE}/sessions?season=${season}&round=${round}`)
  if (!res.ok) throw new Error('Failed to fetch sessions')
  return res.json()
}
```

### Custom Hooks

```typescript
// hooks/useSession.ts
export function useSession(sessionId: string) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  useEffect(() => {
    fetchSession(sessionId)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [sessionId])
  
  return { data, loading, error }
}
```

## Don'ts

❌ Don't use `any` type
❌ Don't mutate state directly
❌ Don't forget key props in lists
❌ Don't put business logic in components
❌ Don't skip error handling
❌ Don't use inline functions in JSX (extract to useCallback)
❌ Don't fetch data in useEffect when you can use server components
❌ Don't forget to clean up effects (return cleanup function)

## Do's

✅ Use TypeScript strict mode
✅ Use server components by default
✅ Extract reusable logic to hooks
✅ Keep components focused and small
✅ Use semantic HTML
✅ Make URLs shareable (encode state)
✅ Optimize images with next/image
✅ Use proper loading and error states
✅ Test critical user flows
✅ Document complex logic

