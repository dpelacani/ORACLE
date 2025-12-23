"""
Script to run classification on an example file.
"""

import sys
import os
from pathlib import Path
from oracle.data.msc_ontology import MSCOntology

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from oracle.cli.classify import classify_module

if __name__ == "__main__":
    example_title = "Numerical Optimisation and Machine Learning"
    example_description = """
    This module introduces numerical optimisation and basic machine learning.
    Topics include gradient descent, stochastic gradient methods, linear regression,
    logistic regression, and simple neural networks. Students will learn to implement
    algorithms in Python and to evaluate models on real-world datasets.
    """
    
    # Create a temporary file for the example
    example_file = "examples/sample.md"
    os.makedirs("examples", exist_ok=True)
    with open(example_file, "w") as f:
        f.write(example_description)

    print("Running example classification...")
    
    # Debug config loading
    from oracle.config import Settings
    config = Settings()
    print("\n[DEBUG] Configuration Loaded:")
    for k, v in config.debug_dump().items():
        print(f"  {k}: {v}")
    print("-" * 40 + "\n")

    try:
        # Instantiate ontology early
        csv_path = Path("ontology/msc") / "MSC_2020.csv"
        ontology = MSCOntology(csv_path)

        result = classify_module(
            module_description=example_description,
            module_title=example_title,
            ontology=ontology,
            debug_log_dir="debug_logs",
            starting_depth=2,
            max_depth=2,
        )
        print(result.model_dump_json(indent=2))
    except Exception as e:
        print(f"Error running example: {e}")
