# SKILL ADAPTER: ADDY OSMANI (PERFORMANCE PATTERNS)

> Web performance optimization, bundle reduction, runtime efficiency, and Core Web Vitals.

## Overview
- **Trigger**: Performance bottlenecks, bundle size alerts, slow page loads, memory leaks, rendering jank, or latency optimization.
- **Pipeline Stage**: `Performance Profiling & Optimization`
- **Guiding Rule**: **Measure before AND after**. Never introduce speculative caches or premature optimizations without concrete baseline metrics.

## Performance Checklist
1. **Bundle & Import Hygiene**:
   - Verify tree-shaking; import specific symbols (`import { debounce } from 'lodash-es'`), avoid barrel imports that pull full libraries.
   - Code-split routes and heavy dialogs using dynamic imports (`React.lazy()`, `import()`).
2. **Rendering & DOM Optimization**:
   - Virtualize long lists (e.g. TanStack Virtual, react-window).
   - Minimize reflows; debounce resize and scroll listeners; use CSS `transform` and `opacity` for animations.
3. **Network & Asset Loading**:
   - Optimize images (WebP/AVIF, explicit `width`/`height` to avoid CLS).
   - Defer non-critical third-party scripts.
4. **Backend / Data Optimization**:
   - Eliminate N+1 query patterns using joins or dataloaders.
   - Add targeted indexes on queried foreign keys; avoid `SELECT *`.

## Verification Gate
- Measure baseline metric (e.g., bundle size `npm run build`, API response time, or Lighthouse score).
- Apply minimal targeted optimization.
- Re-measure and report delta: `Before: X ms / kB -> After: Y ms / kB (-Z%)`.
