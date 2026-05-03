from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    folder_path: str = Field(..., description="Windows folder containing pdf, md, txt, and json files.")


class GmailIngestRequest(BaseModel):
    sender: str = Field(..., description="Email address or sender search term, used as Gmail from:sender.")
    max_results: int = Field(default=25, ge=1, le=500)
    newer_than_days: int | None = Field(default=None, ge=1, le=3650)
    output_folder: str | None = Field(default=None)
    credentials_file: str | None = Field(default=None)
    token_file: str | None = Field(default=None)


class ZapierEmailIngestRequest(BaseModel):
    secret: str | None = Field(default=None, description="Optional shared secret matching ZAPIER_INGEST_SECRET.")
    sender: str | None = None
    from_email: str | None = None
    to: str | None = None
    cc: str | None = None
    subject: str | None = None
    date: str | None = None
    body_plain: str | None = None
    body_html: str | None = None
    snippet: str | None = None
    message_id: str | None = None
    output_folder: str | None = None


class Usage(BaseModel):
    llm_input_tokens: int
    llm_output_tokens: int
    embedding_tokens: int
    estimated_llm_cost_usd: float
    estimated_embedding_cost_usd: float
    estimated_total_cost_usd: float
    pricing_note: str


class IngestResponse(BaseModel):
    folder_path: str
    documents_loaded: int
    collection: str
    message: str
    index_id: str | None = None
    usage: Usage


class GmailIngestResponse(BaseModel):
    sender: str
    query: str
    output_folder: str
    emails_exported: int
    exported_files: list[str]
    ingestion: IngestResponse


class ZapierEmailIngestResponse(BaseModel):
    output_folder: str
    exported_file: str
    ingestion: IngestResponse


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class Source(BaseModel):
    score: float | None = None
    file_name: str | None = None
    file_path: str | None = None
    page_label: str | None = None
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    usage: Usage
