"""
Mathematical Subject Classification (MSC) implementation of BaseOntology.
"""

import csv
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
from .base import BaseOntology, OntologyNode

logger = logging.getLogger(__name__)

class MSCOntology(BaseOntology):
    """
    Implementation of MSC2020 ontology loading directly from CSV.
    
    Hierarchy Logic (from create_tree.py):
    - Level 1 (Roots): XX-XX (e.g., 62-XX -> code "62")
    - Level 2: XX-NN or XXAxx (e.g., 62-01, 62Axx)
    - Level 3: XXANN (e.g., 62A01)
    """

    def __init__(self, csv_path: str, synonym_generator: Optional[Any] = None):
        self.csv_path = Path(csv_path)
        self.synonym_generator = synonym_generator
        self.nodes: Dict[str, OntologyNode] = {}
        self.hierarchy: Dict[str, List[str]] = {} # parent_code -> [child_codes]
        self.roots: List[str] = []
        
        self._load_csv()

    def _load_csv(self):
        """Parse the CSV and build the internal hierarchy."""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"MSC CSV file not found: {self.csv_path}")

        raw_entries = []
        # Try latin-1 as per legacy script
        with open(self.csv_path, 'r', encoding='latin-1') as f:
            # Detect delimiter
            sample = f.readline()
            delimiter = '\t' if '\t' in sample else ','
            f.seek(0)
            
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                # Clean keys and values
                clean_row = {str(k).strip().strip('"'): str(v).strip().strip('"') for k, v in row.items()}
                
                code = clean_row.get('code')
                label = clean_row.get('text')
                desc = clean_row.get('description') or ""
                
                if code and label:
                    raw_entries.append({
                        'code': code.strip(),
                        'label': label.strip(),
                        'description': desc.strip()
                    })

        # Track full codes for child lookup
        all_codes = {e['code'] for e in raw_entries}
        
        # Build hierarchy groups
        roots_map = {}
        l2_groups = {} # XX -> List[code]
        l3_groups = {} # XXAxx -> List[code]

        for entry in raw_entries:
            code = entry['code']
            
            # 1. Level 1 Roots: XX-XX
            match_root = re.match(r'^(\d{2})-XX$', code)
            if match_root:
                root_id = match_root.group(1)
                entry['code'] = root_id # Simplify for ORACLE use
                self.nodes[root_id] = OntologyNode(
                    code=root_id,
                    label=entry['label'],
                    description=entry['description']
                )
                self.roots.append(root_id)
                continue

            # 2. Level 2 Category: XX[A-Z]xx or XX-NN
            match_l2_cat = re.match(r'^(\d{2})[A-Z]xx$', code, re.IGNORECASE)
            match_l2_leaf = re.match(r'^(\d{2})-\d{2}$', code)
            
            if match_l2_cat or match_l2_leaf:
                root_id = (match_l2_cat or match_l2_leaf).group(1)
                l2_groups.setdefault(root_id, []).append(code)
                self.nodes[code] = OntologyNode(
                    code=code,
                    label=entry['label'],
                    description=entry['description']
                )
                continue

            # 3. Level 3 Leaf: XX[A-Z]NN
            match_l3 = re.match(r'^(\d{2})([A-Z])\d{2}$', code, re.IGNORECASE)
            if match_l3:
                root_id = match_l3.group(1)
                letter = match_l3.group(2)
                parent_code = f"{root_id}{letter}xx"
                l3_groups.setdefault(parent_code, []).append(code)
                self.nodes[code] = OntologyNode(
                    code=code,
                    label=entry['label'],
                    description=entry['description']
                )
                continue

        # Link Hierarchy
        for root_id in self.roots:
            children = l2_groups.get(root_id, [])
            if children:
                self.hierarchy[root_id] = children
                self.nodes[root_id].has_children = True

        for parent_code, children in l3_groups.items():
            if parent_code in self.nodes:
                self.hierarchy[parent_code] = children
                self.nodes[parent_code].has_children = True

    def get_roots(self) -> List[OntologyNode]:
        return [self.nodes[r] for r in sorted(self.roots)]

    def get_children(self, parent_code: str) -> List[OntologyNode]:
        child_codes = self.hierarchy.get(parent_code, [])
        return [self.nodes[c] for c in sorted(child_codes)]

    def get_node(self, code: str) -> Optional[OntologyNode]:
        return self.nodes.get(code)
