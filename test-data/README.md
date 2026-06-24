# Test Data

Test data workspace for sample captures, simulated telemetry, field logs,
protocol fixtures, and validation inputs.

Keep test data clearly labeled as simulated, lab-captured, or field-captured.
Do not treat sample RF or regulatory values as authoritative unless their source
is documented.

## Golden Vectors

- `telemetry_gnss_v1_golden.json` contains the shared 40-byte simulated GNSS
  telemetry packet for firmware and command-centre decoder tests.
- `xbee_api_escaped_golden.json` contains a generic XBee API AP=2 escaped-frame
  vector carrying the same telemetry packet inside test-only frame data.
- `tools/generate_golden_vectors.py` regenerates the JSON files and supports
  `--check` for reproducibility.

The XBee vector is not a product-ready transmit request. XBee-PRO 900HP / XBP9B
transmit request, transmit status, and receive packet frame type IDs remain
`TODO_VERIFY` until checked against the Digi product manual.
