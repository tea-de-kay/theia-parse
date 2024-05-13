from openai import AzureOpenAI

from theia_parse.llm.__spi__ import LLM, LlmApiSettings, LLMResponse, Prompts
from theia_parse.llm.openai.prompt_templates import DEFAULT_PROMPTS
from theia_parse.model import PromptAdditions


DEFAULT_PROMPT_ADDITIONS = PromptAdditions()


class OpenAiLM(LLM):
    def __init__(
        self,
        config: LlmApiSettings,
        prompts: Prompts = DEFAULT_PROMPTS,
        prompt_additions: PromptAdditions = DEFAULT_PROMPT_ADDITIONS,
    ) -> None:
        self._config = config
        self._prompts = prompts
        self._prompt_additions = prompt_additions

        self._client = AzureOpenAI(
            azure_endpoint=config.AZURE_OPENAI_API_BASE,
            api_version=config.AZURE_OPENAI_API_VERSION,
            api_key=config.AZURE_OPENAI_API_KEY,
        )

    def extract(
        self,
        image_data: bytes | None,
        extracted_text: str | None,
    ) -> LLMResponse:
        pass
