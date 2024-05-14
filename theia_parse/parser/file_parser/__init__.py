from theia_parse.parser.file_parser.__spi__ import FileParser
from theia_parse.parser.file_parser.pdf_parser import PDFParser


# TODO: Add more file types (or wrapper filetype -> pdf)
EXTENSION_TO_PARSER: dict[str, FileParser] = {
    "pdf": PDFParser(),
}
