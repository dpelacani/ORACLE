# Ontology Format

Ontologies are stored as JSON files.

## Structure

- `root`: The root identifier.
- `levels`: List of levels.
- `children`: List of filenames for child nodes (sub-ontologies).

## Example

```json
{
  "root": "msc",
  "levels": [1, 2, 3],
  "children": ["msc_62_level_2.json"]
}
```
