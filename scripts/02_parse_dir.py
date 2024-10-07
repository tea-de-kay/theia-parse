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

# GPT-4o-mini price
EURO_PER_REQUEST_TOKENS = 2.6867 / 1_000_000
EURO_PER_RESPONSE_TOKENS = 10.746430 / 1_000_000


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
        prompt_config=PromptConfig(custom_instructions=[]),
    )
    parser = DirectoryParser(
        config=DirectoryParserConfig(document_parser_config=config),
    )

    request_tokens = 0
    response_tokens = 0
    for doc in parser.parse(DATA_PATH):
        if doc is not None:
            request_tokens += doc.token_usage.request_tokens or 0
            response_tokens += doc.token_usage.response_tokens or 0

    total_price = (
        request_tokens * EURO_PER_REQUEST_TOKENS
        + response_tokens * EURO_PER_RESPONSE_TOKENS
    )
    total_tokens = request_tokens + response_tokens

    tqdm.write(f"Total tokens used: {total_tokens}.")
    tqdm.write(f"Total price: {total_price:.2f}.")


if __name__ == "__main__":
    main()
