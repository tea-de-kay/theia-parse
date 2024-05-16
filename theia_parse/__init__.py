from theia_parse.model import ParserConfig
from theia_parse.parser.directory_parser import DirectoryParser
from theia_parse.parser.document_parser import DocumentParser
from theia_parse.parser.file_parser import EXTENSION_TO_PARSER


SUPPORTED_EXTENSIONS = list(EXTENSION_TO_PARSER.keys())

__all__ = ["DocumentParser", "ParserConfig", "DirectoryParser", "SUPPORTED_EXTENSIONS"]
