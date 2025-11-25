# IELTS Answer Form

Interactive IELTS Listening/Reading answer form that lets you type candidate answers, paste the official key, auto-grade with ✓ / ✗ indicators, and estimate the IELTS band score.

**Two versions available:**
- **Tkinter version** (`ielts_form_tkinter.py`) - Works on Windows, Linux, and macOS (recommended)
- **GTK version** (`ielts_form_gtk.py`) - Linux only, requires GTK/PyGObject

## Requirements

**Tkinter version (recommended):**
- Python 3.10+ (tkinter is built-in)
- No additional dependencies needed

**GTK version (Linux only):**
- Ubuntu 22.04+ (GTK 3 already installed)
- Python 3.10+
- Python libs: `PyGObject`, `pycairo`

## Run locally

**Tkinter version:**
```bash
python3 ielts_form_tkinter.py
```

**GTK version:**
```bash
python3 -m pip install --user pygobject pycairo
python3 ielts_form_gtk.py
```

## Python packaging

We ship helper scripts under `packaging/` to produce Python-based distributable artifacts.

### Build a `.deb` (Ubuntu)

**GTK Version:**
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
5. Uninstall:
   ```bash
   sudo apt remove ielts-form
   ```

**Tkinter Version (Recommended - works on Windows, Linux, macOS):**
1. Install packaging tool:
   ```bash
   sudo apt install dpkg-dev
   ```
2. Run the builder (version defaults to `1.0.0`):
   ```bash
   ./packaging/deb/build_deb_tkinter.sh 1.0.0
   ```
3. Find the package in `packaging/deb/dist/ielts-form-tkinter_1.0.0_all.deb`.
4. Install on any Ubuntu machine:
   ```bash
   sudo apt install ./packaging/deb/dist/ielts-form-tkinter_1.0.0_all.deb
   ```
5. Uninstall:
   ```bash
   sudo apt remove ielts-form-tkinter
   ```

### Build a Windows `.exe`

**Note:** The Windows build uses `tkinter` instead of GTK to avoid complex dependencies. This means:
- ✅ No GTK/PyGObject installation needed
- ✅ Works on any Windows machine (no Python required)
- ✅ Single `.exe` file, no extra dependencies

**Building the .exe:**

1. Install Python 3.11+ and PyInstaller:
   ```powershell
   pip install pyinstaller
   ```
2. Run PowerShell script (from repo root):
   ```powershell
   pwsh -File packaging/windows/build_exe.ps1 -Version 1.0.0
   ```
3. Output lands in `packaging/windows/dist/IELTSForm-1.0.0.exe`.

**Installing/Using on Windows:**

The `.exe` file is self-contained and portable:
- **Install:** Simply double-click `IELTSForm-1.0.0.exe` to run (no installation needed)
- **Uninstall:** Delete the `.exe` file (no registry entries or system files are created)
- **Distribution:** Copy the `.exe` to any Windows machine and run it directly

> **Why tkinter?** GTK/PyGObject requires complex Unix-like tools and libraries on Windows (MSYS2, pkg-config, GTK runtime). tkinter is built into Python and works natively on Windows. See `WINDOWS_BUILD_EXPLANATION.md` for details.

## Repository layout

| Path | Description |
| --- | --- |
| `ielts_form_gtk.py` | GTK version (Linux only) |
| `ielts_form_tkinter.py` | Tkinter version (Windows, Linux, macOS) |
| `generate_icon.py` | Utility that re-draws `ielts_icon.png` |
| `packaging/deb/build_deb.sh` | Debian package builder for GTK version |
| `packaging/deb/build_deb_tkinter.sh` | Debian package builder for Tkinter version |
| `packaging/windows/build_exe.ps1` | PyInstaller wrapper for Windows `.exe` (Tkinter) |

## License

MIT (see `LICENSE` if/when added). Update as needed for your distribution.

