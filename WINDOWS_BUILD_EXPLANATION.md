# Why Windows Build is Difficult and How to Fix It

## The Problem

### Why `.deb` Works on Ubuntu
The `.deb` package works seamlessly on Ubuntu because:
1. **GTK is native to Linux**: GTK 3 is part of the standard Ubuntu desktop environment
2. **Dependencies are in repositories**: The `.deb` file declares dependencies (`python3-gi`, `gir1.2-gtk-3.0`) which are standard Ubuntu packages
3. **Automatic installation**: When you install the `.deb`, `apt` automatically installs all required dependencies from Ubuntu's repositories
4. **No compilation needed**: Everything is pre-built and ready to use

### Why `.exe` Fails on Windows
Windows has fundamental issues with GTK/PyGObject:

1. **GTK is NOT Windows-native**: GTK is a Linux/Unix GUI toolkit. It doesn't come with Windows.

2. **PyGObject requires complex dependencies**:
   - GObject Introspection (`girepository-2.0`)
   - `pkg-config` (a Unix build tool)
   - C libraries: GLib, Cairo, Pango, ATK, GDK, GTK
   - Hundreds of DLL files

3. **No official Windows wheels**: PyGObject doesn't provide pre-built Windows wheels on PyPI. You must:
   - Install MSYS2 (a Unix-like environment for Windows)
   - Compile from source
   - Install all GTK runtime libraries manually

4. **Even if you bundle it**: You'd need to package 100+ DLL files, making the installer huge (100+ MB)

## The Solution: Use tkinter Instead

I've created `ielts_form_tkinter.py` which:
- ✅ Uses **tkinter** (built into Python - no extra dependencies!)
- ✅ Works on Windows, Linux, and macOS
- ✅ Can be packaged as a single `.exe` file with PyInstaller
- ✅ No GTK runtime needed
- ✅ Much smaller installer size

## How to Build Windows `.exe` Now

### Step 1: Install PyInstaller
```powershell
pip install pyinstaller
```

### Step 2: Build the `.exe`
```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\windows\build_exe.ps1 -Version 1.0.0
```

The script now uses `ielts_form_tkinter.py` instead of `ielts_form_gtk.py`, so it will work without any GTK dependencies!

### Step 3: Test the `.exe`
The output will be in `packaging/windows/dist/IELTSForm-1.0.0.exe`. This single file:
- Contains everything needed (Python runtime + your code)
- No installation of extra packages required
- Just double-click to run!

## Comparison

| Feature | GTK Version | tkinter Version |
|---------|------------|-----------------|
| Windows support | ❌ Requires MSYS2/GTK runtime | ✅ Native (built into Python) |
| Linux support | ✅ Native | ✅ Native |
| macOS support | ⚠️ Possible but complex | ✅ Native |
| Installer size | 100+ MB (if bundled) | ~10-20 MB |
| Dependencies | Many (GTK, PyGObject, etc.) | None (tkinter is built-in) |
| Build complexity | Very high | Low |

## Why This Happens

**GTK** was designed for Unix-like systems (Linux, BSD, etc.). While it *can* run on Windows, it requires:
- A Unix-like environment (MSYS2, Cygwin)
- All the underlying C libraries
- Complex build tools

**tkinter**, on the other hand:
- Is part of Python's standard library
- Uses native OS widgets (Windows uses Windows widgets, Linux uses X11, macOS uses Cocoa)
- Works out of the box on all platforms

## Recommendation

**Use the tkinter version for Windows builds**. Keep the GTK version for Linux `.deb` packages since GTK is native there.

The application functionality is identical - only the UI toolkit changed from GTK to tkinter.

