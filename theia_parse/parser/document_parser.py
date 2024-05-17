import json
from pathlib import Path

from theia_parse.const import PARSED_JSON_SUFFIXES
from theia_parse.llm.__spi__ import LLM, LlmApiSettings
from theia_parse.llm.openai.openai_llm import OpenAiLLM
from theia_parse.model import ParsedDocument, ParserConfig
from theia_parse.parser.file_parser import EXTENSION_TO_PARSER
from theia_parse.util.files import with_suffix
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

        parsed = self._parse_file(path)
        if parsed is not None:
            if self._config.save_files:
                self._save_parsed_doc(parsed, path)

        return parsed

    def _parse_file(self, path: Path) -> ParsedDocument | None:
        parser = EXTENSION_TO_PARSER.get(path.suffix.strip(".").lower())
        if parser is None:
            self._log.warning("Filetype not supported [path='{0}']", path)
            return

        return parser.parse(path=path, llm=self._llm, config=self._config)

    def _save_parsed_doc(self, parsed_doc: ParsedDocument, path: Path) -> None:
        save_path = with_suffix(path, PARSED_JSON_SUFFIXES)
        with open(save_path, "wt") as outfile:
            json.dump(parsed_doc.model_dump(), outfile)
