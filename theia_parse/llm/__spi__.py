from abc import ABC, abstractmethod
from typing import Any

from jinja2 import Environment as JinjaEnvironment
from pydantic import BaseModel

from theia_parse.__spi__ import BaseEnvSettings
from theia_parse.model import PromptAdditions


class LlmApiSettings(BaseEnvSettings):
    AZURE_OPENAI_API_VERSION: str
    AZURE_OPENAI_API_BASE: str
    AZURE_OPENAI_API_DEPLOYMENT: str
    AZURE_OPENAI_API_KEY: str


class LLMUsage(BaseModel):
    request_tokens: int | None = None
    response_tokens: int | None = None
    total_tokens: int | None = None


class LLMResponse(BaseModel):
    raw: str
    usage: LLMUsage = LLMUsage()


class LLM(ABC):
    """
    Multimodal LLM
    """

    @abstractmethod
    def extract(
        self,
        image_data: bytes | None,
        extracted_text: str | None,
    ) -> LLMResponse:
        pass


class Prompt:
    def __init__(self, template: str) -> None:
        self._template = JinjaEnvironment(trim_blocks=True).from_string(template)

    def render(self, data: dict[str, Any]) -> str:
        return self._template.render(**data)


class Prompts(BaseModel):
    mm_extract_content_system_prompt: Prompt
    mm_extract_content_user_prompt: Prompt
