"""
Tests for concept extraction.
"""

from unittest.mock import MagicMock, patch
from oracle.extract.concept_extractor import ConceptExtractor, ConceptSummary

def test_extract_concepts():
    mock_llm = MagicMock()
    extractor = ConceptExtractor(llm=mock_llm)
    
    # Mock the chain invocation by mocking the whole chain object
    mock_result = {
        "module_title": "Test Module",
        "core_topics": ["topic1"],
        "methods": ["method1"],
        "applications": ["app1"],
        "skills": ["skill1"]
    }
    
    # Mock the entire chain object to avoid Pydantic __setattr__ issues
    extractor.chain = MagicMock()
    extractor.chain.invoke.return_value = mock_result
    
    concepts = extractor.extract_concepts("Test Module", "some text")
    assert isinstance(concepts, ConceptSummary)
    assert concepts.module_title == "Test Module"
    assert "topic1" in concepts.core_topics
