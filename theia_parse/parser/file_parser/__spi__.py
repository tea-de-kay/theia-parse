from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path

from theia_parse.llm import get_llm
from theia_parse.llm.__spi__ import LlmApiSettings
from theia_parse.model import DocumentPage, ParsedDocument
from theia_parse.parser.__spi__ import DocumentParserConfig


class FileParser(ABC):
    def __init__(self, llm_api_settings: LlmApiSettings) -> None:
        self._llm = get_llm(llm_api_settings)

    @abstractmethod
    def parse_paged(
        self,
        path: Path,
        config: DocumentParserConfig,
    ) -> Iterable[DocumentPage | None]:
        pass

    @abstractmethod
    def parse_hull(self, path: Path) -> ParsedDocument:
        pass

    @abstractmethod
    def get_number_of_pages(self, path: Path, config: DocumentParserConfig) -> int:
        pass
