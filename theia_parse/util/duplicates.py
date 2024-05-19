import os
import shutil
from pathlib import Path

from theia_parse.const import DUPLICATE_SUFFIXES, PARSED_JSON_SUFFIXES
from theia_parse.model import ParsedDocument
from theia_parse.util.files import has_suffixes, read_json, with_suffix, write_json
from theia_parse.util.log import LogFactory


_log = LogFactory.get_logger()


def restore_duplicates(dir: Path) -> int:
    counter = 0
    for root, _, file_names in os.walk(dir):
        for file_name in file_names:
            curr_path = Path(root) / file_name
            if has_suffixes(curr_path, DUPLICATE_SUFFIXES):
                original_source_path = Path(curr_path.read_text())
                source_path = with_suffix(
                    original_source_path,
                    PARSED_JSON_SUFFIXES,
                    keep_original_suffix=True,
                )
                dest_path = with_suffix(
                    curr_path,
                    PARSED_JSON_SUFFIXES,
                    DUPLICATE_SUFFIXES,
                )
                try:
                    shutil.copy(source_path, dest_path)
                    parsed = ParsedDocument(**read_json(dest_path))
                    parsed.path = str(
                        with_suffix(
                            dest_path,
                            "",
                            replace_suffixes=PARSED_JSON_SUFFIXES,
                        )
                    )
                    write_json(dest_path, parsed)
                    os.remove(curr_path)
                    counter += 1
                except Exception:
                    _log.warning(
                        "Could not restore duplicates "
                        "[source_path='{0}', dest_path='{1}']",
                        source_path,
                        dest_path,
                    )

    return counter
