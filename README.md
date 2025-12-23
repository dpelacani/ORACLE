# ORACLE 🔮

**O**ntology-based **R**easoning **A**gents for **C**urriculum **L**abelling and **E**xploration.

ORACLE is an intelligent system designed to classify educational content (such as university module descriptions) against complex hierarchical ontologies (like the Mathematics Subject Classification - MSC 2020). It leverages Large Language Models (LLMs) to extract concepts, traverse ontology trees, and verify classifications with high precision.

For a detailed deep-dive into the technical design, see **[architecture.md](architecture.md)**.

## 🚀 Key Features

- **Concept Extraction**: Automatically distills raw module text into structured technical summaries (topics, methods, skills).
- **Parallel Traversal**: Efficiently explores deep ontology trees using `asyncio` to process multiple branches concurrently.
- **Dynamic Synonym Enrichment**: Automatically generates technical synonyms for ontology nodes and caches them locally to improve future matching.
- **Self-Healing Robustness**: Built-in retry logic and timeout handling to gracefully navigate API instability.
- **Dual-Mode Execution**: Support for both high-performance **Asynchronous** runs and sequential **Synchronous** runs for debugging.
- **Verification & Refinement**: A final verification step using OpenAI's Structured Output to guarantee high-quality, JSON-compliant results.

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- An OpenAI-compatible API key.

### Setup

1. **Clone and install:**
   ```bash
   git clone https://github.com/dpelacani/ORACLE.git
   cd ORACLE
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Configure Environment:**
   Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   # Edit .env with your OPENAI_API_KEY and other settings
   ```

## 📖 Usage

### 1. Running the Example Script
The fastest way to see ORACLE in action:
```bash
python scripts/run_example.py
```
*Add `--no-async` to run in sequential mode for step-by-step debugging.*

### 2. Using the CLI
The package installs the `oracle-classify` command:
```bash
oracle-classify --title "Advanced Calc" --description "Limits, derivatives, etc." --ontology-path "path/to/ontology.csv"
```

**Common Flags:**
- `--no-async`: Run sequentially (easier to read logs).
- `--debug`: Enable verbose logging.
- `--langsmith`: Enable LangSmith tracing (if configured).

### 3. Data Support
ORACLE currently ships with native support for **MSC 2020**. The system parses the raw CSV directly, so no pre-processing is required if the repository is correctly cloned.

## 📂 Project Structure

```
ORACLE/
├── oracle/                 # Core engine
│   ├── cli/                # CLI entry points
│   ├── data/               # Ontology loaders & Synonym enrichment
│   ├── extract/            # LLM Concept Extraction
│   ├── match/              # Parallel Traversal & Level Selection
│   ├── verify/             # Final verification (Structured Output)
│   └── utils/              # Prompts, Configuration, Logging
├── ontology/               # Ontology sources and caches
├── scripts/                # Utility scripts & benchmarks
├── tests/                  # Unit tests (Mocked LLM support)
└── architecture.md         # Detailed technical design doc
```

## 📝 Roadmap

- [ ] **Batch Processing**: Support for classifying directories of files.
- [ ] **Web Interface**: Multi-user dashboard for reviewing classifications.
- [ ] **Advanced RAG**: Using vector stores to assist in deep ontology search.
- [ ] **Few-Shot Prompting**: kNN-based example selection for higher accuracy.

## 📄 License

[MIT License](LICENSE)
