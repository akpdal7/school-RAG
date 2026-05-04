import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile

from rag_app.config import get_settings
from rag_app.gmail_ingestion import export_and_ingest_gmail_sender, save_zapier_email_and_ingest
from rag_app.ingestion import SUPPORTED_EXTENSIONS, ingest_folder
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


@app.post("/upload/ingest", response_model=IngestResponse)
async def upload_and_ingest(files: list[UploadFile] = File(...)) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one file.")

    unsupported = [
        file.filename
        for file in files
        if Path(file.filename or "").suffix.lower() not in SUPPORTED_EXTENSIONS
    ]
    if unsupported:
        allowed = ", ".join(SUPPORTED_EXTENSIONS)
        joined = ", ".join(unsupported)
        raise HTTPException(status_code=400, detail=f"Unsupported file type(s): {joined}. Allowed: {allowed}")

    upload_dir = Path(tempfile.gettempdir()) / "school-rag-uploads" / uuid4().hex
    upload_dir.mkdir(parents=True, exist_ok=True)

    try:
        for file in files:
            safe_name = Path(file.filename or f"upload-{uuid4().hex}").name
            destination = upload_dir / safe_name
            with destination.open("wb") as output:
                while chunk := await file.read(1024 * 1024):
                    output.write(chunk)

        return ingest_folder(str(upload_dir), get_settings())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        for file in files:
            await file.close()
        shutil.rmtree(upload_dir, ignore_errors=True)


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
