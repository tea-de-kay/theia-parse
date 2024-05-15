import os
from pathlib import Path


def get_total_number_of_files(dir: Path, suffixes: list[str]) -> int:
    counter = 0
    for _, _, file_names in os.walk(dir):
        counter += len(
            [
                f
                for f in file_names
                if any(f.lower().endswith(suffix) for suffix in suffixes)
            ]
        )

    return counter
