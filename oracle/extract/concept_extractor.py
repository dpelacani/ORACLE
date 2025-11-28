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
        self.chain = CONCEPT_EXTRACTION_PROMPT | self.llm | self.parser

    def extract_concepts(
        self, 
        title: str,
        text: str, 
        langsmith_mode: bool = False,
    ) -> ConceptSummary:
        """
        Extract a structured summary of concepts from the provided text.
        
        Args:
            title: Module title
            text: Module description text
            langsmith_mode: If True, add LangSmith metadata for tracing
        """
        logger.info(f"Extracting concepts from text (length: {len(text)})")
        logger.info(f"  Input text length: {len(text)} characters")

        
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
            logger.info(f"Extracting concepts with LangSmith metadata: {config}")
        
        
        text = f"Module Title: {title}\n\nModule Description:\n{text}"


        logging.info(f"Invoking CONCEPT_EXTRACTION_PROMPT")
        result = self.chain.invoke(
            {
                "module_title": title,
                "module_description": text
            },
            config=config
        )
        
        concept_summary = ConceptSummary(**result)
        
        logger.info(f"Extraction complete: {len(concept_summary.core_topics)} topics, "
                    f"{len(concept_summary.methods)} methods, "
                    f"{len(concept_summary.applications)} applications, "
                    f"{len(concept_summary.skills)} skills/outcomes")
        logger.info(f"Extracted Concepts:")
        logger.info(f"\tCore Topics ({len(concept_summary.core_topics)}): {concept_summary.core_topics}")
        logger.info(f"\tMethods ({len(concept_summary.methods)}): {concept_summary.methods}")
        logger.info(f"\tApplications ({len(concept_summary.applications)}): {concept_summary.applications}")
        logger.info(f"\tSkills/Outcomes ({len(concept_summary.skills)}): {concept_summary.skills}")
        
        return concept_summary
