import os
from pathlib import Path

from theia_parse.model import ContentElement, DocumentPage, ParsedDocument
from theia_parse.util.files import has_suffixes, read_json


PATH = (Path(__file__).parent.parent / "data/sample").resolve()
PARSED_JSON_SUFFIX = ".parsed.json"


def main():
    for root, _, file_names in os.walk(PATH):
        for file_name in file_names:
            curr_path = Path(root) / file_name
            if has_suffixes(curr_path, PARSED_JSON_SUFFIX):
                raw = read_json(curr_path)
                doc = ParsedDocument(**raw)
                text = doc_to_markdown(doc)
                save_path = curr_path.with_suffix(".md")
                save_path.write_text(text)


def content_to_markdown(content: ContentElement) -> str:
    if content.is_heading():
        return f"{'#'*content.heading_level} {content.content}"
    elif content.type == "image":
        return f"![{content.content}](...)"
    else:
        return content.content


def page_to_markdown(page: DocumentPage) -> str:
    text = f"PAGE: {page.page_nr}\n"
    for content in page.content:
        text = f"{text}\n\n{content_to_markdown(content)}"

    return text


def doc_to_markdown(doc: ParsedDocument) -> str:
    text = f"PATH: {doc.path}\n"
    if doc.metadata:
        text = f"{text}\n{str(doc.metadata)}"

    for page in doc.pages:
        text = f"{text}\n\n\n\n{page_to_markdown(page)}"

    return text


if __name__ == "__main__":
    main()
