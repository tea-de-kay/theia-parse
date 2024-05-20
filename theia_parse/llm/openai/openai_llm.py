from base64 import b64encode
from typing import Any

from openai import AzureOpenAI

from theia_parse.llm.__spi__ import (
    LLM,
    LlmApiSettings,
    LLMExtractionResult,
    LLMGenerationConfig,
    LLMResponse,
    PromptAdditions,
    Prompts,
)
from theia_parse.llm.openai.prompt_templates import DEFAULT_PROMPTS
from theia_parse.llm.response_parser.json_parser import JsonParser
from theia_parse.model import ContentElement, LLMUsage
from theia_parse.util.log import LogFactory


class OpenAiLLM(LLM):
    _log = LogFactory.get_logger()

    def __init__(
        self,
        config: LlmApiSettings,
        prompts: Prompts = DEFAULT_PROMPTS,
    ) -> None:
        self._config = config
        self._prompts = prompts

        self._client = AzureOpenAI(
            azure_endpoint=config.AZURE_OPENAI_API_BASE,
            api_version=config.AZURE_OPENAI_API_VERSION,
            api_key=config.AZURE_OPENAI_API_KEY,
        )

        self._json_parser = JsonParser()

    def generate(
        self, messages: list[dict], config: LLMGenerationConfig
    ) -> LLMResponse | None:
        try:
            self._log.trace("Calling LLM [messages='{0}']", messages)
            response = self._client.chat.completions.create(
                model=self._config.AZURE_OPENAI_API_DEPLOYMENT,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            self._log.trace("Raw LLM response [response='{0}']", response)
        except Exception as e:
            self._log.error("Exception calling LLM [msg='{0}']", e)
            return

        return LLMResponse(
            raw=response.choices[0].message.content,
            usage=LLMUsage(
                request_tokens=response.usage.prompt_tokens,
                response_tokens=response.usage.completion_tokens,
            ),
        )

    def extract(
        self,
        image_data: bytes | None,
        raw_extracted_text: str | None,
        prompt_additions: PromptAdditions,
    ) -> LLMExtractionResult:
        prompt_data = {
            **prompt_additions.model_dump(),
            "raw_extracted_text": raw_extracted_text,
        }

        messages = self._assemble_messages(prompt_data, image_data)

        response = self.generate(
            messages,
            LLMGenerationConfig(temperature=0, max_tokens=4096),
        )

        if response is None:
            return LLMExtractionResult(raw="", error=True)

        page_data = self._json_parser.parse(response.raw)
        error = False
        content = []
        if page_data is None:
            error = True
        else:
            for element in page_data.get("page_content", []):
                try:
                    content.append(ContentElement(**element))
                except Exception:
                    self._log.error(
                        "Could not create content element [raw='{0}']", element
                    )
                    error = True

        return LLMExtractionResult(
            raw=response.raw,
            content=content,
            usage=response.usage,
            error=error,
        )

    def _image_bytes_to_data_url(
        self,
        image_data: bytes,
        mime_type: str = "image/png",
    ):
        base64_encoded_data = b64encode(image_data).decode("utf-8")

        return f"data:{mime_type};base64,{base64_encoded_data}"

    def _assemble_messages(
        self,
        prompt_data: dict[str, Any],
        image_data: bytes | None,
    ) -> list[dict]:
        system_message = {
            "role": "system",
            "content": self._prompts.mm_extract_content_system_prompt.render(
                prompt_data
            ),
        }

        user_message_content: list[dict] = [
            {
                "type": "text",
                "text": self._prompts.mm_extract_content_user_prompt.render(
                    prompt_data
                ),
            }
        ]

        if image_data is not None:
            user_message_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": self._image_bytes_to_data_url(image_data)},
                }
            )

        user_message = {"role": "user", "content": user_message_content}

        return [system_message, user_message]
