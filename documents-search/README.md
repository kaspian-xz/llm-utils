# Documents Search

A local document search tool using LlamaIndex with Ollama for semantic search. Documents are indexed into a vector store and searched via an interactive CLI using a local LLM.

## Features

- Semantic search across multiple document types
- Incremental indexing with SHA-256 change detection
- Local processing with Ollama (no cloud dependencies)
- Source file attribution in search results

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) running locally
- Required Ollama models:
  - Embedding model: `qwen3-embedding:8b` (multilingual, #1 on MTEB leaderboard)
  - LLM model (e.g., `llama3.1`)

Pull the models before first use:
```bash
ollama pull qwen3-embedding:8b
ollama pull llama3.1
```

## Installation

1. Clone the repository and navigate to the project directory

2. Create and activate a virtual environment:
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with required configuration (see below)

## Configuration

Create a `.env` file in the project root with the following variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATA_DIR` | Yes | Path to directory containing documents to index |
| `STORAGE_DIR` | Yes | Path to store the vector index and file hashes |
| `EMBED_MODEL` | No | Ollama embedding model name (default: `qwen3-embedding:8b`) |
| `LLM_MODEL` | No | Ollama LLM model name (default: `llama3.1:latest`) |
| `OLLAMA_BASE_URL` | No | Ollama server URL (default: `http://localhost:11434`) |

Example `.env`:
```env
DATA_DIR=/path/to/your/documents
STORAGE_DIR=/path/to/index/storage
EMBED_MODEL=qwen3-embedding:8b
LLM_MODEL=llama3.1:latest
OLLAMA_BASE_URL=http://localhost:11434
```

## Usage

### Indexing Documents

Index or synchronize documents from your data directory:

```bash
python index_sync.py
```

Options:
- `-f, --force` - Skip confirmation prompt and force synchronization

```bash
python index_sync.py --force
```

The indexer will:
- Detect new, modified, and deleted files using SHA-256 hashes
- Only re-index changed files (incremental updates)
- Show progress during embedding generation

### Searching Documents

Start the interactive search interface:

```bash
python search.py
```

Enter your query in natural language. The system will:
- Find semantically similar document chunks
- Generate an LLM response based on the context
- Display source file paths for attribution

Type `exit`, `quit`, or `вихід` to close the search interface.

## Supported Document Types

- PDF (`.pdf`)
- Microsoft Word (`.doc`, `.docx`)
- Microsoft Excel (`.xls`, `.xlsx`)
- Text files (`.txt`)
- CSV (`.csv`)
- Markdown (`.md`)
- HTML (`.html`)

## Limitations

- Large documents may take time to index due to single-threaded embedding generation
- LLM response time depends on your hardware and model size

## License

MIT
