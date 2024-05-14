from abc import ABC, abstractmethod
from pathlib import Path

from theia_parse.llm.__spi__ import LLM
from theia_parse.model import ParsedDocument


class FileParser(ABC):
    @abstractmethod
    def parse(self, path: Path, llm: LLM, verbose: bool) -> ParsedDocument | None:
        pass
