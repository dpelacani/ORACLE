"""
Base classes and interfaces for ORACLE ontologies.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class OntologyNode(BaseModel):
    """A single node in the ontology hierarchy."""
    code: str
    label: str
    description: str
    has_children: bool = False

class BaseOntology(ABC):
    """Abstract base class for all ontologies used by ORACLE."""

    @abstractmethod
    def get_roots(self) -> List[OntologyNode]:
        """Return the top-level nodes of the ontology."""
        pass

    @abstractmethod
    def get_children(self, parent_code: str) -> List[OntologyNode]:
        """Return the immediate children of a given node code."""
        pass

    @abstractmethod
    def get_node(self, code: str) -> Optional[OntologyNode]:
        """Return a specific node by its code."""
        pass
