# MECHPHY GNSS Tracker Platform

MECHPHY is an autonomous GNSS tracker network deployment platform for real-world
field deployments in India. The repository is organized as a monorepo so
firmware, RF planning, telemetry protocol definitions, hardware profiles, field
test data, and command-centre software can evolve together.

## System Direction

- Ground nodes are based on STM32L433 microcontrollers.
- Radios are Digi XBee-PRO 900HP / XBP9B family modules.
- DigiMesh is the primary network mode.
- Point-to-multipoint mode is only a fallback or test mode.
- Product firmware uses XBee API Escaped Mode, `AP=2`.
- The command-centre software is Windows-first.
- The v1 command-centre prototype may use Python, PySide6, and SQLite.

## Repository Layout

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

## RF Planning And Telemetry Workflow

The platform is intended to support the full field workflow:

1. Define hardware profiles for supported STM32 and XBee node variants.
2. Plan RF deployments using verified radio, antenna, cable, and regulatory
   inputs only.
3. Encode node telemetry as compact binary packets for RF transport.
4. Send telemetry from STM32L433 ground nodes through XBee API escaped frames.
5. Route packets over DigiMesh using the XBee network stack.
6. Receive packets at the Windows command-centre XBee over a COM port.
7. Decode telemetry in the command-centre app.
8. Store decoded records in SQLite.
9. Display nodes in table and map views for field operators.

Do not implement mesh routing in STM32 firmware. The XBee modules handle mesh
routing.

Do not use JSON or text packets over RF for v1 telemetry. Use compact binary
packets.

## Milestone M1 Success Criterion

```text
STM32L433 -> XBee API escaped frame -> DigiMesh -> command-centre XBee
-> COM port -> app decodes -> SQLite stores -> table/map displays node
```

## Known Blockers

- India WPC/ETA and 902-928 MHz legality are not yet verified.
- Digi A09-F8NF-M antenna gain and radiation pattern are not yet verified.
- Nearson S463AH-915 antenna gain, radiation pattern, and ground-plane
  requirement are not yet verified.
- Cable and connector loss values are not yet verified.

Do not invent RF, antenna, cable loss, EIRP, or regulatory values. Treat these
items as blocked until verified from authoritative sources or datasheets.
