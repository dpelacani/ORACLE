"""
CLI entry point for running classifications.
"""

import argparse
import sys
import json
import logging
from pathlib import Path

from oracle.config import Settings
from oracle.data.base import BaseOntology
from oracle.extract.concept_extractor import ConceptExtractor
from oracle.match.level_selector import LevelSelector
from oracle.match.traversal import TraversalController
from oracle.verify.verifier import Verifier
from oracle.utils.logging import setup_logging

logger = logging.getLogger(__name__)

def classify_module(
    module_description: str,
    ontology: BaseOntology,
    module_title: str = "Untitled Module",
    debug_log_dir: str = "debug_logs",
    starting_depth: int = 1,
    max_depth: int = 10,
):
    # Load config from .env and environment variables
    config = Settings()

    # Determine modes
    log_level_str = config.log_level.upper()
    langsmith_mode = log_level_str == "LANGSMITH"
    debug_mode = log_level_str == "DEBUG"
    
    # Setup logging
    if debug_mode:
        log_level = logging.DEBUG
    elif langsmith_mode:
        log_level = logging.INFO  # Use INFO for LangSmith to reduce noise
    else:
        log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Always enable component file logging (files always log at DEBUG level)
    setup_logging(log_level, config=config, log_dir=debug_log_dir)
    
    # Initialize components
    llm = config.get_llm()                              # The model to use for classification and verification
    extractor = ConceptExtractor(llm)                   # Concept extractor for extracting concepts from the module description
    selector = LevelSelector(llm)                       # Level selector for selecting the appropriate level of the ontology at each step
    controller = TraversalController(selector, ontology) # Traversal controller for traversing the ontology
    verifier = Verifier(llm)                            # Verifier for verifying the classification

    # Step 1: Concept Extraction
    print("=" * 80) if debug_mode else None
    print("STEP 1: CONCEPT EXTRACTION") if debug_mode else None
    print("=" * 80) if debug_mode else None
    logger.info("Extracting concepts...")
    concept_summary = extractor.extract_concepts(
        title=module_title,
        text=module_description, 
        langsmith_mode=langsmith_mode,
        debug_mode=debug_mode
    )
    if debug_mode:
        print(f"\nExtracted Concepts:")
        print(f"  Core Topics ({len(concept_summary.core_topics)}): {concept_summary.core_topics}")
        print(f"  Methods ({len(concept_summary.methods)}): {concept_summary.methods}")
        print(f"  Applications ({len(concept_summary.applications)}): {concept_summary.applications}")
        print(f"  Skills/Outcomes ({len(concept_summary.skills)}): {concept_summary.skills}")
        logger.debug(f"Extracted {len(concept_summary.core_topics)} core topics, "
                    f"{len(concept_summary.methods)} methods, "
                    f"{len(concept_summary.applications)} applications")
    
    # Step 2: Hierarchical Traversal
    print("\n" + "=" * 80) if debug_mode else None
    print("STEP 2: HIERARCHICAL TRAVERSAL") if debug_mode else None
    print("=" * 80) if debug_mode else None
    logger.info("Traversing ontology...")
    selected_entries = controller.traverse(
        concept_summary=concept_summary,
        langsmith_mode=langsmith_mode,
        debug_mode=debug_mode,
        starting_depth=starting_depth,
        depth_limit=max_depth,
    )

    if debug_mode:
        print(f"\nTraversal Results:")
        print(f"  Total entries selected: {len(selected_entries)}")
        if selected_entries:
            print(f"  Selected codes: {[e.code for e in selected_entries]}")
        logger.debug(f"Traversal selected {len(selected_entries)} entries")
    
    # Step 3: Verification
    print("\n" + "=" * 80) if debug_mode else None
    print("STEP 3: VERIFICATION") if debug_mode else None
    print("=" * 80) if debug_mode else None
    logger.info("Verifying selection...")
    final_classification = verifier.verify_selection(
        concept_summary=concept_summary,
        selected_entries=selected_entries,
        ontology_name="MSC2020",
        langsmith_mode=langsmith_mode,
        debug_mode=debug_mode
    )
    if debug_mode:
        print(f"\nVerification Results:")
        print(f"  Final codes selected: {len(final_classification.selected_codes)}")
        if final_classification.selected_codes:
            print(f"  Codes: {[c.code for c in final_classification.selected_codes]}")
        print(f"  Unmatched topics: {len(final_classification.unmatched_topics)}")
        if final_classification.unmatched_topics:
            print(f"  Unmatched: {[t.topic for t in final_classification.unmatched_topics[:5]]}...")
        logger.debug(f"Verification complete: {len(final_classification.selected_codes)} final codes, "
                    f"{len(final_classification.unmatched_topics)} unmatched topics")
    
    return final_classification

def main():
    parser = argparse.ArgumentParser(description="ORACLE Classification CLI")
    # parser.add_argument("input_file", help="Path to the input curriculum file")
    parser.add_argument("--ontology-path", default="ontology/msc", help="Path to ontology directory")
    parser.add_argument("--ontology-name", default="MSC2020", help="Name of the ontology")
    parser.add_argument("--debug-log-dir", default="debug_logs", help="Directory for debug logs")
    parser.add_argument("--starting-depth", type=int, default=1, help="Starting depth for traversal")
    parser.add_argument("--max-depth", type=int, default=10, help="Maximum depth for traversal")
    args = parser.parse_args()

    # # Read input file
    # try:
    #     with open(args.input_file, 'r') as f:
    #         module_description = f.read()
    # except FileNotFoundError:
    #     print(f"Error: Input file '{args.input_file}' not found.")
    #     sys.exit(1)

    module_description = """
    Description: Teaches a variety of important and fundamental university-level mathematical tools to tackle mathematical problems that commonly arise in Earth Sciences such as in planetary sciences, geodynamics, seismic techniques, numerical modelling, physical and surface processes, tectonics of the ocean and many more... \n\n Learning Outcomes Upon successfully completing this module, students will be able to:  Transform between co-ordinate systems; Manipulate vectors and matrices using simple algebra; Solve small systems of linear equations; Solve small eigenvalue problems; Solve simple differential equations analytically; Differentiate and integrate functions of two independent variables; Compute the gradient of a scalar field and the div and curl of a vector field; Analyse functions, sequences and series for convergence; \n\n Module Content Syllabus: Co-ordinate systems and vectors: transformation between co-ordinate systems (Cartesian, polar, cylindrical, spherical); definition of vector, vector algebra, scalar product, vector product. Multivariable Calculus: interpretation and visualisation of functions of two independent variables; partial differentiation; chain rule; double integrals. Vector calculus: scalar and vector fields; operators (gradient, divergence, curl, Laplacian). Matrices, matrix algebra, determinants, linear simultaneous equations, inverse matrices, Cramer's rule. Strain matrices and Eigenvalue problem: characteristic polynomials; eigenvalues and eigenvectors; symmetric matrices; multiple eigenvalues. Infinite Series: Sequences; series; notation; partial sums; convergence; power series. First-order differential equations: classification of differential equations (DEs), solution by separation of variables, integrating factors, Earth Science examples.  Introduction to modelling: numerical differentiation and integration, approximation, numerical solution of ODEs, forward and backward Euler, Newton-Raphson iteration.",
    """

    # Instantiate the ontology
    csv_path = Path(args.ontology_path) / "MSC_2020.csv"
    ontology = MSCOntology(csv_path)

    result = classify_module(
        module_description=module_description,
        ontology=ontology,
        debug_log_dir=args.debug_log_dir,
        starting_depth=args.starting_depth,
        max_depth=args.max_depth,
    )

    print(result.model_dump_json(indent=2))

if __name__ == "__main__":
    main()
