import platform

block_cipher = None

if platform.system() == "Linux":
    if platform.freedesktop_os_release()["ID"] == "ubuntu":
        other_libs = [
            ("libGL.so", "/usr/lib/x86_64-linux-gnu/libGL.so", 'BINARY')
        ]
    else:
        other_libs = []
else:
    other_libs = []


a = Analysis(
    ['mtgorg_app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(
    a.pure, a.zipped_data, cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    other_libs,
    exclude_binaries=True,
    name='MTG Organizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MTG Organizer'
)

app = BUNDLE(
    exe,
    name='MTG Organizer'
)
