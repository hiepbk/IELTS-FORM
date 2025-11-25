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

## Desktop launcher (manual)

Ubuntu already ships everything necessary. Run:

```bash
chmod +x install_desktop_entry.sh
./install_desktop_entry.sh
```

This creates a launcher entry (under “IELTS Answer Form”) that reuses system Python.

## Packaging

We ship helper scripts under `packaging/` to produce distributable artifacts.

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

1. Install GTK/PyGObject runtime (MSYS2 recommended) and Python 3.11+.
2. Install dependencies:
   ```powershell
   pip install pyinstaller pygobject pycairo
   ```
3. Run PowerShell script (from repo root):
   ```powershell
   pwsh -File packaging/windows/build_exe.ps1 -Version 1.0.0
   ```
4. Output lands in `packaging/windows/dist/IELTSForm.exe`.

> **Note:** The Windows build embeds the GTK runtime files collected by PyInstaller. Make sure you run the script from an MSYS2/GTK-enabled environment (MSYS2 shell or Git Bash with `pacman -S mingw-w64-x86_64-gtk3`).

## Repository layout

| Path | Description |
| --- | --- |
| `ielts_form_gtk.py` | Main GTK UI |
| `generate_icon.py` | Utility that re-draws `ielts_icon.png` |
| `install_desktop_entry.sh` | Launcher installer for dev use |
| `packaging/deb/build_deb.sh` | Debian package builder |
| `packaging/windows/build_exe.ps1` | PyInstaller wrapper for `.exe` |

## License

MIT (see `LICENSE` if/when added). Update as needed for your distribution.

