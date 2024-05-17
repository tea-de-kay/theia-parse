import os
import shutil
from pathlib import Path

from theia_parse.const import DUPLICATE_SUFFIXES, PARSED_JSON_SUFFIXES
from theia_parse.util.files import has_suffixes, with_suffix
from theia_parse.util.log import LogFactory


_log = LogFactory.get_logger()


def restore_duplicates(dir: Path) -> int:
    total = 0
    for root, _, file_names in os.walk(dir):
        for file_name in file_names:
            curr_path = Path(root) / file_name
            if has_suffixes(curr_path, DUPLICATE_SUFFIXES):
                source_path = Path(curr_path.read_text())
                try:
                    shutil.copy(
                        with_suffix(source_path, PARSED_JSON_SUFFIXES),
                        with_suffix(curr_path, PARSED_JSON_SUFFIXES),
                    )
                except Exception:
                    _log.warning(
                        "Could not restore duplicates "
                        "[source_path='{0}', current_path='{1}']",
                        source_path,
                        curr_path,
                    )
                os.remove(curr_path)
                total += 1

    return total
