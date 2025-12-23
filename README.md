# ORACLE 🔮

**O**ntology-based **R**easoning **A**gents for **C**urriculum **L**abelling and **E**xploration.

ORACLE is an intelligent system designed to classify educational content (such as university module descriptions) against complex hierarchical ontologies (like the Mathematics Subject Classification - MSC 2020). It leverages Large Language Models (LLMs) to extract concepts, traverse ontology trees, and verify classifications with high precision.

For a detailed deep-dive into the technical design, see **[architecture.md](architecture.md)**.

## 🚀 Features

- **Concept Extraction**: Automatically extracts core topics, methods, applications, and skills from unstructured text.
- **Hierarchical Traversal**: Efficiently navigates deep ontology trees, selecting relevant branches to explore based on content relevance.
- **Verification & Refinement**: A dedicated verification step ensures selected codes are justified and removes hallucinations or weak matches.
- **LangSmith Integration**: Built-in support for LangSmith tracing to debug and monitor LLM chains.
- **Flexible Ontology Support**: Can be adapted to work with different hierarchical classification systems (JSON-based format).

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- An OpenAI-compatible API key (e.g., OpenAI, Azure, or a local LLM server).

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dpelacani/ORACLE.git
   cd ORACLE
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scriptsctivate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

## ⚙️ Configuration

Create a `.env` file or export the following environment variables:

```bash
# Required
export OPENAI_API_KEY="your-api-key"

# Optional: Custom LLM Endpoint (e.g., for local models or proxies)
export OPENAI_BASE_URL="https://your-custom-endpoint/v1"

# Optional: LangSmith Tracing
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
export LANGCHAIN_API_KEY="your-langsmith-key"
export LANGCHAIN_PROJECT="oracle-classification"
```

## 📖 Usage

### Running the Example
A sample script is provided to demonstrate how to classify a module description against the MSC ontology.

1. Ensure you have the ontology data generated (see below).
2. Run the example script:
   ```bash
   python scripts/run_example.py
   ```

### Generating the Ontology Tree
If you are using the MSC 2020 dataset, you first need to generate the JSON tree structure from the CSV file:

```bash
cd ontology/msc
python create_tree.py
```
This will populate the `ontology/msc/` directory with the necessary JSON files.

### Using the CLI (Coming Soon)
The package installs a CLI tool `oracle-classify`.
```bash
oracle-classify --input "path/to/module.txt" --ontology "ontology/msc"
```

## 📂 Project Structure

```
ORACLE/
├── oracle/                 # Main package source code
│   ├── cli/                # Command-line interface
│   ├── data/               # Ontology loading and validation
│   ├── extract/            # Concept extraction logic
│   ├── match/              # Tree traversal and matching
│   ├── verify/             # Final verification and formatting
│   └── utils/              # Logging, prompts, and helpers
├── ontology/               # Ontology data files
│   └── msc/                # Mathematics Subject Classification (MSC 2020)
├── scripts/                # Utility and example scripts
├── tests/                  # Unit tests
├── docs/                   # Documentation
├── pyproject.toml          # Project configuration
└── requirements.txt        # Python dependencies
```

## 📝 TODO

- [ ] Add support for batch processing of multiple files.
- [ ] Improve error handling for LLM timeouts.

### Resarch Features
- [ ] CoT with examples. Use kNN to select 10 diverse examples to label. From each group, select 2 more for validation.
- [ ] Self consistency sampling (expensive!): run at various temperatures, use majority voting for final result
- [ ] Topic Expansion: bring lower level topics as a description of the current topic

### Non-priority
- [ ] Add a web interface (Streamlit/Gradio) for interactive classification.
- [ ] Implement caching for ontology tree loading to speed up startup.
- [ ] Fix unit tests
- [ ] Document the JSON ontology format for custom ontologies.

## 📄 License

[MIT License](LICENSE)
