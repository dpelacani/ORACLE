"""
Tests for concept extraction.
"""

from oracle.extract.concept_extractor import ConceptExtractor

def test_extract_concepts():
    extractor = ConceptExtractor()
    concepts = extractor.extract_concepts("some text")
    assert isinstance(concepts, list)
