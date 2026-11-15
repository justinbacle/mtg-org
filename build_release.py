"""Build a standalone MTG Organizer binary and package it for release."""

import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"


def arch() -> str:
    machine = platform.machine().lower()
    if machine in ("amd64", "x86_64"):
        return "x86_64"
    if machine in ("arm64", "aarch64"):
        return "arm64"
    return machine or "unknown"


def build() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "mtgorg/mtgorg_app.py",
            "--onefile",
            "--windowed",
            "--name",
            "mtgorg",
            "--distpath",
            str(DIST),
            "--workpath",
            str(BUILD),
            "--specpath",
            str(BUILD),
            "--paths",
            str(ROOT / "mtgorg"),
            "--add-data",
            f"{ROOT / 'resources'}{os.pathsep}resources",
            "--collect-data",
            "qt_material",
            "--noconfirm",
        ],
        cwd=ROOT,
        check=True,
    )


def package() -> Path:
    DIST.mkdir(parents=True, exist_ok=True)
    suffix = arch()
    if sys.platform == "win32":
        target = DIST / f"mtgorg-windows-{suffix}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(DIST / "mtgorg.exe", "mtgorg.exe")
        return target
    if sys.platform == "darwin":
        target = DIST / f"mtgorg-macos-{suffix}.zip"
        app = DIST / "mtgorg.app"
        base = app if app.exists() else DIST / "mtgorg"
        shutil.make_archive(str(target.with_suffix("")), "zip", root_dir=DIST, base_dir=base.name)
        return target
    target = DIST / f"mtgorg-linux-{suffix}.tar.gz"
    with tarfile.open(target, "w:gz") as archive:
        archive.add(DIST / "mtgorg", arcname="mtgorg")
    return target


if __name__ == "__main__":
    build()
    print(package())
