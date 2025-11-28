"""
LLM selection per ontology level.
"""

import json
import logging
from typing import List, Dict, Any
from pydantic import BaseModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI

from oracle.utils.prompts import LEVEL_SELECTION_PROMPT
from oracle.data.ontology_loader import OntologyEntry
from oracle.extract.concept_extractor import ConceptSummary

logger = logging.getLogger(__name__)

class LevelSelectionEntry(BaseModel):
    code: str
    label: str
    depth: int
    matched_concepts: List[str]
    justification: str
    should_descend: bool

class LevelSelection(BaseModel):
    selected_entries: List[LevelSelectionEntry]

class LevelSelector:
    """Selects relevant ontology nodes at a specific level."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.parser = JsonOutputParser(pydantic_object=LevelSelection)

    def make_chain(self, depth: int) -> RunnableSequence:
        """Build a Runnable that selects entries at a given depth."""
        
        def _prepare_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
            concept_summary: ConceptSummary = inputs["concept_summary"]
            entries: List[OntologyEntry] = inputs["entries"]

            entries_json = [
                {
                    "code": e.code,
                    "label": e.label,
                    "description": e.description,
                }
                for e in entries
            ]

            return {
                "depth": depth,
                "concept_summary_json": concept_summary.model_dump_json(),
                "ontology_entries_json": json.dumps(
                    entries_json, ensure_ascii=False
                ),
            }

        return RunnableSequence(
            _prepare_inputs,
            LEVEL_SELECTION_PROMPT | self.llm | self.parser,
        )

    def select_nodes(
        self, 
        concept_summary: ConceptSummary, 
        entries: List[OntologyEntry], 
        depth: int,
        langsmith_mode: bool = False,
        file_name: str = None
    ) -> LevelSelection:
        """
        Select the most relevant candidate nodes for the given concepts.
        
        Args:
            concept_summary: Extracted concept summary
            entries: List of ontology entries at this level
            depth: Current depth in the ontology hierarchy
            langsmith_mode: If True, add LangSmith metadata for tracing
            file_name: Optional ontology file name for debugging context
        """
        chain = self.make_chain(depth)
        
        config = {}
        if langsmith_mode:
            config = {
                "run_name": f"level_selection_depth_{depth}",
                "tags": ["oracle", "selection", "level_selector", f"depth_{depth}"],
                "metadata": {
                    "component": "LevelSelector",
                    "depth": depth,
                    "num_entries": len(entries),
                    "file_name": file_name or "unknown",
                    "entry_codes": [e.code for e in entries[:10]],  # First 10 codes
                    "concept_summary_preview": {
                        "core_topics_count": len(concept_summary.core_topics),
                        "methods_count": len(concept_summary.methods),
                        "applications_count": len(concept_summary.applications),
                    }
                }
            }
            logger.debug(f"Selecting nodes at depth {depth} with LangSmith metadata")


        logging.info(f"Invoking LEVEL_SELECTION_PROMPT")
        result = chain.invoke(
            {
                "concept_summary": concept_summary,
                "entries": entries
            },
            config=config
        )
        
        return LevelSelection(**result)
