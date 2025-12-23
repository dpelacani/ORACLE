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
        self.parser = JsonOutputParser(pydantic_object=ConceptSummary)
        self.chain = CONCEPT_EXTRACTION_PROMPT | self.llm.with_retry() | self.parser

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
        result = await self.chain.ainvoke(
            {
                "module_title": title,
                "module_description": full_text
            },
            config=config
        )
        return ConceptSummary(**result)

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
        result = self.chain.invoke(
            {
                "module_title": title,
                "module_description": full_text
            },
            config=config
        )
        return ConceptSummary(**result)

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
