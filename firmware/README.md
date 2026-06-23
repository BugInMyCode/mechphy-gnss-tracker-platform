# Firmware

Firmware workspace for STM32L433 ground node software.

Important constraints:

- Do not implement mesh routing in firmware. XBee handles routing.
- Use XBee API Escaped Mode, `AP=2`, for product firmware.
- Avoid `malloc` in firmware C code.
- Use fixed-size buffers.
- Keep logic unit-testable on desktop where possible.

No firmware source code has been added yet.
