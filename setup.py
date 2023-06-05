import os
from pathlib import Path

paths = [
    Path("resources/icons/sets"),
    Path("resources/images/cards")
]

if __name__ == "__main__":

    for path in paths:
        if not os.path.exists(path.as_posix()):
            os.makedirs(path)
