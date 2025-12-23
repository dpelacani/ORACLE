"""
Final selection and consistency checks.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI

from oracle.utils.prompts import VERIFICATION_PROMPT
from oracle.extract.concept_extractor import ConceptSummary
from oracle.match.level_selector import LevelSelectionEntry

logger = logging.getLogger(__name__)

class FinalSelectedCode(BaseModel):
    code: str
    label: str
    depth: int
    matched_concepts: List[str]
    justification: str

class UnmatchedTopic(BaseModel):
    topic: str
    note: str
    nearest_code_candidate: Optional[str] = None

class FinalClassification(BaseModel):
    module_title: Optional[str]
    ontology_name: Optional[str]
    selected_codes: List[FinalSelectedCode]
    unmatched_topics: List[UnmatchedTopic]
    processing_reason: Optional[str] = None

class Verifier:
    """Verifies the selected classifications."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        # Use with_structured_output for robust JSON generation
        self.structured_llm = self.llm.with_structured_output(FinalClassification)

    def _prepare_final_inputs(self, concept_summary: ConceptSummary, selected_entries: List[LevelSelectionEntry], ontology_name: str) -> Dict[str, Any]:
        selected_entries_json = json.dumps(
            [e.model_dump() for e in selected_entries], ensure_ascii=False
        )
        return {
            "ontology_name": ontology_name,
            "concept_summary_json": concept_summary.model_dump_json(),
            "selected_entries_json": selected_entries_json,
        }

    async def averify_selection(
        self, 
        concept_summary: ConceptSummary, 
        selected_entries: List[LevelSelectionEntry], 
        ontology_name: str,
        langsmith_mode: bool = False,
        debug_mode: bool = False,
    ) -> FinalClassification:
        """
        Check if the selected nodes are consistent and valid (async).
        """
        inputs = self._prepare_final_inputs(concept_summary, selected_entries, ontology_name)
        config = self._prepare_config(selected_entries, ontology_name, langsmith_mode)
        
        logger.info(f"Invoking VERIFICATION_PROMPT (async)")
        # Chain verification prompt with structured output
        prompt_with_inputs = await VERIFICATION_PROMPT.ainvoke(inputs)
        result = await self.structured_llm.ainvoke(prompt_with_inputs, config=config)
        return result

    def verify_selection(
        self, 
        concept_summary: ConceptSummary, 
        selected_entries: List[LevelSelectionEntry], 
        ontology_name: str,
        langsmith_mode: bool = False,
        debug_mode: bool = False,
    ) -> FinalClassification:
        """
        Check if the selected nodes are consistent and valid (sync).
        """
        inputs = self._prepare_final_inputs(concept_summary, selected_entries, ontology_name)
        config = self._prepare_config(selected_entries, ontology_name, langsmith_mode)
        
        logger.info(f"Invoking VERIFICATION_PROMPT (sync)")
        prompt_with_inputs = VERIFICATION_PROMPT.invoke(inputs)
        result = self.structured_llm.invoke(prompt_with_inputs, config=config)
        return result

    def _prepare_config(self, selected_entries, ontology_name, langsmith_mode):
        config = {}
        if langsmith_mode:
            config = {
                "run_name": "verification",
                "tags": ["oracle", "verification", "verifier"],
                "metadata": {
                    "component": "Verifier",
                    "ontology_name": ontology_name,
                    "num_selected_entries": len(selected_entries),
                    "selected_codes": [e.code for e in selected_entries],
                }
            }
        return config
