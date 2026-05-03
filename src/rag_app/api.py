from fastapi import FastAPI, HTTPException

from rag_app.config import get_settings
from rag_app.gmail_ingestion import export_and_ingest_gmail_sender, save_zapier_email_and_ingest
from rag_app.ingestion import ingest_folder
from rag_app.models import (
    ChatRequest,
    ChatResponse,
    GmailIngestRequest,
    GmailIngestResponse,
    IngestRequest,
    IngestResponse,
    ZapierEmailIngestRequest,
    ZapierEmailIngestResponse,
)
from rag_app.query import answer_question


app = FastAPI(
    title="End-to-End RAG API",
    description="FastAPI backend for LlamaIndex ingestion, Qdrant Cloud retrieval, and RAG chat.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/config-check")
def config_check() -> dict:
    settings = get_settings()
    return {
        "mesh_api_base_url": settings.llm_api_base_url,
        "configured_llm_model": settings.openai_llm_model,
        "llama_index_llm_model": settings.llama_index_llm_model,
        "meshapi_llm_model": settings.meshapi_llm_model,
        "embedding_provider": settings.embedding_provider,
        "qdrant_collection": settings.qdrant_collection,
        "has_mesh_api_key": bool(settings.llm_api_key),
        "has_qdrant_url": bool(settings.qdrant_url),
        "has_qdrant_api_key": bool(settings.qdrant_api_key),
    }


@app.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> dict:
    try:
        return ingest_folder(request.folder_path, get_settings())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/gmail/ingest", response_model=GmailIngestResponse)
def ingest_gmail(request: GmailIngestRequest) -> dict:
    settings = get_settings()
    try:
        return export_and_ingest_gmail_sender(
            sender=request.sender,
            settings=settings,
            output_folder=request.output_folder or settings.gmail_json_output_folder,
            credentials_file=request.credentials_file or settings.gmail_credentials_file,
            token_file=request.token_file or settings.gmail_token_file,
            max_results=request.max_results,
            newer_than_days=request.newer_than_days,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/zapier/gmail/ingest", response_model=ZapierEmailIngestResponse)
def ingest_zapier_gmail(request: ZapierEmailIngestRequest) -> dict:
    settings = get_settings()
    if settings.zapier_ingest_secret and request.secret != settings.zapier_ingest_secret:
        raise HTTPException(status_code=401, detail="Invalid Zapier ingest secret.")

    try:
        return save_zapier_email_and_ingest(
            payload=request.model_dump(),
            settings=settings,
            output_folder=request.output_folder or settings.gmail_json_output_folder,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> dict:
    try:
        return answer_question(request.question, get_settings(), request.top_k)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
