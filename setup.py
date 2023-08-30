import os

paths = [
]

if __name__ == "__main__":

    for path in paths:
        if not os.path.exists(path.as_posix()):
            os.makedirs(path)
