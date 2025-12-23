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
from oracle.data.base import OntologyNode
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
    selected_codes: List[LevelSelectionEntry]

class LevelSelector:
    """Selects relevant ontology nodes at a specific level."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        # Use with_structured_output for robust JSON generation
        self.structured_llm = self.llm.with_structured_output(LevelSelection)

    def _prepare_level_inputs(self, concept_summary: ConceptSummary, entries: List[OntologyNode], depth: int, path_so_far: List[str]) -> Dict[str, Any]:
        entries_json = [
            {
                "code": e.code,
                "label": e.label,
                "description": e.description,
                "synonyms": e.synonyms,
            }
            for e in entries
        ]

        return {
            "depth": depth,
            "path_so_far": " -> ".join(path_so_far),
            "concept_summary_json": concept_summary.model_dump_json(),
            "ontology_entries_json": json.dumps(
                entries_json, ensure_ascii=False
            ),
        }

    async def aselect_nodes(
        self, 
        concept_summary: ConceptSummary, 
        entries: List[OntologyNode], 
        depth: int,
        path_so_far: List[str] = [],
        langsmith_mode: bool = False,
        debug_mode: bool = False,
        file_name: str = None
    ) -> LevelSelection:
        """
        Select the most relevant candidate nodes (async).
        """
        inputs = self._prepare_level_inputs(concept_summary, entries, depth, path_so_far)
        config = self._prepare_config(depth, entries, concept_summary, langsmith_mode, file_name)
        
        logger.info(f"Invoking LEVEL_SELECTION_PROMPT (async)")
        # Chain via prompt invocation then structured output
        prompt_with_inputs = await LEVEL_SELECTION_PROMPT.ainvoke(inputs)
        result = await self.structured_llm.ainvoke(prompt_with_inputs, config=config)
        return result

    def select_nodes(
        self, 
        concept_summary: ConceptSummary, 
        entries: List[OntologyNode], 
        depth: int,
        path_so_far: List[str] = [],
        langsmith_mode: bool = False,
        debug_mode: bool = False,
        file_name: str = None
    ) -> LevelSelection:
        """
        Select the most relevant candidate nodes (sync).
        """
        inputs = self._prepare_level_inputs(concept_summary, entries, depth, path_so_far)
        config = self._prepare_config(depth, entries, concept_summary, langsmith_mode, file_name)
        
        logger.info(f"Invoking LEVEL_SELECTION_PROMPT (sync)")
        prompt_with_inputs = LEVEL_SELECTION_PROMPT.invoke(inputs)
        result = self.structured_llm.invoke(prompt_with_inputs, config=config)
        return result

    def _prepare_config(self, depth, entries, concept_summary, langsmith_mode, file_name):
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
                    "entry_codes": [e.code for e in entries[:10]],
                    "concept_summary_preview": {
                        "core_topics_count": len(concept_summary.core_topics),
                        "methods_count": len(concept_summary.methods),
                        "applications_count": len(concept_summary.applications),
                    }
                }
            }
        return config
