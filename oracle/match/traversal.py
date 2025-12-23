import asyncio
import logging
from typing import List, Dict, Optional
from oracle.match.level_selector import LevelSelector, LevelSelectionEntry, LevelSelection
from oracle.data.base import BaseOntology, OntologyNode
from oracle.extract.concept_extractor import ConceptSummary

logger = logging.getLogger(__name__)

class TraversalController:
    """Controls the traversal through the ontology hierarchy using BaseOntology."""

    def __init__(self, selector: LevelSelector, ontology: BaseOntology, max_concurrency: int = 5):
        self.selector = selector
        self.ontology = ontology
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def _aenrich_entries(self, entries: List[OntologyNode], path_so_far: List[str]):
        """Enrich a list of nodes with synonyms if a generator is available (async)."""
        if not hasattr(self.ontology, 'synonym_generator') or not self.ontology.synonym_generator:
            return

        path_str = " -> ".join(path_so_far)
        tasks = []
        
        async def _enriched_aget_synonyms(node):
            async with self.semaphore:
                return await self.ontology.synonym_generator.aget_synonyms(
                    code=node.code,
                    label=node.label,
                    description=node.description,
                    path=path_str
                )

        for node in entries:
            if not node.synonyms:
                tasks.append(_enriched_aget_synonyms(node))
            else:
                tasks.append(asyncio.sleep(0)) 

        results = await asyncio.gather(*tasks)
        for i, node in enumerate(entries):
            if not node.synonyms and results[i] is not None:
                node.synonyms = results[i]

    def _enrich_entries(self, entries: List[OntologyNode], path_so_far: List[str]):
        """Enrich a list of nodes with synonyms if a generator is available (sync)."""
        if not hasattr(self.ontology, 'synonym_generator') or not self.ontology.synonym_generator:
            return

        path_str = " -> ".join(path_so_far)
        for node in entries:
            if not node.synonyms:
                node.synonyms = self.ontology.synonym_generator.get_synonyms(
                    code=node.code,
                    label=node.label,
                    description=node.description,
                    path=path_str
                )

    async def atraverse(
        self, 
        concept_summary: ConceptSummary, 
        starting_depth: int = 1,
        langsmith_mode: bool = False,
        debug_mode: bool = False,
        depth_limit: int = 10,
    ) -> List[LevelSelectionEntry]:
        """Hierarchical traversal (async parallel)."""
        accumulated: List[LevelSelectionEntry] = []
        lock = asyncio.Lock()

        async def _atraverse(node_code: Optional[str], depth: int, path_so_far: List[str]):
            if depth > depth_limit:
                return
            
            if node_code is None:
                entries = self.ontology.get_roots()
                current_label = "Root"
            else:
                entries = self.ontology.get_children(node_code)
                node = self.ontology.get_node(node_code)
                current_label = node.label if node else node_code

            if not entries: return
            current_path = path_so_far + [current_label]
            await self._aenrich_entries(entries, current_path)

            level_selection: LevelSelection
            async with self.semaphore:
                level_selection = await self.selector.aselect_nodes(
                    concept_summary=concept_summary,
                    entries=entries,
                    depth=depth,
                    path_so_far=current_path,
                    langsmith_mode=langsmith_mode,
                    debug_mode=debug_mode,
                    file_name=node_code or "root"
                )

            if not level_selection.selected_codes: return
            async with lock: accumulated.extend(level_selection.selected_codes)

            node_map = {n.code: n for n in entries}
            descend_tasks = []
            for sel in level_selection.selected_codes:
                if sel.should_descend:
                    n = node_map.get(sel.code)
                    if n and n.has_children:
                        descend_tasks.append(_atraverse(sel.code, depth + 1, current_path))
            
            if descend_tasks: await asyncio.gather(*descend_tasks)

        await _atraverse(None, starting_depth, [])
        return accumulated

    def traverse(
        self, 
        concept_summary: ConceptSummary, 
        starting_depth: int = 1,
        langsmith_mode: bool = False,
        debug_mode: bool = False,
        depth_limit: int = 10,
    ) -> List[LevelSelectionEntry]:
        """Hierarchical traversal (sync sequential)."""
        accumulated: List[LevelSelectionEntry] = []

        def _traverse(node_code: Optional[str], depth: int, path_so_far: List[str]):
            if depth > depth_limit:
                return
            
            if node_code is None:
                entries = self.ontology.get_roots()
                current_label = "Root"
            else:
                entries = self.ontology.get_children(node_code)
                node = self.ontology.get_node(node_code)
                current_label = node.label if node else node_code

            if not entries: return
            current_path = path_so_far + [current_label]
            self._enrich_entries(entries, current_path)

            level_selection: LevelSelection = self.selector.select_nodes(
                concept_summary=concept_summary,
                entries=entries,
                depth=depth,
                path_so_far=current_path,
                langsmith_mode=langsmith_mode,
                debug_mode=debug_mode,
                file_name=node_code or "root"
            )

            if not level_selection.selected_codes: return
            accumulated.extend(level_selection.selected_codes)

            node_map = {n.code: n for n in entries}
            for sel in level_selection.selected_codes:
                if sel.should_descend:
                    n = node_map.get(sel.code)
                    if n and n.has_children:
                        _traverse(sel.code, depth + 1, current_path)

        _traverse(None, starting_depth, [])
        return accumulated
