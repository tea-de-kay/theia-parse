from abc import ABC, abstractmethod
from typing import Any, Literal

from jinja2 import Environment as JinjaEnvironment
from pydantic import BaseModel, ConfigDict

from theia_parse.__spi__ import BaseEnvSettings
from theia_parse.model import ContentElement, LlmUsage, Medium


class LlmApiSettings(BaseModel):
    api_version: str
    model: str
    endpoint: str
    key: str


class LlmApiEnvSettings(BaseEnvSettings):
    AZURE_OPENAI_API_VERSION: str = ""
    AZURE_OPENAI_API_ENDPOINT: str = ""
    AZURE_OPENAI_API_DEPLOYMENT: str = ""
    AZURE_OPENAI_API_KEY: str = ""

    def to_settings(self) -> LlmApiSettings:
        return LlmApiSettings(
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
    previous_headings: str | None = None
    previous_structured_page_content: str | None = None


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


class Prompts(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    mm_extract_content_system_prompt: Prompt
    mm_extract_content_user_prompt: Prompt
