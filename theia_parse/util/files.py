import json
from hashlib import md5
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from theia_parse.const import SUPPORTED_EXTENSIONS


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


def has_suffixes(path: Path, suffixes: list[str] | str) -> bool:
    suffixes = [suffixes] if isinstance(suffixes, str) else suffixes
    n_suffixes = len(suffixes)
    return path.suffixes[-n_suffixes:] == suffixes


def with_suffix(
    path: Path,
    suffixes: list[str] | str,
    replace_suffixes: list[str] | str | None = None,
) -> Path:
    suffix = suffixes if isinstance(suffixes, str) else "".join(suffixes)
    if replace_suffixes is not None:
        path_string = str(path)
        replace_suffixes = (
            replace_suffixes
            if isinstance(replace_suffixes, str)
            else "".join(replace_suffixes)
        )
        path_string = path_string.removesuffix(replace_suffixes)
        path = Path(path_string)
    return path.with_suffix(suffix)


def write_json(path: Path | str, data: dict[str, Any] | BaseModel) -> None:
    data = data.model_dump(mode="json") if isinstance(data, BaseModel) else data
    with open(path, "wt") as outfile:
        json.dump(data, outfile)


def read_json(path: Path | str) -> dict[str, Any]:
    with open(path) as infile:
        data = json.load(infile)

    return data
