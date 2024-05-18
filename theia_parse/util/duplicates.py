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
                source_path = Path(curr_path.read_text())
                source_path = with_suffix(source_path, PARSED_JSON_SUFFIXES)
                dest_path = with_suffix(source_path, PARSED_JSON_SUFFIXES)
                try:
                    shutil.copy(source_path, dest_path)
                    parsed = ParsedDocument(**read_json(dest_path))
                    # TODO: dest path hast json suffix, but should be original suffix
                    parsed.path = str(dest_path)
                    write_json(dest_path, parsed)
                except Exception:
                    _log.warning(
                        "Could not restore duplicates "
                        "[source_path='{0}', current_path='{1}']",
                        source_path,
                        dest_path,
                    )
                os.remove(curr_path)
                counter += 1

    return counter
