import os
import shutil
from pathlib import Path

from theia_parse.const import DUPLICATE_SUFFIXES, PARSED_JSON_SUFFIXES
from theia_parse.model import ParsedDocument
from theia_parse.util.files import has_suffixes, read_json, with_suffix, write_json
from theia_parse.util.log import LogFactory


_log = LogFactory.get_logger()


def restore_duplicate_parsed_doc(source_path: Path, dest_path: Path) -> bool:
    parsed_source_path = with_suffix(source_path, PARSED_JSON_SUFFIXES)
    parsed_dest_path = with_suffix(dest_path, PARSED_JSON_SUFFIXES)

    try:
        shutil.copy(parsed_source_path, parsed_dest_path)
        parsed = ParsedDocument(**read_json(parsed_dest_path))
        parsed.path = str(dest_path)
        write_json(parsed_dest_path, parsed)
    except Exception:
        _log.warning(
            "Could not restore duplicates " "[source_path='{0}', dest_path='{1}']",
            parsed_source_path,
            parsed_dest_path,
        )

    return True


def restore_duplicates(dir: Path) -> int:
    counter = 0
    for root, _, file_names in os.walk(dir):
        for file_name in file_names:
            curr_path = Path(root) / file_name
            if has_suffixes(curr_path, DUPLICATE_SUFFIXES):
                source_path = Path(curr_path.read_text())
                dest_path = with_suffix(curr_path, replace_suffixes=DUPLICATE_SUFFIXES)
                if restore_duplicate_parsed_doc(source_path, dest_path):
                    counter += 1
                    os.remove(curr_path)

    return counter
