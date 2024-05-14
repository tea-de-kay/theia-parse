from abc import ABC, abstractmethod

from theia_parse.llm.__spi__ import LLM
from theia_parse.model import ParsedDocument


class FileParser(ABC):
    @abstractmethod
    def parse(self, path: str, llm: LLM) -> ParsedDocument:
        pass
