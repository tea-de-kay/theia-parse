import os
from pathlib import Path

from theia_parse.const import PARSED_JSON_SUFFIXES
from theia_parse.formatter.markdown_formatter import MarkdownFormatter
from theia_parse.model import DocumentPage, ParsedDocument
from theia_parse.util.files import has_suffixes, read_json, with_suffix


PATH = (Path(__file__).parent.parent / "data/sample").resolve()

formatter = MarkdownFormatter()


def main():
    for root, _, file_names in os.walk(PATH):
        for file_name in file_names:
            curr_path = Path(root) / file_name
            if has_suffixes(curr_path, PARSED_JSON_SUFFIXES):
                raw = read_json(curr_path)
                doc = ParsedDocument(**raw)
                text = doc_to_markdown(doc)
                save_path = with_suffix(
                    curr_path,
                    ".parsed.md",
                    replace_suffixes=PARSED_JSON_SUFFIXES,
                )
                save_path.write_text(text)


def page_to_markdown(page: DocumentPage) -> str:
    text = f"PAGE: {page.page_number}\n"
    text = f"{text}\n\n{formatter.format(page.content)}"

    return text


def doc_to_markdown(doc: ParsedDocument) -> str:
    text = f"PATH: {doc.path}\n"
    if doc.metadata:
        text = f"{text}\n{str(doc.metadata)}"

    for page in doc.content:
        text = f"{text}\n\n\n\n{page_to_markdown(page)}"

    return text


if __name__ == "__main__":
    main()
