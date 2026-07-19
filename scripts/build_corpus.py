from pathlib import Path

from enembert.data.corpus import build

if __name__ == "__main__":
    print(build(Path("data")))
