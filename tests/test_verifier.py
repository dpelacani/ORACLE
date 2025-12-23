"""
Tests for verification.
"""

from unittest.mock import MagicMock, patch
from oracle.verify.verifier import Verifier, FinalClassification
from oracle.extract.concept_extractor import ConceptSummary

def test_verify_selection():
    mock_llm = MagicMock()
    verifier = Verifier(llm=mock_llm)
    
    concept_summary = ConceptSummary(module_title="Test")
    
    # Mock the result of the chain
    mock_result = {
        "module_title": "Test",
        "ontology_name": "TestOntology",
        "selected_codes": [],
        "unmatched_topics": [],
        "processing_reason": "None"
    }
    
    # Mock the chain returned by make_chain
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = mock_result
    
    with patch.object(verifier, 'make_chain', return_value=mock_chain):
        result = verifier.verify_selection(concept_summary, [], "TestOntology")
        assert isinstance(result, FinalClassification)
