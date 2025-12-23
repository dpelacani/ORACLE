"""
Hierarchical selective traversal controller.
"""

import logging
from typing import List, Dict, Optional
from oracle.match.level_selector import LevelSelector, LevelSelectionEntry, LevelSelection
from oracle.data.base import BaseOntology, OntologyNode
from oracle.extract.concept_extractor import ConceptSummary

logger = logging.getLogger(__name__)

class TraversalController:
    """Controls the traversal through the ontology hierarchy using BaseOntology."""

    def __init__(self, selector: LevelSelector, ontology: BaseOntology):
        self.selector = selector
        self.ontology = ontology

    def traverse(
        self, 
        concept_summary: ConceptSummary, 
        starting_depth: int = 1,
        langsmith_mode: bool = False,
        debug_mode: bool = False,
        depth_limit: int = 10,
    ) -> List[LevelSelectionEntry]:
        """
        Perform hierarchical traversal:
        - start from ontology roots;
        - at each level, the LLM selects relevant entries and says whether to descend;
        - only branches with should_descend=True and has_children=True are explored.
        Returns all selected entries across all levels.
        """
        accumulated: List[LevelSelectionEntry] = []
        traversal_path = []

        logger.info(f"Starting traversal (depth {starting_depth})")

        def _traverse(node_code: Optional[str], depth: int):
            nonlocal accumulated, traversal_path

            if depth > depth_limit:
                logger.info(f"\t[Depth {depth}] Reached depth limit ({depth_limit}). Stopping traversal.")
                return

            # If node_code is None, we are at the root level
            if node_code is None:
                logger.info(f"\t[Depth {depth}] Loading roots")
                entries = self.ontology.get_roots()
                current_id = "root"
            else:
                logger.info(f"\t[Depth {depth}] Loading children for: {node_code}")
                entries = self.ontology.get_children(node_code)
                current_id = node_code

            if not entries:
                logger.info(f"\t[Depth {depth}] No entries found for {current_id}. Exiting branch.")
                return

            traversal_path.append({"code": current_id, "depth": depth})
            logger.info(f"\t[Depth {depth}] Loaded {len(entries)} entries")

            # Map OntologyNode to a format level_selector understands if needed
            # Currently LevelSelector uses the entries directly. 
            # We ensure MSCOntology.get_children returns LevelSelector compatible objects.
            level_selection: LevelSelection = self.selector.select_nodes(
                concept_summary=concept_summary,
                entries=entries,
                depth=depth,
                langsmith_mode=langsmith_mode,
                debug_mode=debug_mode,
                file_name=current_id # passing code as file_name for now
            )

            if not level_selection.selected_entries:
                logger.info(f"\t[Depth {depth}] No entries selected. Exiting branch {current_id}")
                return

            selected_codes = [e.code for e in level_selection.selected_entries]
            logger.info(f"\t[Depth {depth}] Selected {len(level_selection.selected_entries)} entries: {selected_codes}")

            accumulated.extend(level_selection.selected_entries)

            # Map nodes for quick lookup
            node_map: Dict[str, OntologyNode] = {n.code: n for n in entries}
            
            for sel in level_selection.selected_entries:
                if not sel.should_descend:
                    continue
                
                node = node_map.get(sel.code)
                if node and node.has_children:
                    logger.info(f"\t[Depth {depth}] Descending into {sel.code}")
                    _traverse(node_code=sel.code, depth=depth + 1)
                else:
                    logger.info(f"\t[Depth {depth}] Entry {sel.code} has no children to descend into")

        # Initial call with None to start from roots
        _traverse(node_code=None, depth=starting_depth)
        
        logger.info(f"Traversal complete: {len(accumulated)} total entries selected")
        return accumulated
