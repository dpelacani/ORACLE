"""
Script to run classification on an example file.
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from oracle.cli.classify import classify_module

if __name__ == "__main__":
    example_text = """
    This module introduces numerical optimisation and basic machine learning.
    Topics include gradient descent, stochastic gradient methods, linear regression,
    logistic regression, and simple neural networks. Students will learn to implement
    algorithms in Python and to evaluate models on real-world datasets.
    """
    
    # Create a temporary file for the example
    example_file = "examples/sample.md"
    os.makedirs("examples", exist_ok=True)
    with open(example_file, "w") as f:
        f.write(example_text)

    print("Running example classification...")
    try:
        result = classify_module(
            module_description=example_text,
            ontology_path="ontology/msc",
            root_file="msc_entry.json"
        )
        print(result.json(indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error running example: {e}")
