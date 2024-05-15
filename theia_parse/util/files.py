import os
from hashlib import md5
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


def get_md5_sum(path: Path):
    with open(path, "rb") as f:
        chunk_size = 4096
        md5_hash = md5()
        while chunk := f.read(chunk_size):
            md5_hash.update(chunk)

    return md5_hash.hexdigest()
