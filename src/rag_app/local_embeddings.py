import hashlib
import math
import re

from llama_index.core.embeddings import BaseEmbedding
from pydantic import Field


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")


class LocalHashEmbedding(BaseEmbedding):
    """Small dependency-free embedding model for local demos.

    This is not as semantically rich as a hosted embedding model, but it is stable,
    local, Python 3.13 friendly, and good enough to prove the full RAG pipeline.
    """

    model_name: str = "local-hash-embedding"
    dimensions: int = Field(default=384, gt=0)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, byteorder="big", signed=False)
            index = value % self.dimensions
            sign = 1.0 if (value >> 63) == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._embed(query)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._embed(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._embed(text)

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

