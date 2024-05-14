from theia_parse.llm.__spi__ import LLM, LlmApiSettings
from theia_parse.llm.openai.openai_llm import OpenAiLLM
from theia_parse.model import ParsedDocument


class DocumentParser:
    def __init__(self, llm: LLM | None = None) -> None:
        if llm is None:
            self._llm = OpenAiLLM(config=LlmApiSettings())
        else:
            self._llm = llm

    def parse(self, path: str) -> ParsedDocument | list[ParsedDocument]:
        pass
