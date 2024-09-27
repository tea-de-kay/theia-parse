import os
from pathlib import Path
from typing import Generator

from tqdm import tqdm

from theia_parse.const import DUPLICATE_SUFFIXES
from theia_parse.llm.__spi__ import LLM, LlmApiEnvSettings
from theia_parse.llm.openai.azure_openai_llm import AzureOpenAiLLM
from theia_parse.model import ParsedDocument
from theia_parse.parser.__spi__ import DirectoryParserConfig
from theia_parse.parser.document_parser import DocumentParser
from theia_parse.util.files import get_md5_sum, is_file_supported, with_suffix
from theia_parse.util.log import LogFactory


DEFAULT_DIRECTORY_PARSER_CONFIG = DirectoryParserConfig()


class DirectoryParser:
    _log = LogFactory.get_logger()

    def __init__(
        self,
        llm: LLM | None = None,
        config: DirectoryParserConfig = DEFAULT_DIRECTORY_PARSER_CONFIG,
    ) -> None:
        if llm is None:
            self._llm = AzureOpenAiLLM(config=LlmApiEnvSettings())
        else:
            self._llm = llm

        self._config = config
        self._document_parser = DocumentParser(self._llm, config.document_parser_config)

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
                desc="file in dir",
                disable=not self._config.verbose,
                ncols=80,
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

    def get_number_of_pages(
        self,
        directory: str | Path,
        existing_hash_to_path: dict[str, str | Path] | None = None,
    ) -> tuple[int, int]:
        """
        Returns (total number of pages, number of duplicate pages)
        """

        directory = Path(directory)

        if not directory.is_dir():
            self._log.warning("Not a directory [path='{0}']", directory)
            return 0, 0

        hash_to_path: dict[str, Path] = {}
        if existing_hash_to_path is not None:
            hash_to_path = {k: Path(v) for k, v in existing_hash_to_path.items()}

        total_pages = 0
        duplicate_pages = 0
        for root, _, file_names in os.walk(directory):
            for file_name in sorted(f for f in file_names if is_file_supported(f)):
                current_path = Path(root) / file_name
                n_pages = self._document_parser.get_number_of_pages(current_path)
                total_pages += n_pages or 0
                md5_sum = get_md5_sum(current_path)
                if md5_sum in hash_to_path:
                    duplicate_pages += n_pages or 0
                hash_to_path[md5_sum] = current_path

        return total_pages, duplicate_pages

    def _save_duplicate_info(self, path: Path, existing_path: Path) -> None:
        save_path = with_suffix(path, DUPLICATE_SUFFIXES)
        save_path.write_text(str(existing_path))
