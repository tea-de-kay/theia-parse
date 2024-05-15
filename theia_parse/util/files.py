from hashlib import md5
from pathlib import Path


def get_md5_sum(path: Path):
    with open(path, "rb") as f:
        chunk_size = 4096
        md5_hash = md5()
        while chunk := f.read(chunk_size):
            md5_hash.update(chunk)

    return md5_hash.hexdigest()
