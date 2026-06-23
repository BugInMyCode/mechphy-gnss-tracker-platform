# AGENTS.md

Instructions for future Codex agents working on the MECHPHY GNSS tracker platform.

## Project

MECHPHY is an autonomous GNSS tracker network deployment platform for real-world
field deployments in India.

## Hardware And Product Direction

- Ground nodes use STM32L433 microcontrollers.
- Radios are Digi XBee-PRO 900HP / XBP9B family.
- DigiMesh is the primary network mode.
- Point-to-multipoint mode is only a fallback or test mode.
- Product firmware must use XBee API Escaped Mode, `AP=2`.
- The command-centre app is Windows-first.
- Python + PySide6 is acceptable for the first prototype.
- SQLite is the v1 local storage choice.

## Monorepo Layout

Use this top-level layout:

```text
/docs
/firmware
/command-center-app
/rf-engine
/gis-engine
/telemetry-protocol
/hardware-profiles
/test-data
```

## Critical Engineering Rules

- Do not implement mesh routing in STM32 firmware. XBee handles routing.
- Do not use JSON or text packets over RF for v1 telemetry.
- Use compact binary packets for v1 RF telemetry.
- Firmware C code must avoid `malloc`.
- Use fixed-size buffers.
- Keep code unit-testable on desktop where possible.
- Keep v1 simple and field-testable.
- Do not invent antenna gain, radiation pattern, cable loss, EIRP, or India
  regulatory values.
- Mark India RF regulatory status as blocked until verified.
- Mark A09-F8NF-M, S463AH-915, and cable loss values as blocked until datasheets
  are verified.
- Every task must report files changed, tests run, and unresolved questions.

## Milestone M1

Target end-to-end path:

```text
STM32L433 -> XBee API escaped frame -> DigiMesh -> command-centre XBee
-> COM port -> app decodes -> SQLite stores -> table/map displays node
```

## Acceptance Criteria For Future Tasks

- Preserve these project rules unless the user explicitly changes them.
- Keep changes scoped to the requested task.
- Report files changed, tests run, and unresolved questions.
