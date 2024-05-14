import os
from pathlib import Path

from theia_parse.llm.__spi__ import LLM, LlmApiSettings
from theia_parse.llm.openai.openai_llm import OpenAiLLM
from theia_parse.model import ParsedDocument
from theia_parse.parser.file_parser import EXTENSION_TO_PARSER
from theia_parse.util.log import LogFactory


class DocumentParser:
    _log = LogFactory.get_logger()

    def __init__(self, llm: LLM | None = None, verbose: bool = True) -> None:
        if llm is None:
            self._llm = OpenAiLLM(config=LlmApiSettings())
        else:
            self._llm = llm

        self._verbose = verbose

    def parse(self, path: str | Path) -> ParsedDocument | list[ParsedDocument] | None:
        path = Path(path)

        if path.is_file():
            return self._parse_file(path)
        else:
            docs = []
            for root, _, file_names in os.walk(path):
                for file_name in file_names:
                    parsed = self._parse_file(Path(root) / file_name)
                    if parsed is not None:
                        docs.append(parsed)

        return docs if docs else None

    def _parse_file(self, path: Path) -> ParsedDocument | None:
        parser = EXTENSION_TO_PARSER.get(path.suffix.strip(".").lower())
        if parser is None:
            self._log.warning("Filetype not supported [path='{0}']", path)
            return

        return parser.parse(path=path, llm=self._llm, verbose=self._verbose)
