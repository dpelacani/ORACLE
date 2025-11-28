"""
Central configuration for the ORACLE package.
"""

import os
from dataclasses import dataclass
from typing import Optional

from langchain_openai import ChatOpenAI

@dataclass
class Config:
    """Configuration settings for ORACLE."""
    ontology_path: str = "ontology/msc"
    llm_model: str = "gpt-4.1-mini"
    llm_temperature: float = 0.0
    log_level: str = "INFO"
    api_key: str = os.getenv("OPENAI_API_KEY")
    base_url: str = os.getenv("OPENAI_BASE_URL")
    langsmith_project: Optional[str] = os.getenv("LANGCHAIN_PROJECT", "oracle-classification")
    langsmith_api_key: Optional[str] = os.getenv("LANGCHAIN_API_KEY")

    @classmethod
    def load_from_env(cls, ontology_path: str = "ontology/msc"):
        """Load configuration from environment variables."""
        return cls(
            ontology_path=ontology_path,
            llm_model=os.getenv("ORACLE_LLM_MODEL", "gpt-4.1-mini"),
            llm_temperature=float(os.getenv("ORACLE_LLM_TEMPERATURE", "0.0")),
            log_level=os.getenv("ORACLE_LOG_LEVEL", "INFO"),
            langsmith_project=os.getenv("LANGCHAIN_PROJECT", "oracle-classification"),
            langsmith_api_key=os.getenv("LANGCHAIN_API_KEY")
        )

    @classmethod
    def load_from_args(cls, **kwargs):
        """Load configuration from command line arguments."""
        return cls(
            ontology_path=kwargs.get("ontology_path", "ontology/msc"),
            llm_model=kwargs.get("llm_model", "gpt-4.1-mini"),
            llm_temperature=kwargs.get("llm_temperature", 0.0),
            log_level=kwargs.get("log_level", "INFO"),
            api_key=kwargs.get("api_key", os.getenv("OPENAI_API_KEY")),
            base_url=kwargs.get("base_url", os.getenv("OPENAI_BASE_URL")),
            langsmith_project=kwargs.get("langsmith_project", os.getenv("LANGCHAIN_PROJECT", "oracle-classification")),
            langsmith_api_key=kwargs.get("langsmith_api_key", os.getenv("LANGCHAIN_API_KEY"))
        )

    def get_llm(self) -> ChatOpenAI:
        """Get the configured LLM instance."""
        return ChatOpenAI(
            model=self.llm_model,
            temperature=self.llm_temperature,
            api_key=self.api_key,
            base_url=self.base_url,
        )
