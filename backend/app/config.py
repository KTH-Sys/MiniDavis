"""Server-only settings; importing the baseline never contacts a model provider."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    minidavis_mode: Literal["baseline", "llm"] = "baseline"
    llm_provider: Literal["groq"] = "groq"
    llm_model: str = "qwen/qwen3.8-27b"
    llm_api_key: SecretStr = SecretStr("")
    llm_timeout_seconds: int = Field(default=20, gt=0)
    llm_min_agent_replan_seconds: int = Field(default=30, gt=0)
    llm_max_requests_per_minute: int = Field(default=4, gt=0)
    llm_max_calls_per_run: int = Field(default=20, gt=0)
    llm_max_calls_per_day: int = Field(default=500, gt=0)
    llm_max_tokens_per_day: int = Field(default=160000, gt=0)
    llm_max_input_tokens: int = Field(default=800, ge=256)
    llm_max_completion_tokens: int = Field(default=512, gt=0)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_revision: str = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
    memory_retrieval_mode: Literal["lexical", "semantic"] = "lexical"
    embedding_cache_path: str = "data/model-cache"
    classifier_model_path: str = "ml/artifacts/classifier"
    memory_db_path: str = "data/minidavis.sqlite"
    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]
