from abc import ABC, abstractmethod
from pathlib import Path

from theia_parse.llm.__spi__ import LLM
from theia_parse.model import ParsedDocument, ParserConfig


class FileParser(ABC):
    @abstractmethod
    def parse(
        self,
        path: Path,
        llm: LLM,
        config: ParserConfig,
    ) -> ParsedDocument | None:
        pass

    @abstractmethod
    def get_number_of_pages(self, path: Path, config: ParserConfig) -> int | None:
        pass
