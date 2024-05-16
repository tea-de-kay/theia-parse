from hashlib import md5
from pathlib import Path

from theia_parse import SUPPORTED_EXTENSIONS


def get_md5_sum(path: Path):
    with open(path, "rb") as f:
        chunk_size = 4096
        md5_hash = md5()
        while chunk := f.read(chunk_size):
            md5_hash.update(chunk)

    return md5_hash.hexdigest()


def is_file_supported(
    path: Path | str,
    extensions: list[str] = SUPPORTED_EXTENSIONS,
) -> bool:
    if isinstance(path, Path):
        return path.suffix.strip(".").lower() in extensions
    else:
        return any(path.lower().endswith(ext) for ext in extensions)
