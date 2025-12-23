"""
Tests for ontology traversal.
"""

from unittest.mock import MagicMock
from oracle.match.traversal import TraversalController
from oracle.match.level_selector import LevelSelector

def test_traversal():
    mock_llm = MagicMock()
    mock_ontology = MagicMock()
    selector = LevelSelector(llm=mock_llm)
    controller = TraversalController(selector=selector, ontology=mock_ontology)
    
    # Mocking would be complex for a full traverse, just check initialization for now
    assert controller.selector == selector
    assert controller.ontology == mock_ontology
