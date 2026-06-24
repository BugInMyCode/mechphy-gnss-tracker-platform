# MECHPHY Telemetry Protocol v1

This document defines the MECHPHY v1 compact binary RF telemetry packet for
STM32L433 ground nodes using Digi XBee-PRO 900HP / XBP9B radios.

The telemetry payload is binary. Do not send JSON or text packets over RF for v1
telemetry.

XBee API Escaped Mode, `AP=2`, is part of the XBee serial/API framing layer. The
packet below is the RF payload carried inside the XBee frame.

## Packet Rules

- Fixed packet size for v1 GNSS telemetry: 40 bytes.
- No dynamic-length fields.
- No padding or alignment bytes.
- All multi-byte integer fields are little-endian.
- Signed integer fields use two's-complement representation.
- Firmware and app code should pack and unpack fields explicitly, not by relying
  on compiler-specific struct layout.

## Exact Byte Layout

| Offset | Size | Field | Type | Description |
|---:|---:|---|---|---|
| 0 | 2 | `magic` | `uint16` | Fixed value `0x504D`, transmitted as bytes `4D 50` (`MP`). |
| 2 | 1 | `protocol_version` | `uint8` | Fixed value `1` for this specification. |
| 3 | 1 | `message_type` | `uint8` | Message type registry value. See below. |
| 4 | 4 | `node_id` | `uint32` | Unique node identifier assigned by MECHPHY tooling. |
| 8 | 4 | `sequence_number` | `uint32` | Monotonic packet counter per node; wraps at `0xFFFFFFFF`. |
| 12 | 4 | `utc_time` | `uint32` | Unix time in whole UTC seconds. Use `0` if unknown. |
| 16 | 4 | `latitude_e7` | `int32` | Latitude in degrees multiplied by 10,000,000. |
| 20 | 4 | `longitude_e7` | `int32` | Longitude in degrees multiplied by 10,000,000. |
| 24 | 4 | `altitude_cm` | `int32` | GNSS altitude in centimeters. |
| 28 | 1 | `fix_type` | `uint8` | GNSS fix type. See fix type values. |
| 29 | 1 | `satellite_count` | `uint8` | Satellites used or reported for the fix. |
| 30 | 2 | `hdop_x10` | `uint16` | HDOP multiplied by 10. Use `0xFFFF` if unknown. |
| 32 | 2 | `battery_mv` | `uint16` | Battery voltage in millivolts. Use `0xFFFF` if unknown. |
| 34 | 2 | `temperature_c_x10` | `int16` | Temperature in degrees Celsius multiplied by 10. Use `-32768` if unknown. |
| 36 | 2 | `status_flags` | `uint16` | Bit flags. Reserved bits must be transmitted as `0`. |
| 38 | 2 | `crc16` | `uint16` | CRC-16/CCITT-FALSE over bytes 0 through 37, stored little-endian. |

Packet size calculation:

```text
2 + 1 + 1 + 4 + 4 + 4 + 4 + 4 + 4 + 1 + 1 + 2 + 2 + 2 + 2 + 2 = 40 bytes
```

Bytes covered by CRC: 38 bytes.

Total transmitted v1 GNSS telemetry payload: 40 bytes.

## Scaling Rules

| Field | Scaling |
|---|---|
| `latitude_e7` | `degrees * 10,000,000`, rounded to nearest integer. Example: `12.971599` degrees becomes `129715990`. |
| `longitude_e7` | `degrees * 10,000,000`, rounded to nearest integer. Example: `77.594566` degrees becomes `775945660`. |
| `altitude_cm` | Altitude in centimeters. Example: `920.00 m` becomes `92000`. |
| `hdop_x10` | `HDOP * 10`, rounded to nearest integer. Example: `0.9` becomes `9`. |
| `temperature_c_x10` | Degrees Celsius multiplied by 10. Example: `28.7 C` becomes `287`. |
| `battery_mv` | Battery voltage in millivolts. Example: `3.710 V` becomes `3710`. |

If GNSS fix data is unavailable, set `fix_type = 0`, clear status bit 0, and set
`latitude_e7`, `longitude_e7`, and `altitude_cm` to `0`. If time is unavailable,
set `utc_time = 0`.

## Message Type Values

| Value | Name | Direction | v1 Status |
|---:|---|---|---|
| `0x00` | Reserved invalid | Any | Do not transmit. |
| `0x01` | GNSS telemetry | Node to command centre | Defined by this 40-byte layout. |
| `0x02` | Node health | Node to command centre | Allocated; payload semantics reserved for a later fixed-size spec. |
| `0x03` | Relay health | Relay to command centre | Allocated; payload semantics reserved for a later fixed-size spec. |
| `0x10` | Command | Command centre to node | Reserved for future downlink. |
| `0x11` | Command acknowledgement | Node to command centre | Reserved for future acknowledgement messages. |
| `0x12` to `0x7F` | Reserved | Any | Do not transmit until specified. |
| `0x80` to `0xFF` | Experimental or vendor-specific | Any | Do not use in product firmware without a written spec. |

M1 decoders must implement `0x01` GNSS telemetry. For any unsupported
`message_type`, a decoder may validate `magic`, `protocol_version`, packet
length, and CRC, then report the packet as unsupported without interpreting the
GNSS fields.

## Fix Type Values

| Value | Meaning |
|---:|---|
| `0` | No fix or invalid fix. |
| `2` | 2D GNSS fix. |
| `3` | 3D GNSS fix. |
| Other values | Reserved. Receivers should report but not reinterpret them. |

## Status Flags

`status_flags` is a 16-bit little-endian bitfield.

| Bit | Mask | Meaning |
|---:|---:|---|
| 0 | `0x0001` | GNSS fix valid. |
| 1 | `0x0002` | UTC time valid. |
| 2 | `0x0004` | Low battery warning. |
| 3 | `0x0008` | External power present. |
| 4 | `0x0010` | Telemetry queue overflow occurred since last report. |
| 5 | `0x0020` | Sensor fault. |
| 6-15 | `0xFFC0` | Reserved for future use. Transmit as `0`; receivers must ignore unknown reserved bits. |

## CRC16

Use CRC-16/CCITT-FALSE:

- Polynomial: `0x1021`.
- Initial value: `0xFFFF`.
- Reflected input: no.
- Reflected output: no.
- Final XOR: `0x0000`.
- Coverage: packet bytes at offsets 0 through 37 inclusive.
- Excluded from coverage: the `crc16` field at offsets 38 and 39.
- Storage: calculated 16-bit CRC stored little-endian at offsets 38 and 39.

Embedded-friendly algorithm:

```text
crc = 0xFFFF
for each covered byte in transmitted order:
    crc = crc XOR (byte << 8)
    repeat 8 times:
        if bit 15 of crc is set:
            crc = (crc << 1) XOR 0x1021
        else:
            crc = crc << 1
        crc = crc AND 0xFFFF
```

A lookup table may be used later for speed, but the bitwise algorithm above is
small, deterministic, and suitable for embedded C.

## Example GNSS Telemetry Packet

Dummy example values:

| Field | Value |
|---|---:|
| `magic` | `0x504D` |
| `protocol_version` | `1` |
| `message_type` | `0x01` |
| `node_id` | `0x00001234` |
| `sequence_number` | `42` |
| `utc_time` | `1782282600` (`2026-06-24T06:30:00Z`) |
| `latitude_e7` | `129715990` (`12.971599` degrees) |
| `longitude_e7` | `775945660` (`77.594566` degrees) |
| `altitude_cm` | `92000` (`920.00 m`) |
| `fix_type` | `3` |
| `satellite_count` | `12` |
| `hdop_x10` | `9` (`0.9`) |
| `battery_mv` | `3710` |
| `temperature_c_x10` | `287` (`28.7 C`) |
| `status_flags` | `0x0001` |
| `crc16` | `0x1890`, transmitted as `90 18` |

Complete 40-byte RF payload, shown as hexadecimal bytes:

```text
4D 50 01 01 34 12 00 00 2A 00 00 00 68 79 3B 6A
16 4F BB 07 BC FD 3F 2E 60 67 01 00 03 0C 09 00
7E 0E 1F 01 01 00 90 18
```

The CRC value `0x1890` is calculated over the first 38 bytes only:

```text
4D 50 01 01 34 12 00 00 2A 00 00 00 68 79 3B 6A
16 4F BB 07 BC FD 3F 2E 60 67 01 00 03 0C 09 00
7E 0E 1F 01 01 00
```

## Decoder Validation Order

Recommended v1 decoder checks:

1. Require exactly 40 payload bytes for `0x01` GNSS telemetry.
2. Verify `magic == 0x504D`.
3. Verify `protocol_version == 1`.
4. Verify `crc16` over bytes 0 through 37.
5. Dispatch by `message_type`.
6. Apply field range checks and scaling.

## Future Extension Strategy

- Do not change the meaning, offset, size, or byte order of any field in the v1
  GNSS telemetry packet.
- Keep `message_type = 0x01` fixed at 40 bytes.
- New fields for GNSS telemetry require either a new `protocol_version` or a new
  fixed-size message type.
- A v1 decoder must reject or ignore unsupported `protocol_version` values rather
  than guessing field layout.
- Reserved status flag bits must be transmitted as `0` by v1 firmware and ignored
  by v1 receivers.
- Node health, relay health, command, and acknowledgement packets must receive
  their own fixed-size layouts before product firmware uses them.
- Avoid dynamic-length fields in v1 telemetry. If a later version needs variable
  payloads, it must use a new protocol version and explicit length handling.

## Open Items

- The altitude datum/source should be fixed once the GNSS receiver integration is
  finalized.
- Node ID assignment policy should be defined by MECHPHY provisioning tooling.
