import logging
from pathlib import Path
from oracle.data.msc_ontology import MSCOntology

def test_ontology_depth():
    logging.basicConfig(level=logging.INFO)
    csv_path = Path("ontology/msc/MSC_2020.csv")
    if not csv_path.exists():
        csv_path = Path("../ontology/msc/MSC_2020.csv")
        
    if not csv_path.exists():
        print("CSV not found")
        return

    ontology = MSCOntology(csv_path)
    
    # Check roots (Level 1)
    roots = ontology.get_roots()
    print(f"Total Roots (Level 1): {len(roots)}")
    
    # Check a few specific roots and their children
    for root_code in ['62', '15', '46']:
        root_node = ontology.get_node(root_code)
        if root_node:
            print(f"\nRoot {root_code}: {root_node.label}")
            print(f"  Has children flag: {root_node.has_children}")
            children = ontology.get_children(root_code)
            print(f"  Number of children (Level 2): {len(children)}")
            if children:
                print(f"  First 3 Children Codes: {[c.code for c in children[:3]]}")
                # Depth 3 test
                for child in children:
                    if child.has_children:
                        gc = ontology.get_children(child.code)
                        print(f"    Child {child.code} has {len(gc)} grandchildren (Level 3)")
                        print(f"    Grandchildren Codes: {[g.code for g in gc[:5]]}")
                        break
        else:
            print(f"Root {root_code} not found")

if __name__ == "__main__":
    test_ontology_depth()
