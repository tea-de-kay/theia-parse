from pathlib import Path

from theia_parse.parser.file_parser.__spi__ import FileParser
from theia_parse.parser.file_parser.pdf.pdf_parser import PDFParser
from theia_parse.util.log import LogFactory


_log = LogFactory.get_logger()


# TODO: Add more file types (or wrapper filetype -> pdf)
EXTENSION_TO_PARSER: dict[str, FileParser] = {
    "pdf": PDFParser(),
}


def get_parser(path: Path) -> FileParser | None:
    parser = EXTENSION_TO_PARSER.get(path.suffix.strip(".").lower())
    if parser is None:
        _log.warning("Filetype not supported [path='{0}']", path)
        return

    return parser
