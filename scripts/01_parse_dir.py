from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from theia_parse import (
    DirectoryParser,
    DirectoryParserConfig,
    DocumentParserConfig,
    PromptConfig,
)


ENV_PATH = Path(__file__).parent / ".env"
DATA_PATH = (Path(__file__).parent.parent / "data/sample/").resolve()

# GPT-4o-mini Turbo price
PRICE_PER_REQUEST_TOKEN = 0.00014 / 1_000
PRICE_PER_RESPONSE_TOKEN = 0.0006 / 1_000
APPROXIMATE_PRICE_PER_PAGE = 0.0055  # TODO: get better estimate


def main():
    # Environment variables for LLM API must be set or present in .env file
    # AZURE_OPENAI_API_VERSION
    # AZURE_OPENAI_API_BASE
    # AZURE_OPENAI_API_DEPLOYMENT
    # AZURE_OPENAI_API_KEY

    load_dotenv(ENV_PATH)

    config = DocumentParserConfig(
        verbose=True,
        save_file=True,
        prompt_config=PromptConfig(
            custom_instructions=[
                "Most pages will have a multilingual 2 column layout. Make sure to correctly separate the columns as separate content blocks per language.",  # noqa
                "One column should be a single content block.",
                "Do not convert layout columns to tables.",
                "Keep mixed language headings as a single block including their numbering.",  # noqa
            ]
        ),
    )
    parser = DirectoryParser(
        config=DirectoryParserConfig(document_parser_config=config),
    )

    pages = parser.get_number_of_pages(DATA_PATH)
    if pages:
        total_pages, duplicate_pages = pages
        expected_price = (total_pages - duplicate_pages) * APPROXIMATE_PRICE_PER_PAGE

        tqdm.write(f"TOTAL PAGES: {total_pages}, DUPLICATE PAGES: {duplicate_pages}")
        tqdm.write(f"EXPECTED PRICE: {expected_price:.2f}")

        char = input("Continue ... [y/n]: ")
        if char != "y":
            return

    request_tokens = 0
    response_tokens = 0
    for doc in parser.parse(DATA_PATH):
        if doc is not None:
            request_tokens += doc.token_usage.request_tokens or 0
            response_tokens += doc.token_usage.response_tokens or 0

    total_price = (
        request_tokens * PRICE_PER_REQUEST_TOKEN
        + response_tokens * PRICE_PER_RESPONSE_TOKEN
    )
    total_tokens = request_tokens + response_tokens

    tqdm.write(f"Total tokens used: {total_tokens}.")
    tqdm.write(f"Total price: {total_price:.2f}.")


if __name__ == "__main__":
    main()
