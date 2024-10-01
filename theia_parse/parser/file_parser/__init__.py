from pathlib import Path

from theia_parse.llm.__spi__ import LlmApiSettings
from theia_parse.parser.file_parser.__spi__ import FileParser
from theia_parse.parser.file_parser.pdf.pdf_parser import PdfParser
from theia_parse.util.log import LogFactory


_log = LogFactory.get_logger()


# TODO: Add more file types (or wrapper filetype -> pdf)
EXTENSION_TO_PARSER: dict[str, type[FileParser]] = {
    "pdf": PdfParser,
}


def get_parser(
    path: Path,
    llm_api_settings: LlmApiSettings | None = None,
) -> FileParser | None:
    parser_cls = EXTENSION_TO_PARSER.get(path.suffix.strip(".").lower())
    if parser_cls is None:
        _log.warning("Filetype not supported [path='{0}']", path)
        return

    return parser_cls(llm_api_settings)
