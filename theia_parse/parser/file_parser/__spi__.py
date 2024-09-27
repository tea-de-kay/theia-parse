from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path

from theia_parse.llm.__spi__ import LLM
from theia_parse.model import DocumentPage, ParsedDocument
from theia_parse.parser.__spi__ import DocumentParserConfig


class FileParser(ABC):
    @abstractmethod
    def parse_paged(
        self,
        path: Path,
        llm: LLM,
        config: DocumentParserConfig,
    ) -> Iterable[DocumentPage | None]:
        pass

    @abstractmethod
    def parse_hull(self, path: Path) -> ParsedDocument:
        pass

    @abstractmethod
    def get_number_of_pages(self, path: Path, config: DocumentParserConfig) -> int:
        pass
