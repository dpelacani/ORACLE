# Architecture

ORACLE uses a hierarchical selective traversal approach to classify curriculum content against an ontology.

## Pipeline

1. **Ingestion**: Load curriculum content.
2. **Extraction**: Extract key concepts using LLMs.
3. **Matching**: Traverse the ontology hierarchy, selecting relevant branches at each level.
4. **Verification**: Verify the final leaf node selections.
