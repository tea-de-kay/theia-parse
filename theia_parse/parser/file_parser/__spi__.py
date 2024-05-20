from abc import ABC, abstractmethod
from pathlib import Path

from theia_parse.llm.__spi__ import LLM
from theia_parse.model import ParsedDocument
from theia_parse.parser.__spi__ import DocumentParserConfig


class FileParser(ABC):
    @abstractmethod
    def parse(
        self,
        path: Path,
        llm: LLM,
        config: DocumentParserConfig,
    ) -> ParsedDocument | None:
        pass

    @abstractmethod
    def get_number_of_pages(self, path: Path, config: DocumentParserConfig) -> int:
        pass
