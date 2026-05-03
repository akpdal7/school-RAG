from llama_index.core import VectorStoreIndex

from rag_app.config import Settings
from rag_app.qdrant_store import configure_llama_index, get_vector_store
from rag_app.usage import build_token_counter, summarize_usage


def answer_question(question: str, settings: Settings, top_k: int | None = None) -> dict:
    token_counter = build_token_counter(settings)
    configure_llama_index(settings, token_counter)
    vector_store = get_vector_store(settings)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    query_engine = index.as_query_engine(
        similarity_top_k=top_k or settings.similarity_top_k,
        response_mode="compact",
    )
    response = query_engine.query(question)

    sources = []
    for node in response.source_nodes:
        metadata = dict(node.node.metadata or {})
        sources.append(
            {
                "score": node.score,
                "file_name": metadata.get("file_name"),
                "file_path": metadata.get("file_path"),
                "page_label": metadata.get("page_label"),
                "text": node.node.get_content(metadata_mode="none")[:700],
            }
        )

    return {
        "answer": str(response),
        "sources": sources,
        "usage": summarize_usage(token_counter, settings),
    }
