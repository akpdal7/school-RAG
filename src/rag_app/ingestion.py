from pathlib import Path

from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.readers.file import FlatReader, MarkdownReader, PDFReader
from llama_index.readers.json import JSONReader

from rag_app.config import Settings
from rag_app.qdrant_store import configure_llama_index, get_vector_store
from rag_app.usage import build_token_counter, summarize_usage


SUPPORTED_EXTENSIONS = [".pdf", ".md", ".markdown", ".txt", ".json"]


def load_documents(folder_path: str):
    folder = Path(folder_path).expanduser().resolve()
    if not folder.exists():
        raise FileNotFoundError(f"Folder does not exist: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Path is not a folder: {folder}")

    file_extractor = {
        ".pdf": PDFReader(),
        ".md": MarkdownReader(),
        ".markdown": MarkdownReader(),
        ".txt": FlatReader(),
        ".json": JSONReader(),
    }

    reader = SimpleDirectoryReader(
        input_dir=str(folder),
        recursive=True,
        required_exts=SUPPORTED_EXTENSIONS,
        file_extractor=file_extractor,
    )
    return reader.load_data(), folder


def ingest_folder(folder_path: str, settings: Settings) -> dict:
    token_counter = build_token_counter(settings)
    configure_llama_index(settings, token_counter)
    documents, folder = load_documents(folder_path)
    if not documents:
        return {
            "folder_path": str(folder),
            "documents_loaded": 0,
            "collection": settings.qdrant_collection,
            "usage": summarize_usage(token_counter, settings),
            "message": "No supported documents found.",
        }

    vector_store = get_vector_store(settings)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True,
    )

    return {
        "folder_path": str(folder),
        "documents_loaded": len(documents),
        "collection": settings.qdrant_collection,
        "index_id": index.index_id,
        "usage": summarize_usage(token_counter, settings),
        "message": "Ingestion complete.",
    }
