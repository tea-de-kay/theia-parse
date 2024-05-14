import json
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from theia_parse import DocumentParser
from theia_parse.model import ParsedDocument


PATH = (Path(__file__).parent.parent / "data/sample").resolve()

PRICE_PER_REQUEST_TOKEN = 0.01 / 1_000
PRICE_PER_RESPONSE_TOKEN = 0.029 / 1_000


def main():
    # Environment variables for LLM API must be set or present in .env file
    # AZURE_OPENAI_API_VERSION
    # AZURE_OPENAI_API_BASE
    # AZURE_OPENAI_API_DEPLOYMENT
    # AZURE_OPENAI_API_KEY

    load_dotenv()

    parser = DocumentParser()

    docs: list[ParsedDocument] = []
    for res in parser.parse(PATH):
        if res is not None:
            docs.append(res)

    print(PATH / "parsed.json")

    with open(PATH / "parsed.json", "wt") as outfile:
        json.dump([doc.model_dump() for doc in docs], outfile)

    request_tokens = 0
    response_tokens = 0
    for doc in docs:
        for page in doc.pages:
            request_tokens += page.token_usage.request_tokens
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
