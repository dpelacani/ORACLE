"""
Centralised prompt templates.
"""

from langchain_core.prompts import ChatPromptTemplate

CONCEPT_EXTRACTION_PROMPT = ChatPromptTemplate.from_template(
    """
You are a domain expert analysing a Higher Education module description.

Extract a structured summary of the module content with the following fields:
- module_title (if present)
- core_topics: main theoretical ideas and concepts
- methods: algorithms, techniques, or procedural methods
- applications: problem domains or examples
- skills: the ability to apply the concepts and methods to solve problems

Return a JSON object exactly following this schema:

{{
  "module_title": "<string or null>",
  "core_topics": ["<topic_1>", "..."],
  "methods": ["<method_1>", "..."],
  "applications": ["<application_1>", "..."],
  "skills": ["<skill_1>", "..."]
}}

Module description:
\"\"\"{module_description}\"\"\" 
"""
)

LEVEL_SELECTION_PROMPT = ChatPromptTemplate.from_template(
    """
You are performing ontology-based classification of a Higher Education module.

Inputs:
1) A structured concept summary of the module.
2) A list of ontology entries at the CURRENT LEVEL only, each with:
   - code
   - label
   - description

Your tasks at THIS LEVEL are:
- From the provided entries, select all codes that plausibly match the module content.
- For each selected entry, indicate:
  - which concepts (from core_topics, methods, applications, skills) it matches;
  - a short justification;
  - whether you recommend descending into its children (should_descend = true/false).
    *Set should_descend = true if more specific subclasses are likely to be relevant, 
    and the module content seems rich enough to justify finer distinctions.*

Do NOT invent codes or labels. Only choose among the entries given at this level.

Return a JSON object:

{{
  "selected_entries": [
    {{
      "code": "<string>",
      "label": "<string>",
      "depth": {depth},
      "matched_concepts": ["<core_concept_1>", "<core_concept_2>", "<skill_3>" "..."],
      "justification": "<2–4 sentence explanation>",
      "should_descend": true or false
    }},
    ...
  ]
}}

Module concept summary:
{concept_summary_json}

Ontology entries at this level:
{ontology_entries_json}
"""
)

VERIFICATION_PROMPT = ChatPromptTemplate.from_template(
    """
You are the final verifier for ontology-based module classification.

Inputs:
- Module concept summary (core_topics, methods, applications, skills).
- A list of selected ontology entries across ALL LEVELS, each with:
  - code
  - label
  - depth
  - matched_concepts
  - justification

Tasks:
1) Remove duplicates and obvious near-duplicates.
2) Prefer more specific (higher depth) entries when they clearly apply, 
   but you may keep both specific and general codes where both are informative.
3) Remove codes whose justification is weak or redundant relative to others in the same branch.
4) Identify any core topic, method, or application that has no plausible selected code. 
   For such topics, you may suggest a nearest_code_candidate from the selected codes if appropriate, 
   otherwise leave it null.
5) Produce a final, ready-for-parsing JSON object strictly with fields:
   - module_title (if not present, set to null)
   - ontology_name (if not present, set to null)
   - selected_codes: list of objects (code, label, depth, matched_concepts, justification), if none, return empty list
   - unmatched_topics: list of objects (topic, note, nearest_code_candidate), if none, return empty list
   - processing_reason: 2-3 sentences explaining the rationale for any significant changes made during verification, if none, set to null
    Return a JSON object:
    {{
      "module_title": "<string or null>",
      "ontology_name": "<string or null>",
      "selected_codes": [
        {{
          "code": "<string>",
          "label": "<string>",
          "depth": <int>,
          "matched_concepts": ["<core_concept_1>", "<core_concept_2>", "<skill_3>" "..."],
          "justification": "<2–4 sentence explanation>"
        }},
        ...
      ],
      "unmatched_topics": [
        {{
          "topic": "<string>",
          "note": "<explanation of why unmatched>",
          "nearest_code_candidate": "<string or null>"
        }},
        ...
      ],
      "processing_reason": "<2-3 sentence explanation or null>"
    }}
   
Ontology name: "{ontology_name}"

Module concept summary:
{concept_summary_json}

Selected entries across all levels:
{selected_entries_json}
"""
)
