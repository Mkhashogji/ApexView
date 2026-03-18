# Home Page Phase 1: Structural Foundation

**Status:** Complete
**Implemented:** March 2026
**TypeScript:** Zero compilation errors
**Docker Build:** Clean exit (all 3 services healthy)
**Verification:** 15-point Docker-first validation, all checks passing

---

## Table of Contents

1. [Purpose and Significance](#1-purpose-and-significance)
2. [Theoretical and Logical Background](#2-theoretical-and-logical-background)
3. [End-to-End Workflow and Data Flow](#3-end-to-end-workflow-and-data-flow)
4. [Technical Implementation Breakdown](#4-technical-implementation-breakdown)
5. [Pre-Implementation Diagnostic](#5-pre-implementation-diagnostic)
6. [Learnings and How They Influenced Decisions](#6-learnings-and-how-they-influenced-decisions)
7. [Testing, Verification and Validation](#7-testing-verification-and-validation)
8. [Alignment with Broader Home Page Plan](#8-alignment-with-broader-home-page-plan)

---

## 1. Purpose and Significance

### What Phase 1 Does

Phase 1 establishes the **structural foundation** for the Home page. Unlike every other page's Phase 1 (which built backend data pipelines), the Home page Phase 1 is entirely infrastructure-focused. It accomplishes four objectives:

1. **Placeholder removal** — Deletes the hardcoded `SessionSummary` component with fake F1 data and replaces the Home page with a clean Server Component + Suspense shell.
2. **Brand identity** — Integrates the ApexView SVG favicon via Next.js App Router auto-detection.
3. **Route normalisation** — Migrates Track Intelligence from a dynamic route segment (`/track/[round]`) to query parameters (`/track?round=`), aligning it with the application's URL state convention.
4. **Navigation completeness** — Adds Track Intelligence as the 5th nav link, making all completed features discoverable from any page.

### Why It Matters

Before Phase 1, the ApexView application had a structural inconsistency: four fully implemented analytical pages (Qualifying, Race, Practice, Track Intelligence) existed, but the Home page displayed hardcoded fake data that misrepresented the platform's capabilities. Track Intelligence, despite being fully implemented with data for all 24 circuits, was entirely undiscoverable — no navigation link pointed to it, and its dynamic route pattern (`/track/[round]`) diverged from the query parameter convention (`?round=&season=`) used by every other page.

Phase 1 resolves these inconsistencies before any content is built. This separation is deliberate: building content on top of a structurally inconsistent foundation would compound the problems. By fixing the routing, navigation, metadata, and component architecture first, Phases 2 and 3 can focus exclusively on designing and implementing the Home page content within a stable, well-defined shell.

### Position in the Home Page Architecture

| Phase | Name | Status | Depends On |
|-------|------|--------|-----------|
| **1** | **Structural Foundation** | Complete | — |
| 2 | Content and Identity | Complete | Phase 1 |
| 3 | Polish and Performance | Complete | Phase 2 |

Phase 1 produces no API calls, no data visualisations, and no analytical content. Its deliverable is the architectural shell — the Server Component, Suspense boundary, skeleton, metadata, favicon, normalised routing, and complete navigation — that Phases 2 and 3 populate with content.

### How This Differs from Other Phase 1s

| Page | Phase 1 Focus | Backend Work | Frontend Work |
|------|--------------|-------------|---------------|
| Race | Data pipeline (lap classification, fuel correction, traffic, stints) | 130 tests, 5 services | None |
| Practice | Data pipeline + Long Run Pace panel | 104 tests, 3 services | Violin plot, session tabs |
| **Home** | **Structural shell, routing, navigation** | **None** | **Page shell, skeleton, favicon, route migration** |

The Home page has no backend pipeline because it serves as a navigation hub and platform overview — it does not process telemetry data. This makes Phase 1 fundamentally different: the complexity lies in cross-cutting architectural concerns (route normalisation, backward-compatible redirects, navigation state, Next.js conventions) rather than data processing logic.

---

## 2. Theoretical and Logical Background

### 2.1 Server Component + Suspense Architecture

Every analytical page in ApexView follows the same rendering pattern, established during the Qualifying page performance optimisation (Lighthouse 42 to 90+):

```
page.tsx (Server Component)          — SSR: renders instantly, provides metadata
  └── <Suspense fallback={Skeleton}>  — Streaming boundary
        └── Content.tsx (Client)      — Hydrates after JS loads
```

**Why Server Components for the page shell:** The `page.tsx` file is a React Server Component that runs exclusively on the server. It exports `metadata` (title, description, OpenGraph) that Next.js injects into `<head>` during SSR. This ensures search engines and social media crawlers receive complete metadata without waiting for client-side JavaScript. The component renders to HTML on the first request, producing the Largest Contentful Paint (LCP) element immediately.

**Why Suspense for content:** The `<Suspense>` boundary separates the SSR shell from the client-side interactive content. The fallback (skeleton) paints instantly as part of the server-rendered HTML. When the client-side JavaScript bundle loads and hydrates, React replaces the skeleton with the actual content. This progressive rendering pattern ensures:
- First Contentful Paint (FCP) is fast (skeleton renders from SSR HTML).
- Total Blocking Time (TBT) is zero (no JS blocks the main thread during initial paint).
- The page remains interactive during content loading.

**Why the Home page omits `border-l-4 border-f1red` header:** The analytical pages (Qualifying, Race, Practice) use a red-bordered header as the LCP element:

```tsx
<header className="border-l-4 border-f1red pl-4">
  <h1>Qualifying Analysis</h1>
</header>
```

The Home page intentionally omits this pattern. Phase 2 introduces a hero section that serves as the primary heading — adding a separate header above it would create visual redundancy. The `space-y-12 py-8` container provides additional vertical breathing room appropriate for a landing page, compared to the `space-y-6` used by analytical pages.

### 2.2 URL State Convention and Route Normalisation

ApexView stores session context (season, round, session type) in URL search parameters. This convention was established by the `RaceWeekendSelector` component, which constructs URLs using the current pathname plus updated query parameters:

```tsx
// RaceWeekendSelector.tsx — handleSelect()
router.push(`${pathname}?${params.toString()}`)
```

This pattern preserves the current page's pathname and updates `?round=` and `?season=` parameters. It works correctly for `/qualifying?round=1`, `/race?round=1`, `/practice?round=1`, and now `/track?round=1`.

The Track Intelligence page originally used a dynamic route segment: `/track/[round]`. This created a conflict:

| Aspect | Dynamic Route (`/track/[round]`) | Query Param (`/track?round=`) |
|--------|----------------------------------|------------------------------|
| RaceWeekendSelector compatibility | Incompatible — selector updates `?round=` but pathname stays `/track/[round]` | Compatible — selector updates `?round=` on `/track` pathname |
| URL state consistency | Diverges from all other pages | Matches all other pages |
| Next.js routing | Requires `params.round` (path parameter) | Uses `searchParams.round` (query parameter) |
| Bookmarkability | `/track/24` — readable but inconsistent | `/track?round=24` — consistent with app convention |

Normalising to query parameters makes the Track Intelligence page a first-class citizen of the application's URL state model. The `RaceWeekendSelector` now drives Track Intelligence context automatically — a user can select Round 1 on the Race page and navigate to Track Intelligence to see the same circuit's data.

### 2.3 Backward-Compatible Redirects

Any existing bookmarks or external links to `/track/24` must continue to work after the route migration. Next.js provides a `redirects()` configuration in `next.config.js` that runs at the server level before page rendering:

```js
async redirects() {
  return [
    {
      source: '/track/:round',
      destination: '/track?round=:round',
      permanent: true,    // HTTP 308 Permanent Redirect
    },
  ]
}
```

**Why 308 (not 301):** HTTP 308 is the method-preserving permanent redirect. While 301 technically allows user agents to change the request method (POST to GET), 308 guarantees method preservation. For navigation URLs this distinction is academic, but 308 is the modern standard that Next.js uses for `permanent: true`.

**Why server-side redirect (not client-side):** A server-side redirect returns a 308 response before any page rendering occurs. The browser follows the redirect transparently. A client-side redirect (e.g., `useRouter().replace()`) would first render the page, then redirect — causing a flash of content and doubling the navigation time.

### 2.4 Next.js App Router Favicon Convention

Next.js 14 App Router automatically detects icon files placed in the `app/` directory:

| File | Generated Tag |
|------|--------------|
| `app/icon.svg` | `<link rel="icon" type="image/svg+xml" href="/icon.svg?hash">` |
| `app/icon.png` | `<link rel="icon" type="image/png" href="/icon.png?hash">` |
| `app/apple-icon.png` | `<link rel="apple-touch-icon" href="/apple-icon.png?hash">` |

No manual `<link>` tags are needed in `layout.tsx`. Next.js appends a content hash query parameter (`?c45e97863bd58fa0`) for cache-busting. Phase 1 uses only `icon.svg` — the Apple touch icon is deferred as it requires PNG rasterisation from the SVG source.

### 2.5 Navigation Active State Detection

The `Navigation` component uses pathname-based active state detection:

```tsx
const isActive = (href: string) => {
  if (href === '/') return pathname === '/'
  return pathname.startsWith(href)
}
```

**Root path special case:** The Home link (`/`) uses exact equality (`===`) because `startsWith('/')` would match every page. All other links use prefix matching — `/track` correctly matches `/track` regardless of query parameters (`?round=1&season=2025`), because `pathname` in Next.js excludes the query string.

This detection algorithm required no modifications for the Track Intelligence link. Adding `{ href: '/track', label: 'Track Intelligence' }` to the `navLinks` array was sufficient because:
- `pathname.startsWith('/track')` matches `/track` (the new route).
- Query parameters (`?round=1`) are not part of `pathname`.
- The old dynamic route (`/track/24`) is redirected before the Navigation component renders.

---

## 3. End-to-End Workflow and Data Flow

### 3.1 Phase 1 Data Flow (No API Calls)

The Home page in Phase 1 makes zero API calls. The entire rendering flow is static:

```
Browser Request
  GET /
       |
       v
  Next.js Server
       |
       ├── layout.tsx (Server Component)
       |     Renders: <html> + <body> + font variables
       |     ├── <Navigation />        — 5 nav links, RaceWeekendSelector
       |     ├── <main>
       |     |     └── page.tsx        — Server Component, exports metadata
       |     |           └── <Suspense fallback={HomePageSkeleton}>
       |     |                 └── <HomeContent />  — Client Component placeholder
       |     └── <Footer />
       |
       v
  HTML Response (SSR)
       |  Contains: metadata in <head>, favicon link, nav bar HTML,
       |  skeleton HTML (visible until JS hydrates), footer HTML
       |
       v
  Browser Hydration
       |  React hydrates <HomeContent />, replaces skeleton
       |  with "Home page content — Phase 2" placeholder
       |
       v
  Rendered Page
         No API calls, no data fetching, fully static
```

### 3.2 Track Intelligence Route Flow (Before and After)

**Before Phase 1:**
```
User clicks bookmark: /track/24
       |
       v
  Next.js matches /track/[round]/page.tsx
       |  params.round = "24"
       |
       v
  TrackIntelligenceContent receives round=24
       |
       v
  useTrackIntelligence(24, 2025) fetches data

  ---- BUT ----
  RaceWeekendSelector updates ?round= on pathname /track/24
  → URL becomes /track/24?round=1 (conflicting state)
  → Track Intelligence ignores the query param, stays on round 24
```

**After Phase 1:**
```
User clicks bookmark: /track/24
       |
       v
  next.config.js redirect (308)
       |  Location: /track?round=24
       |
       v
  Browser follows redirect to /track?round=24
       |
       v
  Next.js matches /track/page.tsx
       |  searchParams.round = "24"
       |
       v
  TrackIntelligenceContent receives round=24, season=2025

  ---- AND ----
  RaceWeekendSelector updates ?round= on pathname /track
  → URL becomes /track?round=1&season=2025 (consistent state)
  → Track Intelligence reads round=1 from searchParams
  → Page shows Round 1 data (correct behavior)
```

### 3.3 Navigation Link Flow

```
User on /race?round=1&season=2025
       |
       |  Clicks "Track Intelligence" in nav bar
       |
       v
  <Link href="/track">
       |  Next.js client-side navigation to /track
       |  (no query params — fresh navigation)
       |
       v
  /track/page.tsx
       |  searchParams = {} (empty)
       |  round = parseInt(undefined || '24', 10) = 24
       |  season = parseInt(undefined || '2025', 10) = 2025
       |
       v
  Renders Track Intelligence for Round 24 (Abu Dhabi, default)
       |
       |  User uses RaceWeekendSelector to switch to Round 1
       |
       v
  RaceWeekendSelector: router.push('/track?round=1&season=2025')
       |
       v
  /track/page.tsx re-renders with searchParams.round = "1"
       |  Displays Round 1 (Australian GP)
```

---

## 4. Technical Implementation Breakdown

### 4.1 Files Modified — Complete Inventory

| Action | File | Purpose |
|--------|------|---------|
| Copy | `Downloads/ApexViewIcon (1).svg` to `apps/web/app/icon.svg` | Favicon via App Router auto-detection |
| Delete | `apps/web/components/panels/SessionSummary.tsx` | Remove hardcoded fake data component |
| Rewrite | `apps/web/app/page.tsx` | Server Component shell with metadata + Suspense |
| Create | `apps/web/app/HomeContent.tsx` | Client Component placeholder for Phase 2 |
| Create | `apps/web/app/HomePageSkeleton.tsx` | Skeleton matching planned 3-section layout |
| Create | `apps/web/app/track/page.tsx` | New query-param-based Track page |
| Move | `apps/web/app/track/[round]/TrackIntelligenceContent.tsx` to `apps/web/app/track/` | Relocate to new route directory |
| Delete | `apps/web/app/track/[round]/` (entire directory) | Remove old dynamic route |
| Edit | `apps/web/next.config.js` | Add `redirects()` for backward compatibility |
| Edit | `apps/web/components/layout/Navigation.tsx` | Add 5th nav link (Track Intelligence) |

### 4.2 SessionSummary Removal

`SessionSummary.tsx` was a panel component in `components/panels/` that rendered hardcoded fake F1 data — fabricated driver abbreviations, lap times (1:32.837), speeds (342 km/h), and a "Weekend Overview" title. It was imported only in `apps/web/app/page.tsx`.

The `panels/` directory contains 14 other components (PerformanceInsightsPanel, CornerBreakdownPanel, AnalysisInsights, etc.) used by the Qualifying page. Only `SessionSummary.tsx` was deleted — all other panel components were preserved.

**Why delete rather than refactor:** The component had no reusable logic. Every data point was hardcoded. Refactoring it to accept props would produce a component with no callers (the Home page does not display session summary data) and no architectural alignment with the planned feature card design.

### 4.3 Home Page Server Component (`page.tsx`)

```tsx
import type { Metadata } from 'next'
import { Suspense } from 'react'
import HomePageSkeleton from './HomePageSkeleton'
import HomeContent from './HomeContent'

export const metadata: Metadata = {
  title: 'ApexView | Formula 1 Data Analytics',
  description:
    'Explore Formula 1 race strategy, qualifying pace, practice performance, ' +
    'and circuit intelligence across the full 2025 season.',
  openGraph: {
    title: 'ApexView | Formula 1 Data Analytics',
    description:
      'Race strategy, qualifying analysis, practice performance, and circuit ' +
      'intelligence for every round of the 2025 Formula 1 season.',
    type: 'website',
  },
}

export default function HomePage() {
  return (
    <div className="space-y-12 py-8">
      <Suspense fallback={<HomePageSkeleton />}>
        <HomeContent />
      </Suspense>
    </div>
  )
}
```

**Metadata design:** The title uses "ApexView" (brand name) rather than "F1 Engineering App" (the root layout default). Page-level metadata in Next.js overrides root layout metadata for that route. The description covers all four analytical domains (race strategy, qualifying, practice, circuit intelligence) to provide comprehensive search context. OpenGraph metadata enables rich previews when the URL is shared on social platforms.

**Container spacing:** `space-y-12 py-8` provides more vertical breathing room than the analytical pages' `space-y-6`. This is intentional — the Home page's hero section and feature cards benefit from generous whitespace, while analytical pages pack dense data more tightly. The root layout already applies `py-8` on `<main>`, so the Home page's additional `py-8` doubles the top/bottom padding for a total of approximately 64px — appropriate for a landing page.

### 4.4 HomeContent Placeholder (`HomeContent.tsx`)

```tsx
'use client'

export default function HomeContent() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <p className="text-gray-500 font-mono text-sm">
        Home page content — Phase 2
      </p>
    </div>
  )
}
```

**Why `'use client'`:** Phase 2 will add interactive elements (feature cards with hover states, navigation links with client-side routing). Marking the component as a Client Component now avoids a breaking architectural change later. The `'use client'` directive has no performance impact for a static component — it simply tells Next.js to include this component in the client bundle for hydration.

**Why `min-h-[60vh]`:** Without minimum height, the placeholder text would sit at the top of an otherwise empty page, making the footer jump to mid-screen. The 60vh minimum ensures the page maintains visual presence during the placeholder period.

### 4.5 HomePageSkeleton (`HomePageSkeleton.tsx`)

The skeleton mirrors the three-section layout planned for the completed Home page:

1. **Hero section:** Large title bar (h-16, w-2/3), subtitle bar (h-8, w-1/2), three stat counters (h-12, w-32 each).
2. **Feature cards:** 2x2 grid of `card-panel` containers, each with title, two body lines, and a link placeholder.
3. **Platform capabilities:** Section title with a 2-column grid of 6 capability items.

**Design system alignment:** The skeleton uses `bg-f1gray/30` for primary elements and `bg-f1gray/20` for secondary elements — the same two-tone opacity pattern used by QualifyingPageSkeleton, PracticePageSkeleton, and TrackIntelligenceFallback. The `card-panel` CSS class (defined in `globals.css`) provides the dark card background, border, and rounded corners consistent with all existing panels. The `animate-pulse` class provides the breathing animation.

**Why build the skeleton before the content:** The skeleton is rendered by the server as part of the initial HTML response. It is visible for the brief period between SSR delivery and client-side hydration. Building it now (even before the content exists) ensures that Phase 2 development has a visual loading state from day one, and the skeleton's dimensions guide the content layout design.

### 4.6 Track Intelligence Route Migration

This was the most complex step in Phase 1, involving four coordinated changes.

#### 4.6a — New `track/page.tsx`

The new page uses Next.js 14's synchronous `searchParams` API (plain object, not a Promise):

```tsx
type Props = {
  searchParams: { round?: string; season?: string }
}

export default function TrackPage({ searchParams }: Props) {
  const round = parseInt(searchParams.round || '24', 10)
  const season = parseInt(searchParams.season || '2025', 10)
  // ...
}
```

**Critical API version note:** The project runs Next.js 14.1.0. In Next.js 15, `searchParams` becomes a Promise requiring `await`. This distinction was identified during the pre-implementation diagnostic (see Section 5) and confirmed with the user before implementation. Using the wrong API would cause a runtime error on every page load.

**Defaults:** Round defaults to 24 (Abu Dhabi, the final round of the 2025 season) and season to 2025. These defaults match the `DEFAULT_ROUND` and `DEFAULT_SEASON` constants used by the Race page's `RaceContent.tsx`, ensuring consistent behavior when no parameters are provided.

**Validation:** Invalid round numbers (NaN, < 1, > 24) render an error message rather than crashing or passing invalid data to the Track Intelligence component.

**Season parameter:** The old route did not accept a `season` parameter. The new route does, enabling the `RaceWeekendSelector` to drive both `round` and `season` context — future-proofing the page for multi-season support.

#### 4.6b — Component Relocation

`TrackIntelligenceContent.tsx` was moved from `app/track/[round]/` to `app/track/`. No code changes were needed because:
- All imports use the `@/` path alias, which resolves from the `apps/web` root directory.
- The component receives `round` and `season` as props (not from `params`), so the route structure is irrelevant to its implementation.
- It uses a named export (`export function TrackIntelligenceContent`) — the import statement in the new `page.tsx` uses `{ TrackIntelligenceContent }`.

#### 4.6c — Old Route Cleanup

The entire `apps/web/app/track/[round]/` directory was deleted after confirming both files (page.tsx, TrackIntelligenceContent.tsx) had been replaced or moved. This prevents Next.js from registering a competing dynamic route alongside the new static route.

#### 4.6d — Redirect Configuration

The redirect was added to `next.config.js` as a new `async redirects()` method on the config object:

```js
async redirects() {
  return [
    {
      source: '/track/:round',
      destination: '/track?round=:round',
      permanent: true,
    },
  ]
},
```

The `:round` parameter in the source captures the path segment and interpolates it into the destination's query parameter. For example, `/track/1` redirects to `/track?round=1`, and `/track/24` redirects to `/track?round=24`.

All existing configuration was preserved: `output: 'standalone'`, `reactStrictMode`, `transpilePackages`, the Plotly webpack chunk splitting, and the bundle analyzer wrapper.

### 4.7 Navigation Update

The `navLinks` array in `Navigation.tsx` was extended from 4 entries to 5:

```tsx
const navLinks = [
  { href: '/', label: 'Home' },
  { href: '/qualifying', label: 'Qualifying' },
  { href: '/race', label: 'Race' },
  { href: '/practice', label: 'Practice' },
  { href: '/track', label: 'Track Intelligence' },
]
```

No other changes were needed in the Navigation component. The existing `isActive` function, `aria-current="page"` accessibility attribute, red underline indicator (`bg-f1red shadow-glow-red-sm`), and `RaceWeekendSelector` integration all work correctly with the new link because:
- `pathname.startsWith('/track')` matches `/track` with any query parameters.
- The active indicator renders for the matching link.
- The `onMouseEnter` prefetch handler is only attached to the `/race` link and does not affect `/track`.

### 4.8 Favicon Integration

The SVG favicon was copied from the user's Downloads directory to the App Router convention path:

```
Source:      C:\Users\khash\Downloads\ApexViewIcon (1).svg  (3,658 bytes)
Destination: apps/web/app/icon.svg
```

Next.js auto-detects the file and generates the appropriate `<link>` tag in `<head>`:

```html
<link rel="icon" href="/icon.svg?c45e97863bd58fa0" type="image/svg+xml" sizes="any"/>
```

The content hash query parameter (`c45e97863bd58fa0`) ensures browsers fetch the new icon rather than serving a cached previous favicon.

### 4.9 Existing Patterns Reused

| Pattern | Source | Reused In |
|---------|--------|-----------|
| Server Component + Suspense page structure | `app/practice/page.tsx`, `app/qualifying/page.tsx` | `app/page.tsx`, `app/track/page.tsx` |
| `card-panel` CSS class | `app/globals.css` | `HomePageSkeleton.tsx` |
| `animate-pulse` skeleton pattern | `app/practice/PracticePageSkeleton.tsx` | `HomePageSkeleton.tsx` |
| `bg-f1gray/30` + `bg-f1gray/20` skeleton colours | All existing skeletons | `HomePageSkeleton.tsx` |
| `DEFAULT_ROUND = 24`, `DEFAULT_SEASON = 2025` | `app/race/RaceContent.tsx` | `track/page.tsx` defaults |
| Named export + `searchParams` page pattern | `app/track/[round]/page.tsx` (adapted) | `app/track/page.tsx` |
| `Metadata` + `generateMetadata` pattern | `app/qualifying/page.tsx` | `app/page.tsx`, `app/track/page.tsx` |

---

## 5. Pre-Implementation Diagnostic

Before writing any code, a comprehensive diagnostic was conducted across 8 dimensions of the codebase. This diagnostic identified several critical findings that directly shaped the implementation.

### 5.1 Diagnostic Scope

| Section | What Was Examined |
|---------|------------------|
| Application Structure | Monorepo layout, routing patterns, build pipeline |
| Current Home Page State | SessionSummary content, imports, what needed removal |
| Navigation Flow | RaceWeekendSelector mechanics, active state detection, link structure |
| Completed Pages | Qualifying, Race, Practice, Track Intelligence — patterns and conventions |
| Performance Constraints | Lighthouse baselines, bundle sizes, critical rendering path |
| Design System | Tailwind theme, CSS classes, font stack, colour palette |
| Backend Considerations | API dependencies (none for Home), service architecture |
| Summary Checklist | 18-item verification across all sections |

### 5.2 Critical Findings That Changed the Plan

**Finding 1: Next.js 14, not 15.** The initial implementation prompt assumed Next.js 15, where `searchParams` is a Promise requiring `await`. The diagnostic identified `"next": "^14.1.0"` in `package.json`. In Next.js 14, `searchParams` is a synchronous plain object. Using the wrong API would have caused a runtime error on every Track Intelligence page load.

**Impact:** All `searchParams` usage was written for the synchronous API. The type definition uses `{ searchParams: { round?: string; season?: string } }` instead of `{ searchParams: Promise<{ round?: string }> }`.

**Finding 2: Favicon filename contained a space.** The initial prompt referenced `ApexViewIcon(1).svg`. The actual filename was `ApexViewIcon (1).svg` (with a space before the parenthesis). The copy command would have failed silently or targeted the wrong file.

**Impact:** The copy command was corrected to quote the path, ensuring the correct file was copied.

**Finding 3: TrackIntelligenceContent uses a named export.** The component uses `export function TrackIntelligenceContent` rather than `export default function`. A default import (`import TrackIntelligenceContent from './TrackIntelligenceContent'`) would have compiled but rendered `undefined` at runtime.

**Impact:** The import in the new `page.tsx` uses the named import syntax: `import { TrackIntelligenceContent } from './TrackIntelligenceContent'`.

**Finding 4: Track Intelligence accepted no `season` prop.** The component signature was `{ round, season = 2025 }` with a default. The old `page.tsx` only passed `round`. The new page passes both `round` and `season` from search params, enabling the `RaceWeekendSelector` to drive season context.

**Finding 5: The `panels/` directory had 14 other files.** Deleting the directory or using a broad cleanup would have destroyed the entire Qualifying telemetry analysis pipeline's frontend components. Only `SessionSummary.tsx` was targeted for deletion.

### 5.3 Diagnostic Methodology

The diagnostic was conducted using three parallel exploration agents that examined:
1. Track Intelligence route implementation (dynamic route structure, component exports, props interface).
2. Panels directory inventory and favicon source verification (file listing, import tracing).
3. Next.js configuration and RaceWeekendSelector mechanics (version detection, URL state flow).

This parallel exploration approach reduced diagnostic time while ensuring comprehensive coverage. Each agent reported findings that were cross-referenced before the implementation plan was finalised.

---

## 6. Learnings and How They Influenced Decisions

### 6.1 Learning: Framework Version Assumptions Must Be Verified

**Observation:** The implementation prompt specified Next.js 15 `searchParams` API (Promise-based). The actual version was 14.1.0 (synchronous object). This is a breaking difference — code written for one version will fail at runtime on the other.

**Decision:** Added a version verification step to the pre-implementation diagnostic. The `package.json` was read and version confirmed before any route migration code was written.

**Impact:** This prevented a runtime error that would have manifested only when the Track Intelligence page was loaded — potentially after all other Phase 1 changes were already committed. The lesson generalises: framework API assumptions in implementation prompts must be verified against the actual installed version.

### 6.2 Learning: TypeScript Build Cache Must Be Cleared After Route Deletion

**Observation:** After deleting the `apps/web/app/track/[round]/` directory, `npx tsc --noEmit` failed with:

```
Cannot find module '../../../../../app/track/[round]/page.js'
```

The error originated from `.next/types/app/track/[round]/page.ts` — a cached type stub that Next.js had generated during previous builds. The stub referenced the deleted file.

**Decision:** Added `rm -rf apps/web/.next/types/app/track/\[round\]` to the verification workflow to clear stale type stubs before running TypeScript checks.

**Impact:** Without this cleanup, the TypeScript verification would have produced a false negative — reporting errors in deleted code that no longer exists. The lesson: deleting Next.js route directories requires clearing the corresponding `.next/types/` cache entries.

### 6.3 Learning: Local Build Errors Must Be Distinguished from Code Defects

**Observation:** The local `pnpm --filter web build` succeeded in compilation (10/10 pages generated, TypeScript passed) but failed at the `writeStandaloneDirectory` step with `EPERM: operation not permitted, symlink`. This is a pre-existing Windows/OneDrive issue with `output: 'standalone'` — OneDrive's file sync mechanism prevents symlink creation.

**Decision:** The Docker build was used as the authoritative verification. The same `pnpm --filter web build` command runs inside the Docker container (Alpine Linux) where symlink creation succeeds. The local EPERM error was documented as a known environment issue, not a Phase 1 regression.

**Impact:** This reinforced the Docker-first verification approach — the containerised build environment is the ground truth. Local builds on Windows/OneDrive are useful for fast TypeScript checking but not reliable for full standalone output verification.

### 6.4 Learning: Route Normalisation Requires Comprehensive Redirect Testing

**Observation:** The redirect from `/track/:round` to `/track?round=:round` needed verification at multiple levels: HTTP status code (308), `Location` header correctness, and end-to-end browser follow-through.

**Decision:** Three separate curl commands were used to validate the redirect:
1. `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/track/24` — verifies 308 status.
2. `curl -s -I http://localhost:3000/track/24 | grep -i "location"` — verifies redirect destination.
3. `curl -s -o /dev/null -w "%{http_code}" -L http://localhost:3000/track/24` — verifies the destination returns 200 after following the redirect.

**Impact:** All three checks passed, confirming that the redirect works at the HTTP level, the destination is correct, and the destination page renders successfully. Testing only the final 200 (with `-L`) would have missed a broken redirect that happened to land on a valid 200 page by coincidence.

### 6.5 Learning: Docker-First Verification Catches Environment-Specific Issues

**Observation:** The local TypeScript check and Docker build exercise the same codebase but in different environments. The local check caught the stale type cache issue (Learning 6.2). The Docker build confirmed the code compiles cleanly in a fresh environment without cache artifacts.

**Decision:** The verification workflow was structured as a 5-stage pipeline: pre-flight static checks (local) then Docker build then container health then implementation-specific validation then teardown. Local checks catch fast-feedback issues (broken imports, type errors). Docker checks confirm the production build succeeds.

**Impact:** This dual-layer approach caught issues that either layer alone would have missed. The local pre-flight check identified the cached type stub before attempting a Docker build (saving build time). The Docker build confirmed the standalone output works correctly (which the local build cannot verify on Windows/OneDrive).

### 6.6 Learning: Skeleton Design Should Anticipate Content Layout

**Observation:** The HomePageSkeleton was designed to mirror the three-section layout planned for the completed Home page (hero, feature cards, capabilities). This forward-looking design ensures the skeleton-to-content transition is seamless — the skeleton blocks are positioned where the actual content will render.

**Decision:** Rather than using a generic loading spinner, the skeleton uses dimensioned placeholder blocks that match the planned content dimensions. The hero skeleton uses `h-16 w-2/3` for the title (matching a 3-line heading), `h-8 w-1/2` for the subtitle, and three `h-12 w-32` blocks for stat counters. The feature cards use the `card-panel` class to match the actual card styling.

**Impact:** When Phase 2 replaces `HomeContent` with actual content, the visual transition from skeleton to content will be smooth — elements appear in the same positions as their skeleton placeholders. This follows the established pattern: PracticePageSkeleton matches PracticeContent's panel layout, QualifyingPageSkeleton matches QualifyingContent's tabs-and-panels layout.

---

## 7. Testing, Verification and Validation

### 7.1 Verification Philosophy: Docker-First

The verification approach prioritises Docker-based validation because the application is deployed as a containerised 3-service stack. A passing local build on Windows/OneDrive does not guarantee production correctness (due to symlink issues, path differences, and cache artifacts). The Docker build in Alpine Linux matches the production environment exactly.

### 7.2 Stage 1: Pre-Flight Static Checks

Run before Docker build to catch obvious issues early and avoid long rebuild cycles.

| Check | Command | Expected | Result |
|-------|---------|----------|--------|
| TypeScript compilation | `npx tsc --noEmit` | Zero errors | Initially failed (cached type stub), passed after cache cleanup |
| Stale SessionSummary references | `grep -rn "SessionSummary" apps/web/` | No output | Passed — no references remain |
| Stale `params.round` references | `grep -rn "params\.round" apps/web/app/track/` | No output | Passed — old pattern fully removed |
| Stale `[round]` imports | `grep -rn "from './[round]" apps/web/app/track/` | No output | Passed — no imports reference old directory |
| Favicon file exists | `ls -la apps/web/app/icon.svg` | File exists, non-zero | Passed — 3,658 bytes |
| Old `[round]` directory deleted | `ls apps/web/app/track/[round]/` | "No such file" | Passed — directory removed |
| New route files exist | `ls apps/web/app/track/` | `page.tsx`, `TrackIntelligenceContent.tsx` | Passed — both files present |

### 7.3 Stage 2: Docker Build

```
docker-compose build --no-cache
```

The `--no-cache` flag ensures a clean build without layer caching, verifying that all dependencies resolve correctly. The web service build step (`pnpm --filter web build` inside the Dockerfile) performs the full Next.js production build in the clean Alpine Linux environment.

| Check | Result |
|-------|--------|
| Docker build completes | Exit code 0, all 3 images built |
| `pnpm --filter web build` inside container | 10/10 pages compiled successfully |
| No "Module not found" errors | No references to deleted files |
| Standalone output generated | `COPY --from=builder ... /standalone` succeeded |
| Redirect config accepted | No build-time errors from `next.config.js` |

### 7.4 Stage 3: Container Health

```
docker-compose up -d
```

| Service | Port | Health Check | Status |
|---------|------|-------------|--------|
| f1-api | 8000 | `GET /health` | Healthy |
| f1-analysis | 8501 | Analysis service probe | Healthy |
| f1-web | 3000 | `GET /` | Serving (200) |

### 7.5 Stage 4: Implementation-Specific Validation

15 checks run against the Dockerised application at `http://localhost:3000`.

#### 4a: Home Page — Placeholder Removal

| Check | Method | Result |
|-------|--------|--------|
| No fake data (SessionSummary content) | `curl` + grep for "SessionSummary", "1:32.837", "342 km/h", "Weekend Overview" | No matches — all fake data removed |
| Placeholder text visible | `curl` + grep for "Phase 2" | Match found — new placeholder renders |
| Metadata correct | `curl` + grep for "ApexView" | Match found — page-level metadata active |

#### 4b: Favicon

| Check | Method | Result |
|-------|--------|--------|
| Icon file served | `curl /icon.svg` → HTTP status | 200 |
| Auto-generated link tag | `curl /` + grep for "icon" | `<link rel="icon" href="/icon.svg?c45e97863bd58fa0">` present |

#### 4c: Track Intelligence Route Migration

| Check | Method | Result |
|-------|--------|--------|
| New route (default) | `curl /track` → status | 200 |
| New route (explicit round) | `curl /track?round=1` → status | 200 |
| Old route redirect status | `curl /track/24` → status (no follow) | 308 |
| Redirect destination | `curl -I /track/24` → Location header | `/track?round=24` |
| End-to-end follow | `curl -L /track/24` → status | 200 (destination renders) |

#### 4d: Navigation Bar Completeness

| Check | Method | Result |
|-------|--------|--------|
| All 5 nav hrefs present | `curl /` + grep for each href | `/`, `/qualifying`, `/race`, `/practice`, `/track` all found |
| Track Intelligence on all pages | `curl` each page + grep "Track Intelligence" | Present on all 5 pages |
| Active state indicator (Home) | `curl /` + grep `aria-current="page"` | 1 match (Home link active) |
| Active state indicator (Track) | `curl /track` + grep `aria-current="page"` | 1 match (Track link active) |

#### 4e: Cross-Service API Integration

| Check | Method | Result |
|-------|--------|--------|
| Track API accessible | `curl http://localhost:8000/track/1?season=2025` → status | 200 |

#### 4f: Existing Pages Regression

| Page | HTTP Status | Result |
|------|------------|--------|
| `/qualifying` | 200 | No regression |
| `/race` | 200 | No regression |
| `/practice` | 200 | No regression |

### 7.6 Stage 5: Teardown

```
docker-compose down
```

All containers stopped and removed. Network (`apexview_f1-network`) removed. Clean shutdown confirmed.

### 7.7 Phase 1 Completion Gate

All items true simultaneously:

| Item | Required State | Verified |
|------|---------------|----------|
| Docker build | Completes without errors | Yes |
| All 3 containers | Healthy / serving | Yes |
| Favicon | Visible, `/icon.svg` returns 200 | Yes |
| SessionSummary | Deleted, no references remain | Yes |
| `/` route | Renders placeholder, no fake data | Yes |
| `/track` route | Loads correctly, defaults to round 24 | Yes |
| `/track?round=N` | Loads correct round data | Yes |
| `/track/N` redirect | 308 to `/track?round=N` | Yes |
| Navigation bar | 5 links, active states correct | Yes |
| API integration | Track page reaches API container | Yes |
| Existing pages | No regressions on /qualifying, /race, /practice | Yes |
| TypeScript | Zero compilation errors | Yes |

---

## 8. Alignment with Broader Home Page Plan

### 8.1 What Phase 1 Established for Phases 2 and 3

**Server Component shell:** The `page.tsx` exports complete metadata (title, description, OpenGraph) and wraps `<HomeContent />` in a `<Suspense>` boundary. Phase 2 replaces `HomeContent` — the page shell is fixed.

**Skeleton:** `HomePageSkeleton` mirrors the planned 3-section layout. Phase 2 and Phase 3 content renders within the same visual structure, ensuring smooth skeleton-to-content transitions.

**Navigation context:** All 5 analytical pages are now accessible from the nav bar. The Home page can link to each page using standard `<Link>` components with confidence that the destinations exist and render correctly. The `RaceWeekendSelector` drives context across all pages including Track Intelligence.

**Route consistency:** Every page now uses the same URL state convention (`?round=&season=`). Phase 2's feature cards can construct internal links using consistent patterns.

**Brand identity:** The favicon appears across all pages immediately — no additional per-page work is needed.

### 8.2 Phase 2 — Content and Identity (Complete)

Phase 2 replaced `HomeContent.tsx` with:

- **Hero section:** Platform title ("ApexView"), purpose line ("Where Formula 1 Data Becomes Insight"), server-derived season statistics (2025, 24 rounds, next race / "Season Complete"), and a CTA linking to `/race`.
- **Feature cards:** 2×2 grid linking to the four analytical pages (Qualifying, Race, Practice, Track Intelligence) with analytical questions and capability pills.
- **Platform capabilities:** 8-item grid summarising every type of analysis ApexView supports, with "What You Can Explore" heading.
- The hero section serves as the LCP element — this is why Phase 1's page shell omits the `border-l-4` header used by analytical pages.

### 8.3 Phase 3 — Polish and Performance (Complete)

Phase 3 added:

- **CSS entrance animations:** 400ms fadeSlideIn with 150ms section stagger, `prefers-reduced-motion` hard override.
- **Accessibility remediation:** sr-only h2 for heading hierarchy, focus-ring on CTA and FeatureCards, dynamic aria-label on RaceWeekendSelector.
- **Application-wide metadata:** All 5 pages + root layout corrected to `Page Name | ApexView` pattern with OpenGraph. Zero "F1 Engineering" references remain.
- **Lighthouse final:** Performance 97, Accessibility 100, Best Practices 100, SEO 100 (Desktop preset: 100/100/100/100).

### 8.4 Why This Phased Approach

The three-phase structure reflects a principle established across the Race and Practice page implementations: **build the foundation first, then add content, then polish.** Each phase has a clear completion gate and produces a deployable, testable artifact.

Phase 1 is the only phase that modifies cross-cutting infrastructure (routing, navigation, configuration). Phases 2 and 3 are scoped entirely to `HomeContent.tsx` — they cannot introduce routing regressions or navigation inconsistencies because the structural foundation is already verified and stable.

---

*Documentation Version 1.1 — March 2026 (v1.1: Updated Phase 2 and 3 status from Planned to Complete with final deliverables.)*
