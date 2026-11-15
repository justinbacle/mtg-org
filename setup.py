from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).parent


def readRequirements() -> list[str]:
    requirementsFile = ROOT / "requirements.txt"
    return [
        line.strip()
        for line in requirementsFile.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


setup(
    name="mtgorg",
    version="0.1",
    description="MTG card organizer with deck building, import/export, and offline bulk data",
    long_description=(ROOT / "readme.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/justinbacle/mtg-org",
    packages=find_packages(include=["mtgorg", "mtgorg.*"]),
    python_requires=">=3.10",
    install_requires=readRequirements(),
)
