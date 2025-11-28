import csv
import json
import re
import os
from typing import Dict, List, Optional

# Configuration
INPUT_FILE = 'MSC_2020.csv'
OUTPUT_DIR = '.'  # Current directory

def clean_text(text: str) -> str:
    """Remove surrounding quotes and whitespace."""
    return text.strip().strip('"').strip()

def parse_msc_csv(filepath: str) -> List[Dict[str, str]]:
    """Read the MSC CSV file and return a list of entries."""
    entries = []
    # Try latin-1 encoding as utf-8 failed
    with open(filepath, 'r', encoding='latin-1') as f:
        # Detect delimiter (it looked like TSV in the preview)
        line = f.readline()
        delimiter = '\t' if '\t' in line else ','
        f.seek(0)
        
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            # Handle potential BOM or whitespace in keys
            clean_row = {k.strip(): v for k, v in row.items()}
            
            # Map columns based on observed header: code, text, description
            # Note: The file might have different headers, let's be robust
            code = clean_row.get('code') or clean_row.get('"code"')
            label = clean_row.get('text') or clean_row.get('"text"')
            desc = clean_row.get('description') or clean_row.get('"description"')
            
            if code and label:
                entries.append({
                    'code': clean_text(code),
                    'label': clean_text(label),
                    'description': clean_text(desc) if desc else ""
                })
    return entries

def generate_json_files(entries: List[Dict[str, str]], output_dir: str):
    """Generate the hierarchical JSON files."""
    
    # Data structures to hold the hierarchy
    roots = {} # Key: XX (e.g., "62") -> Entry
    level_2_groups = {} # Key: XX -> List of entries (Level 2)
    level_3_groups = {} # Key: XXLxx -> List of entries (Level 3)
    
    # 1. Classify entries
    for entry in entries:
        code = entry['code']
        
        # Root: XX-XX
        match_root = re.match(r'^(\d{2})-XX$', code)
        if match_root:
            root_id = match_root.group(1)
            # Store root with simplified code "XX" instead of "XX-XX" to match user example
            entry['code'] = root_id 
            roots[root_id] = entry
            continue
            
        # Level 2 Category: XX[A-Z]xx
        match_l2_cat = re.match(r'^(\d{2})[A-Z]xx$', code, re.IGNORECASE)
        if match_l2_cat:
            root_id = match_l2_cat.group(1)
            if root_id not in level_2_groups:
                level_2_groups[root_id] = []
            level_2_groups[root_id].append(entry)
            continue
            
        # Level 2 Leaf: XX-NN (e.g., 62-01)
        match_l2_leaf = re.match(r'^(\d{2})-\d{2}$', code)
        if match_l2_leaf:
            root_id = match_l2_leaf.group(1)
            if root_id not in level_2_groups:
                level_2_groups[root_id] = []
            level_2_groups[root_id].append(entry)
            continue
            
        # Level 3 Leaf: XX[A-Z]NN (e.g., 62A01)
        match_l3 = re.match(r'^(\d{2})([A-Z])\d{2}$', code, re.IGNORECASE)
        if match_l3:
            root_id = match_l3.group(1)
            letter = match_l3.group(2)
            parent_code = f"{root_id}{letter}xx" # e.g., 62Axx
            
            if parent_code not in level_3_groups:
                level_3_groups[parent_code] = []
            level_3_groups[parent_code].append(entry)
            continue
            
    # 2. Build and Write Files
    
    # A. Root File (msc_entry.json)
    root_list = []
    sorted_root_ids = sorted(roots.keys())
    
    for root_id in sorted_root_ids:
        entry = roots[root_id]
        child_filename = f"msc_{root_id}_level_2.json"
        
        # Check if we actually have children for this root
        if root_id in level_2_groups:
            entry['child_file'] = child_filename
        else:
            entry['child_file'] = None
            
        root_list.append(entry)
        
    with open(os.path.join(output_dir, 'msc_entry.json'), 'w', encoding='utf-8') as f:
        json.dump(root_list, f, indent=2, ensure_ascii=False)
    print(f"Created msc_entry.json with {len(root_list)} entries.")

    # B. Level 2 Files
    for root_id, entries in level_2_groups.items():
        filename = f"msc_{root_id}_level_2.json"
        
        for entry in entries:
            code = entry['code']
            # Check if this entry is a parent to Level 3 items
            # Logic: If code is like 62Axx, look for 62Axx in level_3_groups
            if code in level_3_groups:
                entry['child_file'] = f"msc_{code}_level_3.json"
            else:
                entry['child_file'] = None
        
        with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
            
    print(f"Created {len(level_2_groups)} Level 2 files.")

    # C. Level 3 Files
    for parent_code, entries in level_3_groups.items():
        filename = f"msc_{parent_code}_level_3.json"
        
        for entry in entries:
            entry['child_file'] = None # Level 3 are leaves
            
        with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
            
    print(f"Created {len(level_3_groups)} Level 3 files.")

if __name__ == "__main__":
    print("Starting MSC Tree Generation...")
    try:
        entries = parse_msc_csv(INPUT_FILE)
        print(f"Parsed {len(entries)} rows from CSV.")
        generate_json_files(entries, OUTPUT_DIR)
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
