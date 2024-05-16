import os
from pathlib import Path
from typing import Generator

from tqdm import tqdm

from theia_parse.const import DUPLICATE_SUFFIX
from theia_parse.llm.__spi__ import LLM, LlmApiSettings
from theia_parse.llm.openai.openai_llm import OpenAiLLM
from theia_parse.model import ParsedDocument, ParserConfig
from theia_parse.parser.document_parser import DocumentParser
from theia_parse.parser.file_parser import EXTENSION_TO_PARSER
from theia_parse.util.files import get_md5_sum, is_file_supported
from theia_parse.util.log import LogFactory


DEFAULT_DOCUMENT_PARSER_CONFIG = ParserConfig()


class DirectoryParser:
    _log = LogFactory.get_logger()

    def __init__(
        self,
        llm: LLM | None = None,
        config: ParserConfig = DEFAULT_DOCUMENT_PARSER_CONFIG,
    ) -> None:
        if llm is None:
            self._llm = OpenAiLLM(config=LlmApiSettings())
        else:
            self._llm = llm

        self._config = config
        self._document_parser = DocumentParser(self._llm, config)

    def parse(
        self,
        directory: str | Path,
        existing_hash_to_path: dict[str, str | Path] | None = None,
    ) -> Generator[ParsedDocument, None, None]:
        directory = Path(directory)

        if not directory.is_dir():
            self._log.warning("Not a directory [path='{0}']", directory)
            return

        hash_to_path: dict[str, Path] = {}
        if existing_hash_to_path is not None:
            hash_to_path = {k: Path(v) for k, v in existing_hash_to_path.items()}

        for root, _, file_names in os.walk(directory):
            self._log.info("Working on directory [dir_name='{0}']", root)
            file_name_iterator = tqdm(
                sorted(f for f in file_names if is_file_supported(f)),
                desc="files in dir",
                disable=not self._config.verbose,
            )
            for file_name in file_name_iterator:
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
                    file_name_iterator.update()
                    continue

                parsed = self._document_parser.parse(current_path)
                if parsed is not None:
                    hash_to_path[md5_sum] = current_path
                    yield parsed

    def _save_duplicate_info(self, path: Path, existing_path: Path) -> None:
        save_path = path.with_suffix(DUPLICATE_SUFFIX)
        save_path.write_text(str(existing_path))
