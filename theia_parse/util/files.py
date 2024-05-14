import os
from pathlib import Path


def get_total_number_of_files(dir: Path) -> int:
    counter = 0
    for _, _, file_names in os.walk(dir):
        counter += len(file_names)

    return counter
