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
- Required models:
  - Embedding: `embeddinggemma:latest` (Ollama) or `lang-uk/ukr-paraphrase-multilingual-mpnet-base` (HuggingFace)
  - LLM: `gemma3:4b` (Ollama)

## Configuration (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| DATA_DIR | ./data | Directory containing documents to index |
| STORAGE_DIR | ./storage | Persisted vector store location |
| EMBED_PROVIDER | huggingface | Embedding provider: `huggingface` or `ollama` |
| EMBED_MODEL | (depends on provider) | Ollama: `embeddinggemma:latest`, HuggingFace: `lang-uk/ukr-paraphrase-multilingual-mpnet-base` |
| LLM_MODEL | gemma3:4b | Ollama LLM model |
| OLLAMA_BASE_URL | http://localhost:11434 | Ollama server URL |

## Architecture

- **index_sync.py**: Document indexer with change detection via SHA-256 hashes. Supports incremental updates (new/modified/deleted files). Uses `SentenceSplitter` (chunk_size=512, overlap=50). Supports `-f/--force` flag to skip confirmation.

- **search.py**: Interactive query interface. Loads persisted index and runs queries through `QueryEngine` (similarity_top_k=3). Displays LLM response with source file paths.

## Supported Document Types

PDF, DOC, DOCX, XLS, XLSX, TXT, CSV, MD, HTML
