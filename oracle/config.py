import os
import logging
from pathlib import Path
from typing import Optional, Any, Dict, List, Tuple
from pydantic_settings import (
    BaseSettings, 
    SettingsConfigDict, 
    PydanticBaseSettingsSource,
    EnvSettingsSource
)
from pydantic import Field, AliasChoices
from langchain_openai import ChatOpenAI

# Get project root (where .env should be)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

class OracleEnvSource(EnvSettingsSource):
    """Custom source to prioritize ORACLE_ prefixed variables even over shell OPENAI_ vars."""
    def prepare_field_value(self, field_name: str, field: Any, value: Any, value_is_complex: bool) -> Any:
        # Pydantic's EnvSettingsSource already handles Aliases, but we can 
        # double check for ORACLE_ specific overrides here if needed.
        return super().prepare_field_value(field_name, field, value, value_is_complex)

class Settings(BaseSettings):
    """Configuration settings for ORACLE using Pydantic Settings."""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # LLM Configuration
    # Note: AliasChoices priority is Left-to-Right.
    api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("ORACLE_API_KEY", "OPENAI_API_KEY")
    )
    base_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("ORACLE_BASE_URL", "OPENAI_BASE_URL")
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("ORACLE_LLM_MODEL", "LLM_MODEL")
    )
    llm_temperature: float = Field(
        default=0.0,
        validation_alias=AliasChoices("ORACLE_LLM_TEMPERATURE", "LLM_TEMPERATURE")
    )
    request_timeout: int = Field(
        default=60,
        validation_alias=AliasChoices("ORACLE_REQUEST_TIMEOUT", "REQUEST_TIMEOUT")
    )
    max_retries: int = Field(
        default=3,
        validation_alias=AliasChoices("ORACLE_MAX_RETRIES", "MAX_RETRIES")
    )

    # Package Configuration
    ontology_path: str = Field(
        default="ontology/msc",
        validation_alias=AliasChoices("ORACLE_ONTOLOGY_PATH", "ONTOLOGY_PATH")
    )
    log_level: str = Field(
        default="INFO",
        validation_alias=AliasChoices("ORACLE_LOG_LEVEL", "LOG_LEVEL")
    )

    # LangSmith Configuration
    langchain_tracing_v2: bool = Field(
        default=False,
        validation_alias=AliasChoices("ORACLE_LANGCHAIN_TRACING_V2", "LANGCHAIN_TRACING_V2")
    )
    langchain_project: str = Field(
        default="oracle-classification",
        validation_alias=AliasChoices("ORACLE_LANGCHAIN_PROJECT", "LANGCHAIN_PROJECT")
    )
    langchain_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("ORACLE_LANGCHAIN_API_KEY", "LANGCHAIN_API_KEY")
    )
    langchain_endpoint: str = Field(
        default="https://api.smith.langchain.com",
        validation_alias=AliasChoices("ORACLE_LANGCHAIN_ENDPOINT", "LANGCHAIN_ENDPOINT")
    )

    @classmethod
    def settings_customise_sources(
        cls,
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Priority: Init > Dotenv (.env file) > Env (System Shell) > Default
        # This allows the .env file to override "poisoned" shell variables.
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    def get_llm(self) -> ChatOpenAI:
        """Get the configured LLM instance."""
        return ChatOpenAI(
            model=self.llm_model,
            temperature=self.llm_temperature,
            api_key=self.api_key,
            base_url=self.base_url,
            request_timeout=self.request_timeout,
        )

    def debug_dump(self) -> dict:
        """Return setting values for debugging with sensitive keys masked."""
        dump = {}
        for field_name in self.model_fields:
            if field_name.startswith("_"):
                continue
            val = getattr(self, field_name)
            if field_name in ["api_key", "langchain_api_key"] and val:
                val = "****" + str(val)[-4:]
            dump[field_name] = val
        return dump

