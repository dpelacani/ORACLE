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
        self.parser = JsonOutputParser(pydantic_object=FinalClassification)

    def make_chain(self, ontology_name: str) -> RunnableSequence:
        def _prepare_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
            concept_summary: ConceptSummary = inputs["concept_summary"]
            selected_entries: List[LevelSelectionEntry] = inputs["selected_entries"]
            selected_entries_json = json.dumps(
                [e.model_dump() for e in selected_entries], ensure_ascii=False
            )
            return {
                "ontology_name": ontology_name,
                "concept_summary_json": concept_summary.model_dump_json(),
                "selected_entries_json": selected_entries_json,
            }

        return RunnableSequence(
            _prepare_inputs,
            VERIFICATION_PROMPT | self.llm | self.parser,
        )

    def verify_selection(
        self, 
        concept_summary: ConceptSummary, 
        selected_entries: List[LevelSelectionEntry], 
        ontology_name: str,
        langsmith_mode: bool = False,
        debug_mode: bool = False,
    ) -> FinalClassification:
        """
        Check if the selected nodes are consistent and valid.
        
        Args:
            concept_summary: Extracted concept summary
            selected_entries: List of selected entries from traversal
            ontology_name: Name of the ontology being used
            langsmith_mode: If True, add LangSmith metadata for tracing
        """
        chain = self.make_chain(ontology_name)
        
        logger.info(f"Verifying {len(selected_entries)} selected entries")
        logger.info(f"\tInput: {len(selected_entries)} entries to verify")
        logger.info(f"\tOntology: {ontology_name}")
        
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
                    "depths": list(set(e.depth for e in selected_entries)),
                    "concept_summary_preview": {
                        "core_topics_count": len(concept_summary.core_topics),
                        "methods_count": len(concept_summary.methods),
                        "applications_count": len(concept_summary.applications),
                    }
                }
            }
            logger.info(f"Verifying {len(selected_entries)} selected entries with LangSmith metadata")
        
        
        logger.info(f"Invoking VERIFICATION_PROMPT")
        result = chain.invoke(
            {
                "concept_summary": concept_summary,
                "selected_entries": selected_entries
            },
            config=config
        )

        logger.info(f"{result}")
        final_classification = FinalClassification(**result)
        
        logger.info(f"Verification complete: {len(final_classification.selected_codes)} final codes, "
                    f"{len(final_classification.unmatched_topics)} unmatched topics")
        logger.info(f"Dropped codes:{set(e.code for e in selected_entries) - set(c.code for c in final_classification.selected_codes)}")
        logger.info(f"Verification Results:")
        logger.info(f"\tFinal codes selected: {len(final_classification.selected_codes)}")
        if final_classification.selected_codes:
            logger.info(f"\tCodes: {[c.code for c in final_classification.selected_codes]}")
        logger.info(f"\tUnmatched topics: {len(final_classification.unmatched_topics)}")
        if final_classification.unmatched_topics:
            logger.info(f"\tUnmatched: {[t.topic for t in final_classification.unmatched_topics[:5]]}...")

        return final_classification
