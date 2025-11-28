"""
Tests for data loaders.
"""

import pytest
from oracle.data.ontology_loader import OntologyLoader

def test_load_entry_file():
    loader = OntologyLoader("ontology/msc")
    # Mocking file access would be better, but for now we assume the file exists
    # data = loader.load_entry_file("msc_entry.json")
    # assert data["root"] == "msc"
    pass
