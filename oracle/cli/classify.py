"""
CLI entry point for running classifications.
"""

import argparse
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import List, Optional

from oracle.config import Settings
from oracle.data.base import BaseOntology
from oracle.data.enrichment import SynonymGenerator
from oracle.extract.concept_extractor import ConceptExtractor
from oracle.match.level_selector import LevelSelector
from oracle.match.traversal import TraversalController
from oracle.verify.verifier import Verifier, FinalClassification
from oracle.utils.logging import setup_logging

logger = logging.getLogger(__name__)

async def classify_module(
    title: str,
    description: str,
    ontology: BaseOntology,
    config: Settings,
    use_async: bool = True,
    langsmith_mode: bool = False,
    debug_mode: bool = False,
    starting_depth: int = 1,
    depth_limit: int = 10
) -> FinalClassification:
    """
    Main orchestration logic for classifying a module.
    """
    # Initialize components
    llm = config.get_llm()
    
    # Task 3: Initialize SynonymGenerator if supported by the ontology
    if hasattr(ontology, 'synonym_generator') and not ontology.synonym_generator:
        cache_path = Path("ontology/msc/synonyms_cache.json")
        ontology.synonym_generator = SynonymGenerator(llm, str(cache_path))

    extractor = ConceptExtractor(llm)
    selector = LevelSelector(llm)
    controller = TraversalController(selector, ontology)
    verifier = Verifier(llm)

    if use_async:
        # ASYNC MODE
        print("\nRunning in ASYNC mode...")
        # 1. Extract concepts
        print("\nSTEP 1: Extracting concepts (async)...")
        concept_summary = await extractor.aextract_concepts(
            title=title, 
            text=description, 
            langsmith_mode=langsmith_mode,
            debug_mode=debug_mode
        )

        # 2. Traverse ontology
        print("\nSTEP 2: Traversing ontology (async parallel)...")
        selected_entries = await controller.atraverse(
            concept_summary=concept_summary,
            langsmith_mode=langsmith_mode,
            debug_mode=debug_mode,
            starting_depth=starting_depth,
            depth_limit=depth_limit
        )

        # 3. Verify selection
        print(f"\nSTEP 3: Verifying {len(selected_entries)} selected entries (async)...")
        final_classification = await verifier.averify_selection(
            concept_summary=concept_summary,
            selected_entries=selected_entries,
            ontology_name="MSC2020",
            langsmith_mode=langsmith_mode,
            debug_mode=debug_mode
        )
    else:
        # SYNC MODE
        print("\nRunning in SYNC mode...")
        # 1. Extract concepts
        print("\nSTEP 1: Extracting concepts (sync)...")
        concept_summary = extractor.extract_concepts(
            title=title, 
            text=description, 
            langsmith_mode=langsmith_mode,
            debug_mode=debug_mode
        )

        # 2. Traverse ontology
        print("\nSTEP 2: Traversing ontology (sync sequential)...")
        selected_entries = controller.traverse(
            concept_summary=concept_summary,
            langsmith_mode=langsmith_mode,
            debug_mode=debug_mode,
            starting_depth=starting_depth,
            depth_limit=depth_limit
            
        )

        # 3. Verify selection
        print(f"STEP 3: Verifying {len(selected_entries)} selected entries (sync)...")
        final_classification = verifier.verify_selection(
            concept_summary=concept_summary,
            selected_entries=selected_entries,
            ontology_name="MSC2020",
            langsmith_mode=langsmith_mode,
            debug_mode=debug_mode
        )

    return final_classification

def main():
    """CLI entry point for classification."""
    parser = argparse.ArgumentParser(description="ORACLE Classification CLI")
    
    parser.add_argument("--title", help="Module title")
    parser.add_argument("--description", help="Module description")
    parser.add_argument("--ontology-path", default="ontology/msc/MSC_2020.csv", help="Path to the ontology CSV file")
    parser.add_argument("--langsmith", action="store_true", help="Enable LangSmith tracing")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--no-async", action="store_true", help="Disable asynchronous execution (for debugging)")
    parser.add_argument("--starting-depth", type=int, default=1, help="Depth to start traversal at")
    parser.add_argument("--depth-limit", type=int, default=10, help="Maximum depth to traverse")

    args = parser.parse_args()

    # Default description if not provided (for quick testing)
    title = args.title or "Mathematics for Earth Sciences"
    description = args.description or """
    Teaches a variety of important and fundamental university-level mathematical tools to tackle mathematical problems...
    """

    # Load settings
    config = Settings()
    
    # Setup logging
    log_level = "DEBUG" if args.debug else config.log_level
    setup_logging(level=log_level)

    # Instantiate ontology
    from oracle.data.msc_ontology import MSCOntology
    ontology = MSCOntology(args.ontology_path)

    # Run classification
    result = asyncio.run(classify_module(
        title=title,
        description=description,
        ontology=ontology,
        config=config,
        use_async=not args.no_async,
        langsmith_mode=args.langsmith or config.langchain_tracing_v2,
        debug_mode=args.debug,
        starting_depth=args.starting_depth,
        depth_limit=args.depth_limit
    ))

    # Print results summary
    print(f"\nClassification complete for: {title}")
    print(f"Final codes: {[c.code for c in result.selected_codes]}")
    print(json.dumps(result.model_dump(), indent=2))

if __name__ == "__main__":
    main()
