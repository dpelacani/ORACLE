"""
Tests for verification.
"""

from oracle.verify.verifier import Verifier

def test_verify_selection():
    verifier = Verifier()
    assert verifier.verify_selection([])
