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
    LlmResponse,
)
from theia_parse.model import LlmUsage, Medium
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
        images: list[Medium],
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
            system_prompt=system_prompt, user_prompt=user_prompt, images=images
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
            ),
        )

    # def extract(
    #     self,
    #     image_data: bytes | None,
    #     raw_extracted_text: str | None,
    #     prompt_additions: PromptAdditions,
    # ) -> LlExtractionResult:
    #     prompt_data = {
    #         **prompt_additions.model_dump(),
    #         "raw_extracted_text": raw_extracted_text,
    #     }

    #     messages = self._assemble_messages(prompt_data, image_data)

    #     response = self.generate(
    #         messages,
    #         LlmGenerationConfig(temperature=0, max_tokens=4096, json_mode=True),
    #     )

    #     if response is None:
    #         return LlExtractionResult(raw="", error=True)

    #     page_data = self._json_parser.parse(response.raw)
    #     error = False
    #     content = []
    #     if page_data is None:
    #         error = True
    #     else:
    #         for element in page_data.get("page_content", []):
    #             try:
    #                 content.append(ContentElement(**element))
    #             except Exception:
    #                 self._log.error(
    #                     "Could not create content element [raw='{0}']", element
    #                 )
    #                 error = True

    #     return LlExtractionResult(
    #         raw=response.raw,
    #         content=content,
    #         usage=response.usage,
    #         error=error,
    #     )

    def _assemble_image_url(self, image: Medium) -> dict[str, str | dict[str, str]]:
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{image.mime_type};base64,{image.content_b64}"},
        }

    def _assemble_raw_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        images: list[Medium],
    ) -> list[ChatCompletionMessageParam]:
        system_message = {"role": "system", "content": system_prompt}

        user_message_content: list[dict] = [{"type": "text", "text": user_prompt}]
        user_message_content.extend(self._assemble_image_url(image) for image in images)
        user_message = {"role": "user", "content": user_message_content}

        messages = cast(
            list[ChatCompletionMessageParam], [system_message, user_message]
        )

        return messages
