from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    mesh_api_key: str = Field(default="", alias="MESH_API_KEY")
    mesh_api_base_url: str = Field(default="https://api.meshapi.ai/v1", alias="MESH_API_BASE_URL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    qdrant_url: str = Field(default="", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="rag_demo", alias="QDRANT_COLLECTION")

    openai_llm_model: str = Field(default="gpt-4o-mini", alias="OPENAI_LLM_MODEL")
    embedding_provider: str = Field(default="local_hash", alias="EMBEDDING_PROVIDER")
    openai_embed_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBED_MODEL")
    fastembed_model_name: str = Field(default="BAAI/bge-small-en-v1.5", alias="FASTEMBED_MODEL_NAME")
    local_hash_embedding_dim: int = Field(default=384, alias="LOCAL_HASH_EMBEDDING_DIM")

    chunk_size: int = Field(default=1024, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=128, alias="CHUNK_OVERLAP")
    similarity_top_k: int = Field(default=5, alias="SIMILARITY_TOP_K")

    llm_input_price_per_1m: float = Field(default=0.15, alias="LLM_INPUT_PRICE_PER_1M")
    llm_output_price_per_1m: float = Field(default=0.60, alias="LLM_OUTPUT_PRICE_PER_1M")
    embedding_price_per_1m: float = Field(default=0.0, alias="EMBEDDING_PRICE_PER_1M")

    gmail_credentials_file: str = Field(default="data/secrets/gmail_credentials.json", alias="GMAIL_CREDENTIALS_FILE")
    gmail_token_file: str = Field(default="data/secrets/gmail_token.json", alias="GMAIL_TOKEN_FILE")
    gmail_json_output_folder: str = Field(default="data/gmail_json", alias="GMAIL_JSON_OUTPUT_FOLDER")
    zapier_ingest_secret: str = Field(default="", alias="ZAPIER_INGEST_SECRET")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def validate_runtime(self) -> None:
        missing = []
        if not self.llm_api_key:
            missing.append("MESH_API_KEY")
        if not self.qdrant_url:
            missing.append("QDRANT_URL")
        if not self.qdrant_api_key:
            missing.append("QDRANT_API_KEY")
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"Missing required environment variable(s): {joined}")

    @property
    def llm_api_key(self) -> str:
        return self.mesh_api_key or self.openai_api_key

    @property
    def llm_api_base_url(self) -> str:
        base_url = self.mesh_api_base_url.rstrip("/")
        if base_url == "https://api.meshapi.ai":
            return "https://api.meshapi.ai/v1"
        return base_url

    @property
    def llama_index_llm_model(self) -> str:
        if self.openai_llm_model.startswith("openai/"):
            return self.openai_llm_model.removeprefix("openai/")
        return self.openai_llm_model

    @property
    def meshapi_llm_model(self) -> str:
        if "/" in self.openai_llm_model:
            return self.openai_llm_model
        if self.openai_llm_model.startswith(("gpt-", "o1", "o3", "o4")):
            return f"openai/{self.openai_llm_model}"
        return self.openai_llm_model


@lru_cache
def get_settings() -> Settings:
    return Settings()
