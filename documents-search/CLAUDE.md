# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a local document search tool using LlamaIndex with Ollama for semantic search. Documents are indexed into a vector store, then searched via an interactive CLI using a local LLM.

## Commands

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Index/sync documents (run when documents change)
python index_sync.py

# Start interactive search
python search.py
```

## Prerequisites

- Ollama server running locally (default: http://localhost:11434)
- Required Ollama models pulled:
  - Embedding: `nomic-embed-text:latest`
  - LLM: `llama3.1:latest`

## Configuration (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| DATA_DIR | ./data | Directory containing documents to index |
| STORAGE_DIR | ./storage | Persisted vector store location |
| EMBED_MODEL | nomic-embed-text:latest | Ollama embedding model |
| LLM_MODEL | llama3.1:latest | Ollama LLM model |
| OLLAMA_BASE_URL | http://localhost:11434 | Ollama server URL |

## Architecture

- **index_sync.py**: Document indexer with change detection via SHA-256 hashes. Supports incremental updates (new/modified/deleted files). Uses `IngestionPipeline` with `SentenceSplitter` (chunk_size=1024, overlap=20).

- **search.py**: Interactive query interface. Loads persisted index and runs queries through `QueryEngine` (similarity_top_k=3). Displays LLM response with source file paths.

## Supported Document Types

PDF, DOC, DOCX, XLS, XLSX, TXT, CSV, MD, HTML
