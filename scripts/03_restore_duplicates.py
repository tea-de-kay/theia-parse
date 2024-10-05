from pathlib import Path

from theia_parse.util.duplicates import restore_duplicates


PATH = (Path(__file__).parent.parent / "data/sample").resolve()


def main():
    restore_duplicates(PATH)


if __name__ == "__main__":
    main()
