#!/usr/bin/env python3
"""
Local binary build script for development and testing.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout

def main():
    """Build the standalone binary locally."""
    print("Building md2pdf-server standalone binary...")
    
    # Ensure we're in the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Install build dependencies
    print("Installing build dependencies...")
    run_command([sys.executable, "-m", "pip", "install", "-e", ".[build]"])
    run_command([sys.executable, "-m", "pip", "install", "pyinstaller[encryption]"])
    
    # Create PyInstaller spec file
    print("Creating PyInstaller spec file...")
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Get site-packages path
site_packages = None
for path in sys.path:
    if 'site-packages' in path:
        site_packages = Path(path)
        break

if site_packages is None:
    raise RuntimeError("Could not find site-packages directory")

# Find weasyprint data
weasyprint_data = []
weasyprint_path = site_packages / "weasyprint"
if weasyprint_path.exists():
    weasyprint_data.append((str(weasyprint_path / "css"), "weasyprint/css"))
    weasyprint_data.append((str(weasyprint_path / "html"), "weasyprint/html"))

# Find markdown-pdf data
markdown_pdf_data = []
markdown_pdf_path = site_packages / "markdown_pdf"
if markdown_pdf_path.exists():
    for item in markdown_pdf_path.rglob("*"):
        if item.is_file() and not item.name.endswith('.pyc'):
            rel_path = item.relative_to(site_packages)
            markdown_pdf_data.append((str(item), str(rel_path.parent)))

a = Analysis(
    ['grimd2pdf/standalone_server.py'],
    pathex=[],
    binaries=[],
    datas=weasyprint_data + markdown_pdf_data,
    hiddenimports=[
        'weasyprint',
        'cairo',
        'cairocffi', 
        'cairosvg',
        'cssselect2',
        'html5lib',
        'tinycss2',
        'pyphen',
        'markdown_pdf',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'click',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='md2pdf-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('md2pdf-server.spec', 'w') as f:
        f.write(spec_content)
    
    # Build with PyInstaller
    print("Building binary with PyInstaller...")
    run_command([sys.executable, "-m", "PyInstaller", "md2pdf-server.spec", "--clean", "--noconfirm"])
    
    # Test the binary
    print("Testing the binary...")
    binary_path = Path("dist/md2pdf-server")
    if binary_path.exists():
        # Make executable
        os.chmod(binary_path, 0o755)
        
        # Test help command
        result = subprocess.run([str(binary_path), "--help"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Binary built successfully!")
            print(f"📍 Location: {binary_path.absolute()}")
            print(f"📏 Size: {binary_path.stat().st_size / (1024*1024):.1f} MB")
            print("\nUsage examples:")
            print(f"  # MCP mode: {binary_path}")
            print(f"  # HTTP mode: {binary_path} --http --port 8000")
        else:
            print(f"❌ Binary test failed: {result.stderr}")
            sys.exit(1)
    else:
        print("❌ Binary not found after build")
        sys.exit(1)

if __name__ == "__main__":
    main()