import os
import shutil
from pathlib import Path

from theia_parse.const import DUPLICATE_SUFFIX, PARSED_JSON_SUFFIX


def restore_duplicates(dir: Path) -> None:
    for root, _, file_names in os.walk(dir):
        for file_name in file_names:
            curr_path = Path(root) / file_name
            if "".join(curr_path.suffixes[-2:]) == DUPLICATE_SUFFIX:
                source_path = Path(curr_path.read_text())
                shutil.copy(
                    source_path.with_suffix(PARSED_JSON_SUFFIX),
                    curr_path.with_suffix(PARSED_JSON_SUFFIX),
                )
