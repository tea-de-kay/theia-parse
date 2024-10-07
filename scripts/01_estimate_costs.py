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
from theia_parse.parser.__spi__ import DocumentParserConfig, ImageExtractionConfig
from theia_parse.parser.file_parser.pdf.pdf_parser import PdfParser


DATA_DIR = Path(__file__).parent.parent / "data/sample"

CONFIG = DocumentParserConfig(image_extraction_config=ImageExtractionConfig())

# GPT-4o-mini
IMAGE_BASE_TOKENS = 2833
IMAGE_TOKENS_PER_TILE = 5667
EURO_PER_REQUEST_TOKENS = 2.6867 / 1_000_000
EURO_PER_RESPONSE_TOKENS = 10.746430 / 1_000_000

TOKENS_PER_CHAR = 0.3
PROMPT_TOKENS = 1_000
TEXT_OUTPUT_TOKENS_PER_CHAR = 1


def main():
    all_paths: list[Path] = []
    for root, _, file_names in os.walk(DATA_DIR):
        root = Path(root)
        paths = sorted(root / f for f in file_names if _is_file_supported(f))
        all_paths.extend(paths)

    request_tokens = 0
    response_tokens = 0
    total_usage = LlmUsage(
        request_tokens=request_tokens, response_tokens=response_tokens
    )
    for path in tqdm(all_paths):
        tqdm.write(str(path))
        usage = _estimate_usage_pdf(path)
        assert usage.request_tokens is not None
        assert usage.response_tokens is not None

        request_tokens += usage.request_tokens
        response_tokens += usage.response_tokens

        total_usage = LlmUsage(
            request_tokens=request_tokens, response_tokens=response_tokens
        )
        estimated_costs = _calc_price(total_usage)
        tqdm.write(
            f"Estimated token usage up to now: request {usage.request_tokens}; "
            f"response: {usage.response_tokens}; € {estimated_costs:.2f}.\n"
        )

    estimated_costs = _calc_price(total_usage)
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


def _is_file_supported(file_name: str) -> bool:
    return file_name.lower().endswith(".pdf")


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
    embedded_images = PdfParser._get_embedded_images(
        page, CONFIG.image_extraction_config
    )
    res = CONFIG.image_extraction_config.resolution
    page_size = _to_pixels(page.width, page.height, res)
    embedded_sizes = [_to_pixels(img.width, img.height, res) for img in embedded_images]

    page_usage = calc_image_token_usage(
        page_size[0], page_size[1], IMAGE_BASE_TOKENS, IMAGE_TOKENS_PER_TILE
    )
    embedded_usages = [
        calc_image_token_usage(
            w,
            h,
            IMAGE_BASE_TOKENS,
            IMAGE_TOKENS_PER_TILE,
            low_res=CONFIG.image_extraction_config.use_low_details,
        )
        for w, h in embedded_sizes
    ]

    tokens = page_usage.request_tokens or 0 + sum(
        u.request_tokens or 0 for u in embedded_usages
    )
    return LlmUsage(request_tokens=tokens)


def _to_pixels(width: float, height: float, resolution: int) -> tuple[int, int]:
    width = int(width / 72 * resolution)
    height = int(height / 72 * resolution)

    return width, height


if __name__ == "__main__":
    main()
