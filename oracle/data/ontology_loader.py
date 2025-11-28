"""
JSON loaders and structural validation for ontology files.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class OntologyEntry(BaseModel):
    code: str
    label: str
    description: str
    child_file: Optional[str] = None

class OntologyLoader:
    """Loads and validates ontology JSON files."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def load_ontology_level(self, filename: str) -> List[OntologyEntry]:
        """Load a single JSON file representing one level or branch."""
        path = self.base_path / filename
        if not path.exists():
            logger.error(f"Ontology file not found: {path}")
            return []
            
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        entries: List[OntologyEntry] = []

        if isinstance(data, list):
            for entry in data:
                entries.append(
                    OntologyEntry(
                        code=str(entry.get("code", "")),
                        label=entry.get("label", ""),
                        description=entry.get("description", ""),
                        child_file=entry.get("child_file"),
                    )
                )
        return entries

    def load_entry_file(self, filename: str) -> Dict[str, Any]:
        """Load the main entry point for the ontology (legacy/scaffold support)."""
        path = self.base_path / filename
        with open(path, 'r') as f:
            data = json.load(f)
        return data
