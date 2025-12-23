"""
LLM-based concept extraction logic.
"""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

from oracle.utils.prompts import CONCEPT_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

class ConceptSummary(BaseModel):
    module_title: Optional[str] = Field(default=None)
    core_topics: List[str] = Field(default_factory=list)
    methods: List[str] = Field(default_factory=list)
    applications: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)

class ConceptExtractor:
    """Extracts key concepts from curriculum text using an LLM."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        # Use with_structured_output for consistency and robustness
        self.structured_llm = self.llm.with_structured_output(ConceptSummary)

    async def aextract_concepts(
        self, 
        title: str,
        text: str, 
        langsmith_mode: bool = False,
        debug_mode: bool = False,
    ) -> ConceptSummary:
        """
        Extract a structured summary of concepts (async).
        """
        logger.info(f"Extracting concepts from text (length: {len(text)})")
        config = self._prepare_config(text, langsmith_mode)
        full_text = f"Module Title: {title}\n\nModule Description:\n{text}"

        logger.info(f"Invoking CONCEPT_EXTRACTION_PROMPT (async)")
        prompt_with_inputs = await CONCEPT_EXTRACTION_PROMPT.ainvoke(
            {
                "module_title": title,
                "module_description": full_text
            }
        )
        # Directly get the result model from structured output
        result = await self.structured_llm.ainvoke(prompt_with_inputs, config=config)
        return result

    def extract_concepts(
        self, 
        title: str,
        text: str, 
        langsmith_mode: bool = False,
        debug_mode: bool = False,
    ) -> ConceptSummary:
        """
        Extract a structured summary of concepts (sync).
        """
        logger.info(f"Extracting concepts from text (length: {len(text)})")
        config = self._prepare_config(text, langsmith_mode)
        full_text = f"Module Title: {title}\n\nModule Description:\n{text}"

        logger.info(f"Invoking CONCEPT_EXTRACTION_PROMPT (sync)")
        prompt_with_inputs = CONCEPT_EXTRACTION_PROMPT.invoke(
            {
                "module_title": title,
                "module_description": full_text
            }
        )
        result = self.structured_llm.invoke(prompt_with_inputs, config=config)
        return result

    def _prepare_config(self, text, langsmith_mode):
        config = {}
        if langsmith_mode:
            config = {
                "run_name": "concept_extraction",
                "tags": ["oracle", "extraction", "concept_extractor"],
                "metadata": {
                    "component": "ConceptExtractor",
                    "text_length": len(text),
                    "text_preview": text[:200] + "..." if len(text) > 200 else text
                }
            }
        return config
