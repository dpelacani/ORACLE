"""
Hierarchical selective traversal controller.
"""

import logging
from typing import List, Dict
from oracle.match.level_selector import LevelSelector, LevelSelectionEntry, LevelSelection
from oracle.data.ontology_loader import OntologyLoader, OntologyEntry
from oracle.extract.concept_extractor import ConceptSummary

logger = logging.getLogger(__name__)

class TraversalController:
    """Controls the traversal through the ontology hierarchy."""

    def __init__(self, selector: LevelSelector, loader: OntologyLoader):
        self.selector = selector
        self.loader = loader

    def traverse(
        self, 
        concept_summary: ConceptSummary, 
        root_file: str, 
        starting_depth: int = 1,
        langsmith_mode: bool = False,
        depth_limit: int = 10,
    ) -> List[LevelSelectionEntry]:
        """
        Perform hierarchical traversal:
        - start from root_file;
        - at each level, the LLM selects relevant entries and says whether to descend;
        - only branches with should_descend=True and non-null child_file are explored.
        Returns all selected entries across all levels.
        
        Args:
            concept_summary: Extracted concept summary
            root_file: Starting ontology file
            starting_depth: Initial depth level
            langsmith_mode: If True, enable LangSmith metadata
        """
        accumulated: List[LevelSelectionEntry] = []
        traversal_path = []  # Track traversal for debugging

        logger.info(f"Starting traversal from: {root_file} (depth {starting_depth})")

        def _traverse(file_name: str, depth: int):
            nonlocal accumulated, traversal_path

            if depth > depth_limit:
                logger.info(f"\t[Depth {depth}] Reached depth limit ({depth_limit}). Stopping traversal.")
                return

            # logger.info(f"Traversing: file={file_name}, depth={depth}")
            logger.info(f"\t[Depth {depth}] Loading: {file_name}")
            traversal_path.append({"file": file_name, "depth": depth})

            entries = self.loader.load_ontology_level(file_name)
            if not entries:
                logger.info(f"\t[Depth {depth}] No entries found in {file_name}. Exiting traversal.")
                return

            logger.info(f"\t[Depth {depth}] Loaded {len(entries)} entries")

            level_selection: LevelSelection = self.selector.select_nodes(
                concept_summary=concept_summary,
                entries=entries,
                depth=depth,
                langsmith_mode=langsmith_mode,
                file_name=file_name
            )

            if not level_selection.selected_entries:
                logger.info(f"\t[Depth {depth}] No entries selected. Exiting traversal of {file_name}")
                return

            selected_codes = [e.code for e in level_selection.selected_entries]
            logger.info(f"\t[Depth {depth}] Selected {len(level_selection.selected_entries)} entries: {selected_codes}")

            accumulated.extend(level_selection.selected_entries)

            # Descend only into branches that are both selected and flagged for descent
            # and that have a valid child_file
            entry_by_code: Dict[str, OntologyEntry] = {e.code: e for e in entries}
            branches_to_descend = []

            for sel in level_selection.selected_entries:
                if not sel.should_descend:
                    logger.info(f"\t\tNot descending into {sel.code}: should_descend=False")
                    continue
                e = entry_by_code.get(sel.code)
                if e is None:
                    logger.info(f"\t\tEntry {sel.code} not found in entry_by_code")
                    continue
                if e.child_file is None or e.child_file in ("", "None"):
                    logger.info(f"\t\tEntry {sel.code} has no child_file")
                    continue
                branches_to_descend.append((sel.code, e.child_file))

            if branches_to_descend:
                logger.info(f"\t[Depth {depth}] Descending into {len(branches_to_descend)} "
                            f"branches: {[f'{code}->{file}' for code, file in branches_to_descend]}")

            for code, child_file in branches_to_descend:
                _traverse(file_name=child_file, depth=depth + 1)

        _traverse(file_name=root_file, depth=starting_depth)
        
        logger.info(f"Traversal complete: {len(accumulated)} total entries selected")
        logger.info(f"\tTraversal path: {traversal_path}")
        logger.info(f"\tTotal entries selected: {len(accumulated)}")
        if accumulated:
            logger.info(f"\tSelected codes: {[e.code for e in accumulated]}")
        
        return accumulated
