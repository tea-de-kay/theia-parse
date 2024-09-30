from theia_parse.llm.__spi__ import LLM, LlmApiSettings
from theia_parse.llm.openai.azure_openai_llm import AzureOpenAiLLM


def get_llm(settings: LlmApiSettings) -> LLM:
    if settings.provider == "azure_openai":
        return AzureOpenAiLLM(settings)
    else:
        raise Exception(f"LLM API provider {settings.provider} not supported.")
