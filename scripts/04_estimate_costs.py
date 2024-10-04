"""
Estimate costs for parsing a directory with the PDF parser using an OpenAI model
TODO: include other file types
"""

import os
from pathlib import Path

import pdfplumber
from pdfplumber.page import Page as PdfPage
from tqdm import tqdm

from theia_parse.llm.openai.util import calc_image_token_usage
from theia_parse.model import LlmUsage
from theia_parse.parser.__spi__ import DocumentParserConfig
from theia_parse.parser.file_parser.pdf.pdf_parser import PdfParser


DATA_DIR = Path(__file__).parent.parent / "data/sample"

CONFIG = DocumentParserConfig()

# GPT-4o-mini
IMAGE_BASE_TOKENS = 2833
IMAGE_TOKENS_PER_TILE = 5667
N = 1_000_000
EURO_PER_REQUEST_TOKENS = 2.6867 / N
EURO_PER_RESPONSE_TOKENS = 10.746430 / N

TOKENS_PER_CHAR = 0.3
PROMPT_TOKENS = 1_000
TEXT_OUTPUT_TOKENS_PER_CHAR = 1


def main():
    request_tokens = 0
    response_tokens = 0
    for root, _, file_names in tqdm(os.walk(DATA_DIR)):
        for file_name in file_names:
            path = Path(root) / file_name
            if path.suffix.lower() == ".pdf":
                usage = _estimate_usage_pdf(path)
                assert usage.request_tokens is not None
                assert usage.response_tokens is not None

                request_tokens += usage.request_tokens
                response_tokens += usage.response_tokens

    estimated_costs = _calc_price(usage)
    print(
        "Estimated token usage: "
        f"request {usage.request_tokens}; response: {usage.response_tokens}"
    )
    print(f"Get ready to pay approximately € {estimated_costs:.2f}.")


def _calc_price(usage: LlmUsage) -> float:
    assert usage.request_tokens is not None
    assert usage.response_tokens is not None

    return (
        usage.request_tokens * EURO_PER_REQUEST_TOKENS
        + usage.response_tokens * EURO_PER_RESPONSE_TOKENS
    )


def _estimate_usage_pdf(path: Path) -> LlmUsage:
    request_tokens = 0
    response_tokens = 0
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text_usage = _calc_text_usage(page)
            image_usage = _calc_image_usage(page)
            page_usage = _calc_usage(text_usage=text_usage, image_usage=image_usage)
            assert page_usage.request_tokens is not None
            assert page_usage.response_tokens is not None

            request_tokens += page_usage.request_tokens
            response_tokens += page_usage.response_tokens

    return LlmUsage(request_tokens=request_tokens, response_tokens=response_tokens)


def _calc_usage(text_usage: LlmUsage, image_usage: LlmUsage) -> LlmUsage:
    assert text_usage.request_tokens is not None
    assert image_usage.request_tokens is not None

    request_tokens = (
        PROMPT_TOKENS + text_usage.request_tokens + image_usage.request_tokens
    )

    response_tokens = int(
        text_usage.request_tokens / TOKENS_PER_CHAR * TEXT_OUTPUT_TOKENS_PER_CHAR
    )

    return LlmUsage(request_tokens=request_tokens, response_tokens=response_tokens)


def _calc_text_usage(page: PdfPage) -> LlmUsage:
    text = page.extract_text()

    estimate = int(len(text) * TOKENS_PER_CHAR)

    return LlmUsage(request_tokens=estimate)


def _calc_image_usage(page: PdfPage) -> LlmUsage:
    _, embedded_images = PdfParser._get_images(page, CONFIG)
    res = CONFIG.image_extraction_config.resolution
    sizes = [_to_pixels(page.width, page.height, res)]
    sizes += [_to_pixels(img.width, img.height, res) for img in embedded_images]

    usages = [
        calc_image_token_usage(w, h, IMAGE_BASE_TOKENS, IMAGE_TOKENS_PER_TILE)
        for w, h in sizes
    ]

    return LlmUsage(request_tokens=sum(u.request_tokens or 0 for u in usages))


def _to_pixels(width: float, height: float, resolution: int) -> tuple[int, int]:
    width = int(width / 72 * resolution)
    height = int(height / 72 * resolution)

    return width, height


if __name__ == "__main__":
    main()
