from pathlib import Path

from theia_parse.const import PARSED_JSON_SUFFIXES
from theia_parse.llm.__spi__ import LlmApiEnvSettings, LlmApiSettings
from theia_parse.model import ParsedDocument
from theia_parse.parser.__spi__ import DocumentParserConfig
from theia_parse.parser.file_parser import get_parser
from theia_parse.util.files import with_suffix, write_json


DEFAULT_DOCUMENT_PARSER_CONFIG = DocumentParserConfig()


class DocumentParser:
    def __init__(
        self,
        llm_api_settings: LlmApiSettings | None = None,
        config: DocumentParserConfig = DEFAULT_DOCUMENT_PARSER_CONFIG,
    ) -> None:
        if llm_api_settings is None:
            llm_api_settings = LlmApiEnvSettings().to_settings()

        self._llm_api_settings = llm_api_settings
        self._config = config

    def parse(self, path: str | Path) -> ParsedDocument | None:
        path = Path(path)

        parser = get_parser(path, self._llm_api_settings)
        if parser is None:
            return

        parsed = parser.parse(path, self._config)
        if parsed is not None:
            if self._config.save_file:
                save_path = with_suffix(path, PARSED_JSON_SUFFIXES)
                write_json(save_path, parsed)

        return parsed

    def get_number_of_pages(self, path: Path) -> int | None:
        parser = get_parser(path, self._llm_api_settings)
        if parser is not None:
            return parser.get_number_of_pages(path, self._config)

        return
