from pathlib import Path

from theia_parse.const import PARSED_JSON_SUFFIXES
from theia_parse.llm.__spi__ import LLM, LlmApiSettings
from theia_parse.llm.openai.openai_llm import OpenAiLLM
from theia_parse.model import ParsedDocument, ParserConfig
from theia_parse.parser.file_parser import get_parser
from theia_parse.util.files import with_suffix, write_json
from theia_parse.util.log import LogFactory


DEFAULT_DOCUMENT_PARSER_CONFIG = ParserConfig()


class DocumentParser:
    _log = LogFactory.get_logger()

    def __init__(
        self,
        llm: LLM | None = None,
        config: ParserConfig = DEFAULT_DOCUMENT_PARSER_CONFIG,
    ) -> None:
        if llm is None:
            self._llm = OpenAiLLM(config=LlmApiSettings())
        else:
            self._llm = llm

        self._config = config

    def parse(self, path: str | Path) -> ParsedDocument | None:
        path = Path(path)

        parser = get_parser(path)
        if parser is None:
            return

        parsed = parser.parse(path=path, llm=self._llm, config=self._config)
        if parsed is not None:
            if self._config.save_files:
                save_path = with_suffix(
                    path,
                    PARSED_JSON_SUFFIXES,
                    keep_original_suffix=True,
                )
                write_json(save_path, parsed)

        return parsed

    def get_number_of_pages(self, path: Path) -> int | None:
        path = Path(path)

        parser = get_parser(path)
        if parser is not None:
            return parser.get_number_of_pages(path, self._config)
