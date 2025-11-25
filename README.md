# IELTS Answer Form

Interactive IELTS Listening/Reading answer form built with Python 3 and GTK (PyGObject). It lets you type candidate answers, paste the official key, auto-grade with ✓ / ✗ indicators, and estimate the IELTS band score.

## Requirements

- Ubuntu 22.04+ (GTK 3 already installed) or Windows 10+ with GTK/PyGObject runtime
- Python 3.10+
- Python libs: `PyGObject`, `pycairo`

Run locally:

```bash
python3 -m pip install --user pygobject pycairo
python3 ielts_form_gtk.py
```

## Python packaging

We ship helper scripts under `packaging/` to produce Python-based distributable artifacts.

### Build a `.deb` (Ubuntu)

1. Install packaging tool:
   ```bash
   sudo apt install dpkg-dev
   ```
2. Run the builder (version defaults to `1.0.0`):
   ```bash
   ./packaging/deb/build_deb.sh 1.0.0
   ```
3. Find the package in `packaging/deb/dist/ielts-form_1.0.0_all.deb`.
4. Install on any Ubuntu machine:
   ```bash
   sudo apt install ./packaging/deb/dist/ielts-form_1.0.0_all.deb
   ```

### Build a Windows `.exe`

**Note:** The Windows build now uses `tkinter` instead of GTK to avoid complex dependencies. This means:
- ✅ No GTK/PyGObject installation needed
- ✅ Works on any Windows machine with Python
- ✅ Single `.exe` file, no extra dependencies

1. Install Python 3.11+ and PyInstaller:
   ```powershell
   pip install pyinstaller
   ```
2. Run PowerShell script (from repo root):
   ```powershell
   pwsh -File packaging/windows/build_exe.ps1 -Version 1.0.0
   ```
3. Output lands in `packaging/windows/dist/IELTSForm-1.0.0.exe`.

The `.exe` file is self-contained and can be distributed to any Windows machine without requiring Python or any other dependencies.

> **Why tkinter?** GTK/PyGObject requires complex Unix-like tools and libraries on Windows (MSYS2, pkg-config, GTK runtime). tkinter is built into Python and works natively on Windows. See `WINDOWS_BUILD_EXPLANATION.md` for details.

## Repository layout

| Path | Description |
| --- | --- |
| `ielts_form_gtk.py` | Main GTK UI |
| `generate_icon.py` | Utility that re-draws `ielts_icon.png` |
| `packaging/deb/build_deb.sh` | Debian package builder (Python/GTK app) |
| `packaging/windows/build_exe.ps1` | PyInstaller wrapper for `.exe` (Python/GTK app) |

## License

MIT (see `LICENSE` if/when added). Update as needed for your distribution.

