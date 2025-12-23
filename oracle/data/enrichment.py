"""
Logic for enriching ontology nodes with LLM-generated synonyms.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger(__name__)

SYNONYM_PROMPT = ChatPromptTemplate.from_template(
    """
    You are an expert in Higher Education curriculum and ontologies.
    Your task is to generate a list of synonyms and related technical keywords for a specific ontology category.
    These keywords will be used to help match university module descriptions to this category.

    Ontology Category:
    Code: {code}
    Label: {label}
    Description: {description}

    Current Classification Path:
    {path}

    Generate 5 to 10 relevant, technical synonyms or related keywords that would likely appear in a module syllabus covering this topic.
    Avoid overly broad terms; focus on specific, distinguishing terminology.

    Return a JSON object exactly following this schema:
    {{
      "synonyms": ["<keyword_1>", "<keyword_2>", "..."]
    }}
    """
)

class SynonymResponse(BaseModel):
    synonyms: List[str] = Field(default_factory=list)

class SynonymGenerator:
    """Generates and caches synonyms for ontology nodes."""

    def __init__(self, llm: ChatOpenAI, cache_path: str):
        self.llm = llm
        self.cache_path = Path(cache_path)
        # Use structured output for robust synonym generation
        self.structured_llm = self.llm.with_structured_output(SynonymResponse)
        self.cache: Dict[str, List[str]] = self._load_cache()

    def _load_cache(self) -> Dict[str, List[str]]:
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load synonym cache: {e}")
        return {}

    def _save_cache(self):
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save synonym cache: {e}")

    async def aget_synonyms(self, code: str, label: str, description: str, path: str) -> List[str]:
        """Get synonyms from cache or generate them if missing (async)."""
        if code in self.cache:
            return self.cache[code]

        logger.info(f"Generating synonyms for node {code} ({label}) - async")
        try:
            prompt_with_inputs = await SYNONYM_PROMPT.ainvoke({
                "code": code,
                "label": label,
                "description": description,
                "path": path
            })
            result = await self.structured_llm.ainvoke(prompt_with_inputs)
            synonyms = result.synonyms
            self.cache[code] = synonyms
            self._save_cache()
            return synonyms
        except Exception as e:
            logger.error(f"Failed to generate synonyms for {code} (async): {e}")
            return []

    def get_synonyms(self, code: str, label: str, description: str, path: str) -> List[str]:
        """Get synonyms from cache or generate them if missing (sync)."""
        if code in self.cache:
            return self.cache[code]

        logger.info(f"Generating synonyms for node {code} ({label}) - sync")
        try:
            prompt_with_inputs = SYNONYM_PROMPT.invoke({
                "code": code,
                "label": label,
                "description": description,
                "path": path
            })
            result = self.structured_llm.invoke(prompt_with_inputs)
            synonyms = result.synonyms
            self.cache[code] = synonyms
            self._save_cache()
            return synonyms
        except Exception as e:
            logger.error(f"Failed to generate synonyms for {code} (sync): {e}")
            return []
