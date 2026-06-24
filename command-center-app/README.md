# Command-Centre App

Windows-first command-centre software workspace.

The v1 prototype may use Python, PySide6, and SQLite. The command-centre receives
telemetry from a command-centre XBee over a COM port, decodes compact binary
telemetry packets, stores records locally, and displays node status in table and
map views.

## Prototype

The first prototype decodes MECHPHY telemetry protocol v1 packets, decodes the
generic XBee API AP=2 golden vector, stores decoded node telemetry in SQLite,
and displays node status in a PySide6 table.

COM port live reading is intentionally a TODO/stub for now.

## Windows Setup

Use Python 3.11 or newer.

```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
python -m mechphy_command_center.main
```

Run tests with:

```powershell
python -m pytest -q
```
