from dataclasses import asdict, dataclass

import tiktoken
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler

from rag_app.config import Settings


@dataclass
class UsageSummary:
    llm_input_tokens: int
    llm_output_tokens: int
    embedding_tokens: int
    estimated_llm_cost_usd: float
    estimated_embedding_cost_usd: float
    estimated_total_cost_usd: float
    pricing_note: str


def build_token_counter(settings: Settings) -> TokenCountingHandler:
    try:
        encoding = tiktoken.encoding_for_model(settings.openai_llm_model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return TokenCountingHandler(tokenizer=encoding.encode)


def build_callback_manager(token_counter: TokenCountingHandler | None) -> CallbackManager | None:
    if token_counter is None:
        return None
    return CallbackManager([token_counter])


def summarize_usage(token_counter: TokenCountingHandler, settings: Settings) -> dict:
    llm_input_tokens = token_counter.prompt_llm_token_count
    llm_output_tokens = token_counter.completion_llm_token_count
    embedding_tokens = token_counter.total_embedding_token_count

    estimated_llm_cost = (
        llm_input_tokens * settings.llm_input_price_per_1m
        + llm_output_tokens * settings.llm_output_price_per_1m
    ) / 1_000_000
    estimated_embedding_cost = embedding_tokens * settings.embedding_price_per_1m / 1_000_000
    estimated_total_cost = estimated_llm_cost + estimated_embedding_cost

    summary = UsageSummary(
        llm_input_tokens=llm_input_tokens,
        llm_output_tokens=llm_output_tokens,
        embedding_tokens=embedding_tokens,
        estimated_llm_cost_usd=round(estimated_llm_cost, 8),
        estimated_embedding_cost_usd=round(estimated_embedding_cost, 8),
        estimated_total_cost_usd=round(estimated_total_cost, 8),
        pricing_note=(
            "Estimated from local token counts and configured per-1M-token prices. "
            "Check MeshAPI for authoritative LLM credits. Local FastEmbed embeddings do not use API credits."
        ),
    )
    return asdict(summary)
