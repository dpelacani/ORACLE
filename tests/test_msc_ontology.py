"""
Tests for MSCOntology CSV parsing and hierarchy.
"""

import pytest
from pathlib import Path
from oracle.data.msc_ontology import MSCOntology

@pytest.fixture
def msc_ontology():
    # Use the real CSV for testing as it's the source of truth
    csv_path = Path("ontology/msc/MSC_2020.csv")
    return MSCOntology(csv_path)

def test_msc_ontology_roots(msc_ontology):
    roots = msc_ontology.get_roots()
    assert len(roots) > 0
    # Check a known root from CSV: "00-XX" -> should be "00"
    root_codes = [r.code for r in roots]
    assert "00" in root_codes
    
    # Check root content
    root_00 = next(r for r in roots if r.code == "00")
    assert "General" in root_00.label
    assert root_00.has_children is True

def test_msc_ontology_children_l2(msc_ontology):
    # Level 1 "00" should have Level 2 children like "00Axx" or "00-01"
    children = msc_ontology.get_children("00")
    assert len(children) > 0
    child_codes = [c.code for c in children]
    assert "00Axx" in child_codes
    
    # Check has_children flag
    node_00Axx = next(c for c in children if c.code == "00Axx")
    assert node_00Axx.has_children is True

def test_msc_ontology_children_l3(msc_ontology):
    # Level 2 "00Axx" should have Level 3 children like "00A05"
    children = msc_ontology.get_children("00Axx")
    assert len(children) > 0
    child_codes = [c.code for c in children]
    assert "00A05" in child_codes
    
    # Bottom level node should have has_children=False
    node_00A05 = next(c for c in children if c.code == "00A05")
    assert node_00A05.has_children is False

def test_msc_ontology_get_node(msc_ontology):
    node = msc_ontology.get_node("62Axx")
    assert node is not None
    assert "statistics" in node.label.lower()
    
    node_none = msc_ontology.get_node("NON_EXISTENT")
    assert node_none is None
