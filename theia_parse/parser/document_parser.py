import os
from pathlib import Path
from typing import Generator

from tqdm import tqdm

from theia_parse.llm.__spi__ import LLM, LlmApiSettings
from theia_parse.llm.openai.openai_llm import OpenAiLLM
from theia_parse.model import ParsedDocument
from theia_parse.parser.file_parser import EXTENSION_TO_PARSER
from theia_parse.util.files import get_total_number_of_files
from theia_parse.util.log import LogFactory


class DocumentParser:
    _log = LogFactory.get_logger()

    def __init__(self, llm: LLM | None = None, verbose: bool = True) -> None:
        if llm is None:
            self._llm = OpenAiLLM(config=LlmApiSettings())
        else:
            self._llm = llm

        self._verbose = verbose

    def parse(self, path: str | Path) -> Generator[ParsedDocument | None, None, None]:
        path = Path(path)

        if path.is_file():
            yield self._parse_file(path)
        else:
            for root, _, file_names in tqdm(
                os.walk(path),
                desc="files",
                disable=not self._verbose,
                total=get_total_number_of_files(path),
            ):
                for file_name in file_names:
                    current_path = Path(root) / file_name
                    self._log.info("Working on file [path='{0}']", current_path)
                    parsed = self._parse_file(current_path)
                    if parsed is not None:
                        yield parsed

    def _parse_file(self, path: Path) -> ParsedDocument | None:
        parser = EXTENSION_TO_PARSER.get(path.suffix.strip(".").lower())
        if parser is None:
            self._log.warning("Filetype not supported [path='{0}']", path)
            return

        return parser.parse(path=path, llm=self._llm, verbose=self._verbose)
