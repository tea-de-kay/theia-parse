from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from theia_parse import DocumentParser, DocumentParserConfig
from theia_parse.model import PromptAdditions


PATH = (Path(__file__).parent.parent / "data/sample").resolve()

# GPT-4 Turbo prices
PRICE_PER_REQUEST_TOKEN = 0.01 / 1_000
PRICE_PER_RESPONSE_TOKEN = 0.029 / 1_000


def main():
    # Environment variables for LLM API must be set or present in .env file
    # AZURE_OPENAI_API_VERSION
    # AZURE_OPENAI_API_BASE
    # AZURE_OPENAI_API_DEPLOYMENT
    # AZURE_OPENAI_API_KEY

    load_dotenv()

    config = DocumentParserConfig(
        verbose=True,
        save_files=True,
        prompt_additions=PromptAdditions(
            custom_instructions=[
                "Most pages will have a multilingual 2 column layout. Make sure to correctly separate the columns as separate content blocks per language.",  # noqa
                "One column should be a single content block.",
                "Do not convert layout columns to tables.",
                "Keep mixed language headings as a single block including their numbering.",  # noqa
            ]
        ),
    )
    parser = DocumentParser(config=config)

    request_tokens = 0
    response_tokens = 0
    for doc in parser.parse(PATH):
        if doc is not None:
            for page in doc.pages:
                if page.token_usage.request_tokens is not None:
                    request_tokens += page.token_usage.request_tokens
                if page.token_usage.response_tokens is not None:
                    response_tokens += page.token_usage.response_tokens

    total_price = round(
        request_tokens * PRICE_PER_REQUEST_TOKEN
        + response_tokens * PRICE_PER_RESPONSE_TOKEN,
        2,
    )
    total_tokens = request_tokens + response_tokens

    tqdm.write(f"Total tokens used: {total_tokens}.")
    tqdm.write(f"Total price: {total_price}.")


if __name__ == "__main__":
    main()
