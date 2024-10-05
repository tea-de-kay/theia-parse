from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast

from openai import NOT_GIVEN, AzureOpenAI, NotGiven
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.completion_create_params import ResponseFormat

from theia_parse.llm.__spi__ import (
    LLM,
    LlmApiSettings,
    LlmGenerationConfig,
    LlmMedium,
    LlmResponse,
)
from theia_parse.model import LlmUsage
from theia_parse.util.log import LogFactory


_log = LogFactory.get_logger()


class AzureOpenAiLLM(LLM):
    def __init__(self, api_settings: LlmApiSettings) -> None:
        self._api_settings = api_settings

    @contextmanager
    def _get_client(self) -> Iterator[AzureOpenAI]:
        client = AzureOpenAI(
            azure_endpoint=self._api_settings.endpoint,
            api_version=self._api_settings.api_version,
            api_key=self._api_settings.key,
        )
        try:
            yield client
        finally:
            client.close()

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        media: list[LlmMedium],
        config: LlmGenerationConfig,
    ) -> LlmResponse | None:
        _log.trace(
            "Calling LLM [system_prompt='{0}', user_prompt='{1}']",
            system_prompt,
            user_prompt,
        )

        response_format: ResponseFormat | NotGiven = NOT_GIVEN
        if config.json_mode:
            response_format = {"type": "json_object"}

        messages = self._assemble_raw_messages(
            system_prompt=system_prompt, user_prompt=user_prompt, media=media
        )

        try:
            with self._get_client() as client:
                response = client.chat.completions.create(
                    model=self._api_settings.model,
                    messages=messages,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    response_format=response_format,
                )

            _log.trace("Raw LLM response [response='{0}']", response)

            content = response.choices[0].message.content
            usage = response.usage
            assert content is not None
            assert usage is not None
        except Exception as e:
            _log.error("Exception calling LLM [msg='{0}']", e)
            return

        return LlmResponse(
            raw=content,
            usage=LlmUsage(
                request_tokens=usage.prompt_tokens,
                response_tokens=usage.completion_tokens,
                model=response.model,
            ),
        )

    def _assemble_image_url(
        self,
        medium: LlmMedium,
    ) -> dict[str, str | dict[str, str]]:
        image = medium.image
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{image.mime_type};base64,{image.content_b64}",
                "detail": medium.detail_level,
            },
        }

    def _assemble_raw_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        media: list[LlmMedium],
    ) -> list[ChatCompletionMessageParam]:
        system_message = {"role": "system", "content": system_prompt}

        user_message_content: list[dict] = [{"type": "text", "text": user_prompt}]
        user_message_content.extend(
            self._assemble_image_url(medium) for medium in media
        )
        user_message = {"role": "user", "content": user_message_content}

        messages = cast(
            list[ChatCompletionMessageParam], [system_message, user_message]
        )

        return messages
