---
name: env-config-rebuild-check
description: "Check whether an environment/config change actually takes effect with a restart, or requires a rebuild because the value is baked into the image/bundle at build time."
---

# env-config-rebuild-check

## Instructions

Trace how the specific variable is consumed: a runtime read on each request needs only a restart; a value baked in during image build/bundling needs a rebuild, and a plain restart will silently keep serving the old value.

## Inputs

- `target`: the env var or config file that changed.

## Outputs

A statement of whether a restart is sufficient or a rebuild is required, with the reason.

## Constraints

- Don't assume a restart is enough without tracing how the value is actually read.

## Examples

### Example 1

Input: "I changed environments/.env but the app still uses the old value after restart."

Output: The `.env` file is baked into the Docker image at build time; a restart re-reads the old snapshot. Run `docker compose build app` (or the equivalent build step) before restarting.
