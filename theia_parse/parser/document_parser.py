import json
import os
from pathlib import Path
from typing import Generator

from tqdm import tqdm

from theia_parse.llm.__spi__ import LLM, LlmApiSettings
from theia_parse.llm.openai.openai_llm import OpenAiLLM
from theia_parse.model import DocumentParserConfig, ParsedDocument
from theia_parse.parser.file_parser import EXTENSION_TO_PARSER
from theia_parse.util.files import get_md5_sum, get_total_number_of_files
from theia_parse.util.log import LogFactory


DEFAULT_DOCUMENT_PARSER_CONFIG = DocumentParserConfig()
PARSED_JSON_SUFFIX = ".parsed.json"
DUPLICATE_SUFFIX = ".duplicate"


class DocumentParser:
    _log = LogFactory.get_logger()

    def __init__(
        self,
        llm: LLM | None = None,
        config: DocumentParserConfig = DEFAULT_DOCUMENT_PARSER_CONFIG,
    ) -> None:
        if llm is None:
            self._llm = OpenAiLLM(config=LlmApiSettings())
        else:
            self._llm = llm

        self._config = config

    def parse(self, path: str | Path) -> Generator[ParsedDocument, None, None]:
        path = Path(path)

        if path.is_file():
            parsed = self._parse_file(path)
            if parsed is not None:
                if self._config.save_files:
                    self._save_parsed_doc(parsed, path)
                yield parsed
        else:
            hash_to_path: dict[str, Path] = {}
            for root, _, file_names in tqdm(
                os.walk(path),
                desc="files",
                disable=not self._config.verbose,
                total=get_total_number_of_files(path, list(EXTENSION_TO_PARSER.keys())),
            ):
                for file_name in sorted(file_names):
                    current_path = Path(root) / file_name
                    self._log.info("Working on file [path='{0}']", current_path)
                    md5_sum = get_md5_sum(current_path)
                    if self._config.deduplicate_docs and (
                        existing_path := hash_to_path.get(md5_sum)
                    ):
                        self._log.info(
                            "Skipping file due to deduplication "
                            "[path='{0}', duplicate_path='{1}']",
                            current_path,
                            existing_path,
                        )
                        self._save_duplicate_info(current_path, existing_path)
                        continue
                    hash_to_path[md5_sum] = current_path

                    parsed = self._parse_file(current_path)
                    if parsed is not None:
                        parsed.md5_sum = md5_sum
                        if self._config.save_files:
                            self._save_parsed_doc(parsed, current_path)
                        yield parsed

    def _parse_file(self, path: Path) -> ParsedDocument | None:
        parser = EXTENSION_TO_PARSER.get(path.suffix.strip(".").lower())
        if parser is None:
            self._log.warning("Filetype not supported [path='{0}']", path)
            return

        return parser.parse(path=path, llm=self._llm, config=self._config)

    def _save_parsed_doc(self, parsed_doc: ParsedDocument, path: Path) -> None:
        save_path = path.with_suffix(PARSED_JSON_SUFFIX)
        with open(save_path, "wt") as outfile:
            json.dump(parsed_doc.model_dump(), outfile)

    def _save_duplicate_info(self, path: Path, existing_path: Path) -> None:
        save_path = path.with_suffix(DUPLICATE_SUFFIX)
        save_path.write_text(str(existing_path))