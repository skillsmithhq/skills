---
name: web-performance-check
description: "Check a web page or front-end change for performance problems that users feel: Core Web Vitals (LCP, INP, CLS), JavaScript bundle size, images, fonts, render-blocking resources and caching, measured before and after rather than guessed. Use when reviewing a front-end change, a slow page, a new dependency, or before a launch."
---

# web-performance-check

## Instructions

1. Detect the stack first: framework, bundler, how the app is served, and any performance tooling already in the repo (Lighthouse CI, bundle analyser, size-limit, web-vitals reporting, RUM). Use those before adding anything new, and ask before installing a tool.
2. Measure a baseline on the pages the change affects, in a production build, not the dev server. Use lab data (for example Lighthouse with mobile throttling) and, if the project collects them, field data (real-user Core Web Vitals at the 75th percentile). Say which kind each number is.
3. Check against the Core Web Vitals "good" thresholds at the 75th percentile: LCP 2.5 s or less, INP 200 ms or less, CLS 0.1 or less. INP replaced FID in March 2024; do not report FID.
4. Look for the usual causes:
   - JavaScript: bundle size and what grew (new dependency, whole-library imports, missing code splitting, duplicate packages), long tasks on the main thread, hydration cost.
   - LCP element: is it discoverable early, preloaded if needed, not lazy-loaded, served at the right size and format.
   - Images and media: dimensions set (CLS), modern formats, responsive sizes, lazy loading below the fold only.
   - Fonts: preloading or `font-display` choice, layout shift on swap, number of weights.
   - Render-blocking CSS and scripts, third-party scripts, and request waterfalls.
   - Caching: hashed static assets with long cache lifetimes, compression enabled.
5. For each fix, measure again with the same method and report the change.

## Inputs

- `target`: page URL or route, component, or the diff to check.
- `budget` (optional): the project's performance budget; if none exists, propose one.

## Outputs

A table of metrics before and after (lab or field, device profile, run count), then findings ordered by user impact, each with the cause, the evidence and the fix.

## Constraints

- Lab scores vary between runs; take the median of at least three runs and do not report a single run as a result.
- A good Lighthouse score does not prove good field performance. Say when field data is unavailable.
- Only test sites and environments the user owns or is allowed to test.

## Examples

### Example 1

Input: "the product page got slower after adding a charts library"

Output: Production build, Lighthouse mobile, median of 5 runs: LCP 3.9 s (was 2.3 s), main-thread blocking up 420 ms. The charts library is imported in the page entry, adding 180 KB gzipped to first load. Lazy-load the chart component below the fold: LCP back to 2.4 s in the same test.
