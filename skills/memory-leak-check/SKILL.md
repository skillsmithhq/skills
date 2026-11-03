---
name: memory-leak-check
description: "Check whether a service, worker or browser app's memory grows without bound, find what is holding the memory using the runtime's own heap tools, and confirm the fix with a before-and-after soak. Use when memory climbs until a restart or out-of-memory kill, or when reviewing caches, listeners, timers or long-lived collections."
---

# memory-leak-check

## Instructions

1. Detect the runtime and its tools: for example heap snapshots in Node.js or browser DevTools, `tracemalloc` in Python, heap dumps and a profiler on the JVM, pprof in Go, or allocation tools for .NET. Use what the project already has.
2. Confirm there is a leak. Look at memory over time (container metrics or a soak run with steady load). Steady growth that garbage collection does not reclaim, across many cycles, suggests a leak. A sawtooth pattern that returns to a stable floor does not.
3. Take two or more heap snapshots under the same load some time apart, and compare them for the object types and retainers that keep growing.
4. Check the usual causes: unbounded caches or maps without eviction, event listeners or subscriptions not removed, timers or intervals not cleared, closures holding large objects, global or module-level collections, connection or stream objects not closed, and in browser apps, components that do not clean up on unmount.
5. Fix the retainer, then run the same soak again and compare the memory curve.

## Inputs

- `target`: service, worker, page or component.
- `symptom` (optional): for example "restarts every 6 hours with OOMKilled".

## Outputs

The memory curve before and after (environment, load, duration), the growing object types and their retention path, the root cause in code, and the fix.

## Constraints

- Heap snapshots can contain personal data and secrets. Take them in non-production environments where possible, store them securely, and delete them afterwards.
- Taking a heap dump can pause a process; ask before doing it in production.
- Raising the memory limit or adding scheduled restarts hides a leak; it is not a fix.

## Examples

### Example 1

Input: "the API pod is OOMKilled every few hours"

Output: Soak at constant load on staging: heap grows about 40 MB per hour with no plateau. Snapshot comparison: a module-level map of per-request contexts keyed by request ID is never cleared. Replace it with request-scoped context; a 6-hour soak afterwards stays flat at 180 MB.
