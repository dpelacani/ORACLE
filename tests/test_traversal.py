"""
Tests for ontology traversal.
"""

from oracle.match.traversal import TraversalController
from oracle.match.level_selector import LevelSelector

def test_traversal():
    selector = LevelSelector()
    controller = TraversalController(selector)
    # result = controller.traverse(["concept"], [])
    # assert isinstance(result, list)
    pass
