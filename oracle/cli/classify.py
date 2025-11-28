"""
CLI entry point for running classifications.
"""

import argparse
import sys
import json
import logging
from pathlib import Path

from oracle.config import Config
from oracle.data.ontology_loader import OntologyLoader
from oracle.extract.concept_extractor import ConceptExtractor
from oracle.match.level_selector import LevelSelector
from oracle.match.traversal import TraversalController
from oracle.verify.verifier import Verifier
from oracle.utils.logging import setup_logging

logger = logging.getLogger(__name__)

def classify_module(
    module_description: str,
    ontology_path: str = "ontology/msc",
    root_file: str = "msc_entry.json",
    ontology_name: str = "MSC2020",
    debug_log_dir: str = "debug_logs"
):
    # Load config
    config = Config.load_from_env(ontology_path)

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
    
    if langsmith_mode:
        logger.info("LANGSMITH mode enabled - LangSmith tracing will be active")
        logger.info(f"LangSmith project: {config.langsmith_project}")
        logger.info(f"Component logs will be written to: {debug_log_dir} (always DEBUG level)")
    elif debug_mode:
        logger.info("DEBUG mode enabled - File logging and print statements active")
        logger.info(f"Component logs will be written to: {debug_log_dir} (always DEBUG level)")
    else:
        logger.info(f"Component logs will be written to: {debug_log_dir} (always DEBUG level)")
    
    # Initialize components
    llm = config.get_llm()                              # The model to use for classification and verification
    loader = OntologyLoader(ontology_path)       # The ontology loader for loading the ontology
    extractor = ConceptExtractor(llm)                   # Concept extractor for extracting concepts from the module description
    selector = LevelSelector(llm)                       # Level selector for selecting the appropriate level of the ontology at each step
    controller = TraversalController(selector, loader)  # Traversal controller for traversing the ontology in a hierarchical manner
    verifier = Verifier(llm)                            # Verifier for verifying the classification, checking for duplicates and near-duplicates, and ensuring that all core topics, methods, and applications are matched

    # Step 1: Concept Extraction
    print("=" * 80) if debug_mode else None
    print("STEP 1: CONCEPT EXTRACTION") if debug_mode else None
    print("=" * 80) if debug_mode else None
    logger.info("Extracting concepts...")
    concept_summary = extractor.extract_concepts(
        module_description, 
        langsmith_mode=langsmith_mode,
        debug_mode=debug_mode
    )
    if debug_mode:
        print(f"\nExtracted Concepts:")
        print(f"  Core Topics ({len(concept_summary.core_topics)}): {concept_summary.core_topics}")
        print(f"  Methods ({len(concept_summary.methods)}): {concept_summary.methods}")
        print(f"  Applications ({len(concept_summary.applications)}): {concept_summary.applications}")
        print(f"  Skills/Outcomes ({len(concept_summary.skills_outcomes)}): {concept_summary.skills_outcomes}")
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
        root_file=root_file,
        langsmith_mode=langsmith_mode,
        debug_mode=debug_mode
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
        ontology_name=ontology_name,
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
    parser.add_argument("--root-file", default="msc_entry.json", help="Root ontology file")
    parser.add_argument("--ontology-name", default="MSC2020", help="Name of the ontology")
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

    result = classify_module(
        module_description=module_description,
        ontology_path=args.ontology_path,
        root_file=args.root_file,
        ontology_name=args.ontology_name
    )

    print(result.json(indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
