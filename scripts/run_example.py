"""
Script to run classification on an example file.
"""

import asyncio
import traceback
from pathlib import Path
from oracle.config import Settings
from oracle.cli.classify import classify_module
from oracle.data.msc_ontology import MSCOntology
from oracle.utils.logging import setup_logging

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-async", action="store_true", help="Disable async execution")
    args = parser.parse_args()

    # Setup test data
    title = "Mathematics for Earth Sciences"
    description = """
    Teaches a variety of important and fundamental university-level mathematical tools to tackle mathematical problems 
    that commonly arise in Earth Sciences such as in planetary sciences, geodynamics, seismic techniques, 
    numerical modelling, physical and surface processes, tectonics of the ocean and many more...
    """


    # Load settings
    config = Settings()
    setup_logging(level="INFO")

    # Print debug config
    print("\nConfiguration Loaded:")
    for k, v in config.debug_dump().items():
        print(f"  {k}: {v}")
    print("-" * 40 + "\n")

    # Instantiate ontology
    csv_path = Path("ontology/msc/MSC_2020.csv")
    if not csv_path.exists():
        # Fallback if running from scripts dir
        csv_path = Path("../ontology/msc/MSC_2020.csv")
    ontology = MSCOntology(csv_path)

    try:
        # Run classification
        result = asyncio.run(classify_module(
            title=title,
            description=description,
            ontology=ontology,
            config=config,
            use_async=not args.no_async,
            langsmith_mode=False,
            debug_mode=True,
            starting_depth=2,
            depth_limit=2,
        ))
        result, concept_summary, selected_entries = result

        print("Concept Summary:")
        print("-" * 40)
        print(concept_summary)

        print("Selected Entries:")
        print("-" * 40)
        print(selected_entries)
        
        print("\n" + "="*50)
        print("FINAL CLASSIFICATION RESULT")
        print("="*50)
        print(f"Title: {title}")
        print(f"Codes: {[c.code for c in result.selected_codes]}")
        for code in result.selected_codes:
            print(f"  - {code.code}: {code.label}")
        
        if result.unmatched_topics:
            print(f"\nUnmatched Topics: {len(result.unmatched_topics)}")
            for t in result.unmatched_topics:
                print(f"  - {t.topic}")

    except Exception as e:
        print(f"\nError running example: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
