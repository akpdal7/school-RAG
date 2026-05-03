from llama_index.core import Settings as LlamaSettings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from rag_app.config import Settings
from rag_app.local_embeddings import LocalHashEmbedding
from rag_app.meshapi_llm import MeshAPILLM
from rag_app.usage import build_callback_manager


def configure_llama_index(settings: Settings, token_counter=None) -> None:
    settings.validate_runtime()
    LlamaSettings.llm = MeshAPILLM(
        model=settings.meshapi_llm_model,
        metadata_model=settings.llama_index_llm_model,
        api_key=settings.llm_api_key,
        api_base=settings.llm_api_base_url,
    )
    if settings.embedding_provider.lower() == "local_hash":
        LlamaSettings.embed_model = LocalHashEmbedding(dimensions=settings.local_hash_embedding_dim)
    elif settings.embedding_provider.lower() == "openai_compatible":
        LlamaSettings.embed_model = OpenAIEmbedding(
            model=settings.openai_embed_model,
            api_key=settings.llm_api_key,
            api_base=settings.llm_api_base_url,
        )
    else:
        raise ValueError("EMBEDDING_PROVIDER must be 'local_hash' or 'openai_compatible'.")
    LlamaSettings.chunk_size = settings.chunk_size
    LlamaSettings.chunk_overlap = settings.chunk_overlap
    callback_manager = build_callback_manager(token_counter)
    if callback_manager is not None:
        LlamaSettings.callback_manager = callback_manager


def get_qdrant_client(settings: Settings) -> QdrantClient:
    settings.validate_runtime()
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        timeout=60,
    )


def get_vector_store(settings: Settings) -> QdrantVectorStore:
    client = get_qdrant_client(settings)
    return QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection,
    )
