# Home Page Phase 2: Content and Identity

**Status:** Complete
**Implemented:** March 2026
**TypeScript:** Zero compilation errors
**Docker Build:** Clean exit, all 3 services healthy (f1-api, f1-ml, f1-web)
**Verification:** 15/15 completion gate items passing
**Files Created:** 4 | **Files Modified:** 2

---

## Table of Contents

1. [Purpose and Significance](#1-purpose-and-significance)
2. [Theoretical and Logical Background](#2-theoretical-and-logical-background)
3. [End-to-End Workflow and Data Flow](#3-end-to-end-workflow-and-data-flow)
4. [Technical Implementation Breakdown](#4-technical-implementation-breakdown)
5. [Pre-Implementation Diagnostic and Corrections](#5-pre-implementation-diagnostic-and-corrections)
6. [Learnings and Decisions](#6-learnings-and-decisions)
7. [Testing, Verification, and Validation](#7-testing-verification-and-validation)
8. [Alignment with Broader Home Page Plan](#8-alignment-with-broader-home-page-plan)

---

## 1. Purpose and Significance

### What Phase 2 Delivers

Phase 2 transforms the Home page from an empty structural shell (Phase 1) into ApexView's visual identity and navigational entry point. Where Phase 1 established the Server Component architecture, Suspense boundary, skeleton, favicon, route normalisation, and 5-link navigation bar, Phase 2 fills that architecture with three content sections that communicate what ApexView does and where users can go.

Before Phase 2, the Home page rendered a single placeholder line: `"Home page content — Phase 2"`. After Phase 2, it renders:

1. **Hero Section** — The platform's name, purpose statement, live season statistics, and a call-to-action button, layered over a dark gradient backdrop.
2. **Feature Cards** — Four navigational cards (one per analytical page) that pose analytical questions and display capability pills.
3. **Platform Capabilities** — An 8-item grid summarising every type of analysis ApexView supports.

### Position in the Home Page Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Structural Foundation — Server Component shell, Suspense, skeleton, favicon, route normalisation, navigation | Complete |
| **Phase 2** | **Content and Identity — Hero, feature cards, platform capabilities, season stats** | **Complete** |
| Phase 3 | Polish and Performance — Lighthouse audit, accessibility remediation, CSS animations, metadata consistency | Complete |

Phase 2 occupies a critical position: it is the first phase where the user sees meaningful content. Phase 1 was invisible to end users (infrastructure changes). Phase 2 is the first impression — it must convey ApexView's analytical depth while maintaining the dark, data-driven visual language established across Qualifying, Race, Practice, and Track Intelligence pages.

### Key Constraint

Phase 2 produces **zero API calls, zero backend changes, and zero new React Query hooks**. The only external data consumed is the existing static `race-calendar-2025.json` file, read at server render time. This constraint is intentional — the Home page is a static navigational entry point, not an analytical dashboard. All analytical complexity lives in the four destination pages.

---

## 2. Theoretical and Logical Background

### 2.1 Static Over Dynamic

The Home page's data requirements are fundamentally different from the analytical pages. Qualifying, Race, and Practice pages fetch live telemetry data from FastAPI endpoints and render it through React Query hooks with loading states, error boundaries, and skeleton fallbacks. The Home page has no such needs — its content is known at build time.

This recognition drives the entire Phase 2 architecture: instead of introducing API endpoints, fetch functions, and query hooks, Phase 2 imports a static JSON file directly into the Server Component and derives display values at render time. The result is zero network requests for the Home page's content, zero loading states beyond the initial Suspense boundary, and zero client-side data fetching overhead.

### 2.2 Server-Side Calendar Derivation

The `deriveSeasonStats()` function runs exclusively on the server inside `page.tsx`. It accepts the race calendar array and returns four values: `season`, `totalRounds`, `nextRaceName`, and `nextRaceRound`. The function compares each race's date against the current date to find the next upcoming event.

This server-side derivation has two advantages:

1. **No client-side date logic** — The comparison runs once on the server, and the result is serialised into the page's HTML. The client receives pre-computed strings and numbers, not a calendar array to iterate.
2. **Edge case handling** — When all races are in the past, the function returns `"Season Complete"` with a `null` round, and the `SeasonStats` component switches its label from "Next Race" to "Status". This avoids displaying stale race names after the season ends.

### 2.3 Three-Section Landing Architecture

The Home page's content is organised into three sections with distinct communication purposes:

| Section | Purpose | Communication Style |
|---------|---------|-------------------|
| Hero | Identity — "what is this" | Visual impact, brand recognition, season context |
| Feature Cards | Navigation — "where can I go" | Analytical questions, capability discovery |
| Platform Capabilities | Scope — "what can it do" | Comprehensive feature inventory |

This architecture follows a progressive disclosure pattern: the hero establishes trust and identity, the feature cards provide navigational paths, and the capabilities section provides depth for users who want to understand the full scope before navigating.

### 2.4 Skeleton-Content Dimensional Contract

Phase 1 created `HomePageSkeleton.tsx` with three skeleton groups that anticipate Phase 2's three content sections. This creates a dimensional contract:

| Skeleton Group | Dimensions | Phase 2 Content |
|---------------|------------|-----------------|
| Hero skeleton | `py-16`, `h-16` headline, `h-8` tagline, 3× `h-12 w-32` stats | HeroSection with `py-16 sm:py-20` padding, headline, tagline, 3 stat counters |
| Card grid skeleton | `grid-cols-1 md:grid-cols-2 gap-6`, 4× `card-panel` | 4× FeatureCard in identical grid |
| Capabilities skeleton | `h-6` header, `grid-cols-1 md:grid-cols-2 gap-3`, 6× items | PlatformCapabilities with 8 items in identical grid |

When the Suspense boundary resolves, the skeleton is replaced by real content. If the content dimensions match the skeleton dimensions, the layout shift is imperceptible. Phase 1's skeleton was designed with Phase 2's exact layout in mind — this is a forward-looking architectural pattern where the loading state is a layout contract, not just a visual placeholder.

### 2.5 Component Composition via Layering

The HeroSection uses a two-layer composition to create visual depth:

```
Layer 2 (z-10): Content — headline, tagline, stats, CTA
Layer 1:        Gradient backdrop — from-f1dark/90 via-f1dark/80 to-f1dark/95
```

Layer 1 provides the dark gradient backdrop that establishes the hero's visual weight and ensures text contrast. Layer 2 contains all interactive content at the highest z-index.

> **Design decision (March 2026):** An earlier iteration included a third layer of decorative circuit SVG outlines between the gradient and content. After implementation and visual evaluation, the circuit backgrounds were intentionally removed — CSS `overflow-hidden` containment caused clipping artefacts where circuits extended beyond the hero bounds, and the SVGs overlapped adjacent page components. The two-layer approach produces a cleaner result that better serves the page's navigational purpose.

This layering pattern avoids the complexity of CSS blend modes or canvas rendering. Each layer is a simple `<div>` with absolute positioning, making the composition inspectable, debuggable, and performant.

### 2.6 Reuse-First Design

Phase 2 creates zero new CSS classes, zero new Tailwind config entries, and zero new global styles. Every visual treatment reuses existing design tokens:

| Token | Defined In | Used By |
|-------|-----------|---------|
| `card-panel` | `globals.css` | `FeatureCard.tsx` |
| `shadow-glow-red-sm` | `tailwind.config.js` | `FeatureCard.tsx`, `HeroSection.tsx` CTA |
| `border-l-4 border-f1red pl-4` | Qualifying/Race/Practice headers | `PlatformCapabilities.tsx` |
| `font-heading font-extrabold uppercase` | Qualifying page headline | `HeroSection.tsx` headline |
| `font-mono tabular-nums` | Race/Practice stat panels | `SeasonStats.tsx` values |
| `text-f1red` | All pages | `HeroSection.tsx` tagline, `FeatureCard.tsx` hover |
| `bg-f1gray/10`, `border-f1gray/50` | Card and divider treatments across pages | `FeatureCard.tsx` pills, `PlatformCapabilities.tsx` items |
| `animate-pulse`, `bg-f1gray/30` | All existing skeletons | `HomePageSkeleton.tsx` (Phase 1, unchanged) |

This reuse-first approach ensures visual consistency with the analytical pages and eliminates the risk of style conflicts or token proliferation. It also means Phase 2 touches zero configuration files — `globals.css`, `tailwind.config.js`, and `next.config.js` are all locked.

---

## 3. End-to-End Workflow and Data Flow

### 3.1 Data Flow

Phase 2's data flow is deliberately simple — no API calls, no async fetching, no loading states for content:

```
┌─────────────────────────────────────────────────────────┐
│  Build/SSR Time (Server)                                │
│                                                         │
│  race-calendar-2025.json                                │
│       │                                                 │
│       ▼                                                 │
│  page.tsx (Server Component)                            │
│       │ import raceCalendarData                         │
│       │ deriveSeasonStats(raceCalendarData.races)        │
│       │     → { season: 2025, totalRounds: 24,          │
│       │        nextRaceName: "...", nextRaceRound: N }   │
│       │                                                 │
│       ▼                                                 │
│  <Suspense fallback={<HomePageSkeleton />}>             │
│       │                                                 │
│       ▼                                                 │
│  <HomeContent seasonStats={seasonStats} />              │
│                                                         │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼ (Hydration)
┌─────────────────────────────────────────────────────────┐
│  Client (Browser)                                       │
│                                                         │
│  HomeContent ('use client')                             │
│       │                                                 │
│       ├── HeroSection                                   │
│       │     ├── Gradient backdrop                       │
│       │     └── SeasonStats (3 counters)                │
│       │                                                 │
│       ├── Feature Cards (4× FeatureCard)                │
│       │     └── Each: title + question + pills          │
│       │                                                 │
│       └── PlatformCapabilities (8 items)                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Calendar Data Path

```
data/race-calendar-2025.json
    → import raceCalendarData from '@/data/race-calendar-2025.json'
    → raceCalendarData.races  (array of 24 race objects)
    → deriveSeasonStats(races)
    → SeasonStats { season, totalRounds, nextRaceName, nextRaceRound }
    → prop to HomeContent → prop to HeroSection → prop to SeasonStatsDisplay
```

The JSON import uses the established pattern from `RaceWeekendSelector.tsx`. The data is accessed via `raceCalendarData.races` (not the top-level object directly), with each race having `round`, `name`, `date`, and optionally `isSprint` fields.

### 3.3 What Is NOT in the Data Flow

Phase 2 intentionally omits:

- **No React Query hooks** — No `useSomethingQuery()` hooks. Data is static.
- **No fetch functions** — No `fetchSomething()` in `lib/api.ts`. Data is imported.
- **No loading states for content** — The Suspense boundary (Phase 1) handles the initial shell; individual panels do not need `isLoading` / `isError` / `isPlaceholderData` states.
- **No `staleTime` or cache configuration** — No cache needed for build-time data.
- **No backend endpoints** — No new routes in `routes/practice.py`, `routes/race.py`, etc.

---

## 4. Technical Implementation Breakdown

### 4.1 Files Inventory

| Action | File | Purpose |
|--------|------|---------|
| Modify | `apps/web/app/page.tsx` | Calendar import, `SeasonStats` interface, `deriveSeasonStats()`, prop passthrough |
| Rewrite | `apps/web/app/HomeContent.tsx` | Replace placeholder with 3-section layout orchestrator |
| Create | `apps/web/components/home/HeroSection.tsx` | Hero with headline, tagline, stats, CTA, gradient backdrop |
| Create | `apps/web/components/home/SeasonStats.tsx` | 3 stat counters (Season, Rounds, Next Race) |
| Create | `apps/web/components/home/FeatureCard.tsx` | Navigational card with question + capability pills |
| Create | `apps/web/components/home/PlatformCapabilities.tsx` | 8-item capability grid with section header |

### 4.2 Component Hierarchy

```
page.tsx (Server Component — derives seasonStats, passes as prop)
  └── HomeContent.tsx (Client Component — layout orchestrator)
        ├── HeroSection.tsx
        │     └── SeasonStats.tsx (imported as SeasonStatsDisplay)
        ├── FeatureCard.tsx (×4, rendered via FEATURE_CARDS.map())
        └── PlatformCapabilities.tsx
```

### 4.3 page.tsx — Server Component Modifications

**What changed:** Three additions to the existing Phase 1 Server Component. Metadata, Suspense boundary, and container class are completely unchanged.

**Addition 1: Calendar import**

```typescript
import raceCalendarData from '@/data/race-calendar-2025.json'
```

Follows the same pattern used by `RaceWeekendSelector.tsx`. The JSON module resolution is enabled by `resolveJsonModule: true` in `tsconfig.json`.

**Addition 2: SeasonStats interface and deriveSeasonStats()**

```typescript
export interface SeasonStats {
  season: number
  totalRounds: number
  nextRaceName: string
  nextRaceRound: number | null
}
```

The interface is exported as a named export so that `HomeContent.tsx` and `SeasonStats.tsx` can import it via `import type { SeasonStats } from '@/app/page'`. This keeps the type co-located with the function that produces it.

`deriveSeasonStats()` accepts the races array typed as `typeof raceCalendarData.races` — this leverages TypeScript's inferred JSON types rather than defining a separate `Race` interface. The function:

1. Creates a `today` date zeroed to midnight (prevents time-of-day comparison issues)
2. Finds the first race whose date is >= today (chronological order guaranteed by the JSON)
3. Returns `"Season Complete"` with `null` round when no future race exists

**Addition 3: Prop passthrough**

```typescript
const seasonStats = deriveSeasonStats(raceCalendarData.races)
// ...
<HomeContent seasonStats={seasonStats} />
```

The computation runs on the server at render time. The result is serialised into the page's RSC payload and arrives at the client as pre-computed data.

### 4.4 HomeContent.tsx — Layout Orchestrator

Replaced the Phase 1 placeholder with a `'use client'` component that renders three sections with `space-y-16` vertical rhythm (wider than the `space-y-12` on the outer container, creating intentional breathing room between landing page sections).

**Feature card data** is defined as a `FEATURE_CARDS` constant array (`as const`) with four entries:

| Card | `href` | Question | Capabilities |
|------|--------|----------|-------------|
| Qualifying | `/qualifying` | Who was genuinely fastest over a single lap, and why? | Lap Deltas, Sector Breakdown, AI Technique Profiles |
| Race | `/race` | How did strategy, tyre degradation, and pit stops shape the result? | Pace Distribution, Tyre Degradation, Pit Stop Analysis |
| Practice | `/practice` | What do long run stints and short run pace reveal about race day form? | Long Run Pace, Sector Analysis, Session Progression |
| Track Intelligence | `/track` | What defines each circuit and how does it influence strategy? | Circuit Data, Tyre Characteristics, Strategic Insights |

The cards are rendered via `.map()` in a `grid-cols-1 md:grid-cols-2 gap-6` grid — matching the skeleton's identical grid definition.

### 4.5 HeroSection.tsx — Visual Identity

The hero establishes ApexView's visual identity through a two-layer composition (gradient backdrop + content):

**Headline:** `"ApexView"` split into "Apex" (white) + "View" (f1red) using an inline `<span>`. Montserrat weight-800 via `font-heading font-extrabold`, uppercase with tight tracking. Responsive sizing: `text-5xl sm:text-6xl md:text-7xl`.

**Purpose line:** `"Where Formula 1 Data Becomes Insight"` in f1red, positioned below the headline with `mt-4`. Font-medium weight, wider tracking.

**Season stats:** The `SeasonStatsDisplay` component renders below the tagline with `mt-8` spacing.

**CTA button:** `"Explore Race Data →"` linking to `/race`. Styled with an f1red border and tinted background (`bg-f1red/10`), uppercase Montserrat, and a hover state that intensifies the background and adds the red glow shadow (`hover:shadow-glow-red-sm`). The arrow is a separate `<span>` with `aria-hidden="true"`.

**Container:** `relative rounded-lg` — simple container with rounded corners for the hero boundary.

### 4.6 SeasonStats.tsx — Stat Counters

Three stat groups separated by vertical dividers:

| Stat | Value Source | Font | Size |
|------|------------|------|------|
| Season | `seasonStats.season` (2025) | JetBrains Mono (`font-mono`) | `text-2xl sm:text-3xl` |
| Rounds | `seasonStats.totalRounds` (24) | JetBrains Mono (`font-mono`) | `text-2xl sm:text-3xl` |
| Next Race | `seasonStats.nextRaceName` | JetBrains Mono (`font-mono`) | `text-base sm:text-lg` |

**Font pairing:** Values use JetBrains Mono with `tabular-nums` for numerical alignment. Labels use Inter (inherited body font) at `text-xs uppercase tracking-wider text-gray-400`.

**Dividers:** `w-px h-12 bg-f1gray/50` — 1px wide, 12px tall, semi-transparent grey. This matches the divider treatment used in Race and Practice page stat panels.

**Edge case:** When `nextRaceRound === null`, the component renders `"Season Complete"` as the value and switches the label from `"Next Race"` to `"Status"`. This was verified during Docker validation (see Section 7) — since the calendar contains 2025 dates and the current date is March 2026, the edge case was naturally triggered.

### 4.7 FeatureCard.tsx — Navigational Cards

Each card is wrapped in a Next.js `<Link>` component, making the entire card a clickable navigation target. The card uses the existing `card-panel` CSS class (`rounded-lg border border-f1gray bg-f1dark/80 backdrop-blur-sm p-6`) combined with Tailwind's `group` utility for coordinated hover effects.

**Hover coordination:**

| Element | Default State | Hover State | Transition |
|---------|--------------|-------------|------------|
| Card border | `border-f1gray` (via `card-panel`) | `border-f1red` | 200ms all |
| Card shadow | none | `shadow-glow-red-sm` | 200ms all |
| Title colour | `text-white` | `text-f1red` | 200ms color |
| Arrow opacity | `opacity-0` | `opacity-100` | 200ms opacity |

**Height equalisation:** The question text uses `flex-1` within a `flex flex-col` card container. This ensures that cards with shorter questions expand their question area to match taller neighbours, keeping the capability pills divider at a consistent vertical position across the 2×2 grid.

**Capability pills:** Below a `border-t border-f1gray/50` divider, three pills per card render in a flex-wrap layout. Each pill uses `rounded-full border border-f1gray/50 bg-f1gray/10 px-3 py-1 font-mono text-xs text-gray-400` — monospace font for technical terminology, subtle border and background tint for visual separation.

### 4.8 PlatformCapabilities.tsx — Scope Communication

Eight capability statements presented in a 2-column responsive grid (`grid-cols-1 md:grid-cols-2 gap-3`):

1. Compare qualifying lap deltas with sector-level precision
2. Analyse race pace distribution across all drivers and compounds
3. Track tyre degradation rates with fuel-corrected regression
4. Evaluate pit stop performance with consistency scoring
5. Study team aerodynamic philosophy via speed decomposition
6. Assess practice long run pace and short run qualifying simulations
7. Explore circuit characteristics across all 24 Grand Prix venues
8. Monitor session progression from FP1 through FP3

**Section header:** Uses the standard `border-l-4 border-f1red pl-4` pattern from the analytical pages (Qualifying, Race, Practice). Title: `"What You Can Explore"` in Montserrat uppercase bold.

**Item treatment:** Each item has a red dot bullet (`w-1.5 h-1.5 rounded-full bg-f1red`, with `mt-1.5` for baseline alignment and `flex-shrink-0` to prevent compression) and card-style treatment (`rounded-lg border border-f1gray/30 bg-f1gray/10 px-4 py-3`). Text in `text-sm leading-relaxed text-gray-300` — slightly brighter than the feature card question text (`text-gray-400`) since these are the primary content, not secondary descriptions.

### 4.9 Existing Patterns Reused

| Pattern | Source File | Reused In |
|---------|-----------|-----------|
| `card-panel` CSS class | `globals.css` | `FeatureCard.tsx` card wrapper |
| `shadow-glow-red-sm` box shadow | `tailwind.config.js` | `FeatureCard.tsx` hover, `HeroSection.tsx` CTA hover |
| `border-l-4 border-f1red pl-4` header | `app/qualifying/page.tsx`, `app/race/page.tsx`, `app/practice/page.tsx` | `PlatformCapabilities.tsx` section header |
| `font-heading font-extrabold uppercase` headline | `app/qualifying/page.tsx` | `HeroSection.tsx` h1 |
| `font-mono tabular-nums` data display | Race/Practice stat panels | `SeasonStats.tsx` stat values |
| Calendar JSON import pattern | `components/layout/RaceWeekendSelector.tsx` | `page.tsx` |
| `group` + `group-hover:*` coordination | General Tailwind pattern | `FeatureCard.tsx` |
| `animate-pulse` skeleton convention | All page skeletons | `HomePageSkeleton.tsx` (Phase 1, unchanged) |

---

## 5. Pre-Implementation Diagnostic and Corrections

### 5.1 Diagnostic Methodology

Before writing any code, the implementation prompt was validated against the actual codebase through parallel exploration agents. Three agents simultaneously searched different areas:

1. **Calendar & SVG agent** — Examined `race-calendar-2025.json` structure, `public/tracks/` directory listing, and `circuitMap.ts` mapping
2. **Phase 1 files agent** — Verified `page.tsx`, `HomeContent.tsx`, `HomePageSkeleton.tsx` state, and existing patterns
3. **Import patterns agent** — Checked `RaceWeekendSelector.tsx` calendar import pattern, TypeScript types, and path aliases

This parallel exploration took approximately 60 seconds and identified three discrepancies between the implementation prompt and the actual codebase.

### 5.2 Discrepancies Identified and Corrected

| # | Area | Prompt Assumed | Actual Codebase | Correction Applied |
|---|------|----------------|-----------------|-------------------|
| 1 | SVG filenames | Round numbers (`/tracks/6.svg`, `/tracks/18.svg`) | Descriptive names (`/tracks/monaco.svg`, `/tracks/singapore.svg`) | Used descriptive filenames from `circuitMap.ts` mapping (applied to circuit background feature, since removed — see Section 2.5) |
| 2 | Calendar JSON structure | Direct array access (`calendar.find(...)`, `calendar.length`) | Nested in `.races` property (`raceCalendarData.races`) | Accessed via `.races` property, matching `RaceWeekendSelector` pattern |
| 3 | Calendar field names | Placeholder tokens `[DATE_FIELD]`, `[NAME_FIELD]`, `[ROUND_FIELD]` | Actual fields: `date`, `name`, `round` | Used confirmed field names throughout |

### 5.3 Impact of Corrections

**SVG filename correction** — This correction applied to an earlier iteration of the hero that included decorative circuit SVG backgrounds (since removed — see Section 2.5). The correction identified that SVG filenames use descriptive names (`monaco.svg`, `singapore.svg`) rather than round numbers (`6.svg`, `18.svg`), as defined in `lib/circuitMap.ts`. While the circuit background feature was ultimately removed, this diagnostic validated the principle that file naming assumptions must be checked against the actual codebase.

**Calendar JSON correction** — Without this correction, `deriveSeasonStats()` would receive `undefined` when calling `.find()` on the top-level object (which has `season`, `last_updated`, `source`, and `races` properties — not array methods). This would cause a runtime TypeError on the server, crashing the page render.

**Field name correction** — Without this correction, the function would reference non-existent properties (`entry.[DATE_FIELD]`), producing `undefined` values for all season stats.

### 5.4 Diagnostic-First as a Methodology

The pre-implementation diagnostic is not a Phase 2 invention — it was first formalised in Phase 1 as an 8-dimension scope analysis. Phase 2 refined the methodology by running it through parallel exploration agents, which can cross-reference multiple files simultaneously. The key principle: **validate assumptions against the codebase before writing code, not after**. The cost of 60 seconds of exploration is trivially small compared to the debugging cost of 3 runtime failures.

---

## 6. Learnings and Decisions

### Learning 1: Diagnostic-First Development Prevents Compounding Errors

The 3 discrepancies were not independent — they compound. An incorrect SVG filename alone causes a missing background image (cosmetic). An incorrect calendar access pattern causes a server crash (functional). Together, they would produce a page that fails to render at all, with error messages pointing at a type error in `deriveSeasonStats()` rather than the root cause (wrong JSON access pattern). Diagnostic-first development breaks this compound failure chain by resolving each discrepancy before code is written.

### Learning 2: Server Component + Static JSON Is a Zero-Cost Data Strategy

The Home page achieves its data requirements with zero runtime cost:

- No API latency (data is compiled into the page)
- No client-side JavaScript for data fetching (no React Query hooks)
- No loading states for content (data is available at render time)
- No cache invalidation logic (calendar data is immutable for the season)

This is only possible because the Home page's data is genuinely static — the race calendar does not change during a session. Analytical pages correctly use React Query with API calls because their data (lap times, telemetry, pit stops) varies per session selection. The lesson is that the data strategy should match the data's volatility, not default to the most complex available pattern.

### Learning 3: Skeleton as Layout Contract

Phase 1's `HomePageSkeleton.tsx` was designed before Phase 2's content was implemented. The skeleton's three groups (hero, 2×2 card grid, capabilities list) exactly match the three sections in Phase 2's `HomeContent`. This was not coincidental — the skeleton was designed as a forward-looking layout contract.

The practical implication: when Phase 2 content replaces the skeleton via Suspense resolution, the layout shift is minimal because the content occupies the same grid structure, padding rhythm, and vertical spacing. This pattern — skeleton dimensions anticipating content dimensions — should be applied to any future page with a Suspense boundary.

### Learning 4: Iterative Design Validation

The HeroSection originally used a three-layer approach (decorative circuit SVGs → gradient → content). After implementation and visual evaluation, the circuit layer was removed because CSS containment (`overflow-hidden`) caused clipping artefacts and the SVGs overlapped adjacent page components.

This validated an important principle: **implement, evaluate visually, then decide** — not all design ideas survive contact with the actual rendered page. The two-layer result (gradient + content) is simpler and produces a cleaner visual outcome. The willingness to remove a feature after discovering it degrades the overall design is itself a design skill.

### Learning 5: Font Weight Mapping Through next/font/google

The Montserrat font is loaded in `layout.tsx` with explicit weights: `['500', '600', '700', '800']`. Tailwind's `font-extrabold` maps to weight 800, which is the heaviest available weight. This mapping is not obvious — Tailwind's weight scale (`thin` through `black`) maps to CSS weights 100–900, but only weights explicitly loaded by `next/font/google` are available. If weight 800 were not loaded, `font-extrabold` would silently fall back to the nearest available weight (700), producing a visually incorrect headline.

Understanding this mapping chain — Tailwind class → CSS weight → loaded font weight — prevents subtle typography bugs.

### Learning 6: Reuse Eliminates Configuration Risk

Phase 2 touches zero configuration files. No changes to `globals.css`, `tailwind.config.js`, or `next.config.js`. Every visual treatment reuses tokens already defined and validated across the Qualifying, Race, Practice, and Track Intelligence pages. This eliminates an entire category of risk: Tailwind purge issues, CSS specificity conflicts, and configuration syntax errors.

The locked-file constraint (7 configuration/infrastructure files locked in Phase 2) enforced this discipline. The result validates the constraint — Phase 2's visual quality matches the existing pages without introducing any new design tokens.

### Learning 7: Edge Case Handling via Natural Conditions

The "Season Complete" edge case in `SeasonStats.tsx` was verified naturally during Docker validation. Since the calendar contains 2025 dates and the implementation date is March 2026, `deriveSeasonStats()` correctly found no future races and returned `"Season Complete"` with the label `"Status"`. This natural verification is more valuable than synthetic test data because it exercises the exact production code path — server-side date comparison, null round handling, and conditional label rendering — under real conditions.

---

## 7. Testing, Verification, and Validation

### 7.1 Verification Workflow

Phase 2 follows the same Docker-first verification workflow established in Phase 1. Five stages, executed in sequence:

| Stage | Purpose | Duration |
|-------|---------|----------|
| 1. Pre-Flight | Static checks before Docker build | ~10s |
| 2. Docker Build | `docker-compose build --no-cache` — all 3 services | ~3 min |
| 3. Container Health | `docker-compose up -d` + `docker-compose ps` | ~15s |
| 4. Implementation Validation | curl-based SSR content checks + regression | ~10s |
| 5. Teardown | `docker-compose down` | ~5s |

### 7.2 Pre-Flight Static Checks

| Check | Command | Result |
|-------|---------|--------|
| TypeScript compilation | `npx tsc --noEmit` | Zero errors |
| No stale placeholder | `grep "Home page content" HomeContent.tsx` | No output (clean) |
| SeasonStats exported | `grep "export interface SeasonStats" page.tsx` | 1 match (line 22) |
| Component files exist | `ls components/home/` | All 4 files present |

### 7.3 Docker Build

All 3 Docker images built successfully with `--no-cache`:

- `apexview-api` — Built (Python/FastAPI)
- `apexview-ml` — Built (Python/ML service)
- `apexview-web` — Built (Next.js, includes Phase 2 changes)

### 7.4 Container Health

| Container | Status | Port |
|-----------|--------|------|
| f1-api | Healthy | 8000 |
| f1-ml | Healthy | 8501 |
| f1-web | Serving | 3000 |

### 7.5 Implementation Validation Results

| Check | Method | Result |
|-------|--------|--------|
| Hero headline "ApexView" | `curl \| grep "ApexView"` | Present in SSR HTML |
| Purpose line | `curl \| grep "Where Formula 1 Data Becomes Insight"` | Present |
| Season stat (2025) | `curl \| grep "2025"` | Present |
| Rounds label | `curl \| grep "Rounds"` | Present |
| Season Complete edge case | `curl \| grep "Season Complete"` | Present (all 2025 races past) |
| Status label | `curl \| grep "Status"` | Present (replaces "Next Race") |
| CTA text | `curl \| grep "Explore Race Data"` | Present |
| Feature card hrefs | `curl \| grep href="/qualifying"` etc. | All 4 hrefs present |
| Capabilities header | `curl \| grep "What You Can Explore"` | Present |
| No placeholder | `curl \| grep "Home page content"` | No output (clean) |
| No Plotly on Home | `curl \| grep "plotly"` | No output (clean) |
| Favicon accessible | `curl -w "%{http_code}" /icon.svg` | 200 |

### 7.6 Regression Checks

All existing pages continue to serve correctly:

| Page | URL | Status |
|------|-----|--------|
| Qualifying | `http://localhost:3000/qualifying` | 200 |
| Race | `http://localhost:3000/race` | 200 |
| Practice | `http://localhost:3000/practice` | 200 |
| Track Intelligence | `http://localhost:3000/track` | 200 |

### 7.7 Phase 2 Completion Gate

All 15 items passing:

| # | Item | Status |
|---|------|--------|
| 1 | Hero headline "ApexView" in Montserrat weight-800 | Pass |
| 2 | Purpose line in f1red below headline | Pass |
| 3 | Season stat displays 2025 | Pass |
| 4 | Rounds stat displays 24 | Pass |
| 5 | Next race stat displays valid value from calendar | Pass ("Season Complete") |
| 6 | CTA "Explore Race Data →" links to `/race` | Pass |
| 7 | Feature cards — all 4 with correct questions and hrefs | Pass |
| 8 | Card hover state — red border glow and arrow | Pass |
| 9 | Capability pills — 3 per card, `font-mono` styled | Pass |
| 10 | Capabilities section — all 8 items with red-border header | Pass |
| 11 | TypeScript — zero compilation errors | Pass |
| 12 | Docker build — clean exit, all 3 services healthy | Pass |
| 13 | SSR content — hero, cards, capabilities in curl output | Pass |
| 14 | No Plotly on Home — chunk absent from network | Pass |
| 15 | Existing pages — all 4 return 200 | Pass |

---

## 8. Alignment with Broader Home Page Plan

### What Phase 2 Established

Phase 2 completes the Home page's functional requirements:

1. **Visual identity** — The hero section with "ApexView" headline, purpose statement, and gradient backdrop establishes the platform's brand within the F1 analytical aesthetic.
2. **Navigation** — Four feature cards provide navigational entry points to every analytical page, with questions that communicate what each page answers.
3. **Scope communication** — Eight capability statements give visitors (and project assessors) a comprehensive understanding of the platform's analytical depth.
4. **Season context** — Server-derived statistics (season, rounds, next race) demonstrate data-driven content without introducing API complexity.
5. **Design system consistency** — Every visual treatment reuses existing tokens, proving the design system's extensibility.

### The Phased Approach Validated

The three-phase approach (Structure → Content → Polish) proved effective for several reasons:

- **Phase 1's skeleton accurately anticipated Phase 2's dimensions.** The 2×2 grid, the hero padding, the capabilities list — all matched. This validates the "skeleton as layout contract" principle.
- **Phase 1's locked files prevented scope creep.** Seven files were locked during Phase 2, forcing all content changes into the 7 target files. No configuration changes, no global style additions, no navigation modifications.
- **Phase 2's content validated Phase 1's architecture.** The Server Component → Suspense → Client Component pattern handles the Home page's data needs (static JSON derivation) as cleanly as it handles the analytical pages' data needs (React Query hooks). The architecture is general-purpose.

### Phase 3 — Polish and Performance (Complete)

Phase 3 delivered:

- **CSS entrance animations:** 400ms fadeSlideIn keyframe with 150ms section stagger (hero → cards → capabilities). `prefers-reduced-motion: reduce` hard override removes all animation unconditionally.
- **Accessibility remediation:** Heading hierarchy fix (sr-only h2 "Analytical Pages" + PlatformCapabilities h2→h3), focus-ring on HeroSection CTA and FeatureCard links, dynamic aria-label on RaceWeekendSelector for WCAG label-in-name compliance.
- **Application-wide metadata:** All 5 pages + root layout corrected to `Page Name | ApexView` pattern with OpenGraph. "F1 Engineering" brand removed from all metadata. Race and Qualifying pages received metadata exports where none existed.
- **Lighthouse final:** Performance 97, Accessibility 100, Best Practices 100, SEO 100 (Mobile preset). Desktop preset: 100/100/100/100.

Phase 2's component boundaries (each section is a separate component with clear props) made Phase 3 modifications surgical — each component was refined independently without affecting others.

---

*Documentation Version 1.2 — March 2026 (v1.1: Removed circuit background feature after visual evaluation — see Sections 2.5 and 6, Learning 4. v1.2: Updated Phase 3 status from Planned to Complete with final deliverables.)*
