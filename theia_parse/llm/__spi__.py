from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Deque, Literal

from jinja2 import Environment as JinjaEnvironment
from pydantic import BaseModel, ConfigDict

from theia_parse.__spi__ import BaseEnvSettings
from theia_parse.model import ContentElement, DocumentPage, LlmUsage, Medium
from theia_parse.parser.__spi__ import PromptConfig


LlmApiProvider = Literal["azure_openai"]


class LlmApiSettings(BaseModel):
    provider: LlmApiProvider = "azure_openai"
    api_version: str
    model: str
    endpoint: str
    key: str


class LlmApiEnvSettings(BaseEnvSettings):
    PROVIDER: LlmApiProvider = "azure_openai"
    AZURE_OPENAI_API_VERSION: str = ""
    AZURE_OPENAI_API_ENDPOINT: str = ""
    AZURE_OPENAI_API_DEPLOYMENT: str = ""
    AZURE_OPENAI_API_KEY: str = ""

    def to_settings(self) -> LlmApiSettings:
        return LlmApiSettings(
            provider=self.PROVIDER,
            api_version=self.AZURE_OPENAI_API_VERSION,
            endpoint=self.AZURE_OPENAI_API_ENDPOINT,
            model=self.AZURE_OPENAI_API_DEPLOYMENT,
            key=self.AZURE_OPENAI_API_KEY,
        )


class LlmResponse(BaseModel):
    raw: str
    usage: LlmUsage = LlmUsage()


class LlmExtractionResult(BaseModel):
    raw: str
    content: list[ContentElement] | None = None
    usage: LlmUsage = LlmUsage()
    error: bool = False


class LlmGenerationConfig(BaseModel):
    temperature: float = 0
    max_tokens: int | None = None
    json_mode: bool = True


class PromptAdditions(BaseModel):
    system_prompt_preamble: str | None = None
    custom_instructions: list[str] | None = None
    raw_extracted_text: str | None = None
    previous_headings: list[str] | None = None
    previous_parsed_pages: list[str] | None = None
    embedded_images: bool | None = None

    @staticmethod
    def create(
        config: PromptConfig,
        raw_extracted_text: str | None = None,
        previous_headings: Deque[ContentElement] | None = None,
        previous_parsed_pages: Deque[DocumentPage] | None = None,
        embedded_images: list[Medium] | None = None,
    ) -> PromptAdditions:
        return PromptAdditions(
            system_prompt_preamble=config.system_prompt_preamble,
            custom_instructions=config.custom_instructions,
            raw_extracted_text=(
                raw_extracted_text if config.include_raw_extracted_text else None
            ),
            previous_headings=PromptAdditions._previous_headings(previous_headings),
            previous_parsed_pages=PromptAdditions._previous_parsed_pages(
                previous_parsed_pages
            ),
            embedded_images=bool(embedded_images),
        )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)

    @staticmethod
    def _previous_headings(
        previous_headings: Deque[ContentElement] | None,
    ) -> list[str] | None:
        if previous_headings is not None:
            return [f"{h.type}: {h.content}" for h in previous_headings]

    @staticmethod
    def _previous_parsed_pages(
        previous_parsed_pages: Deque[DocumentPage] | None,
    ) -> list[str] | None:
        if previous_parsed_pages is not None:
            return [p.content_to_string() for p in previous_parsed_pages]


class LLM(ABC):
    """
    Multimodal LLM
    """

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        images: list[Medium],
        config: LlmGenerationConfig,
    ) -> LlmResponse | None:
        pass


class Prompt:
    def __init__(self, template: str) -> None:
        self._template = JinjaEnvironment(trim_blocks=True).from_string(template)

    def render(self, data: dict[str, Any]) -> str:
        return self._template.render(**data).strip()
