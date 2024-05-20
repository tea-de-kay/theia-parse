from pydantic import BaseModel


class DocumentParserConfig(BaseModel):
    verbose: bool = True
    save_file: bool = True
    system_prompt_preamble: str | None = None
    custom_instructions: list[str] | None = None


class DirectoryParserConfig(BaseModel):
    verbose: bool = True
    deduplicate_docs: bool = True
    document_parser_config: DocumentParserConfig = DocumentParserConfig()
