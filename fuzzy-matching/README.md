# Local Name Matcher: LlamaIndex & Ollama Retrieval

## 💡Description

This Python project provides a robust solution for **fuzzy name matching** between a list of full item names and a list of short or analogous names. It leverages **LlamaIndex** for high-quality **semantic search** and uses a **self-hosted Ollama** instance for the underlying embedding model, ensuring privacy and local execution.

The goal is to automatically find the best-fitting full name for every short name, even when the short name is an abbreviation, a slight variation, or has word order changes.

---

## 🛠️ How It Works

The system operates based on the **Vector Search** paradigm:

1.  **Indexing (Knowledge Base Creation):** Each full name from `items_names.txt` is converted into a high-dimensional vector (an **embedding**) using the local **Ollama** embedding model (`nomic-embed-text`). These vectors are stored in a **LlamaIndex `VectorStoreIndex`**.
2.  **Querying (Matching):** Each short name from `input.txt` is also converted into a vector using the same Ollama model.
3.  **Retrieval:** LlamaIndex compares the vector of the short name (the query) against all the stored vectors of the full names. It identifies and retrieves the full name whose vector is **most similar** (closest distance in vector space), providing the best semantic match.
4.  **Output:** The script compiles the successful matches into an `output.csv` file.

---

## 🚀 Setup and Installation

Follow these steps to get the project running on your local machine.

### 1. Prerequisites

You must have **Ollama** installed and running on your system.

Once Ollama is running, pull the required models from the command line:

```bash
ollama pull embeddinggemma:latest
ollama pull gemma3:12b-it-qat
```

### 2. Python Environment

Create and activate a virtual environment, then install the necessary dependencies:

```Bash

# Install required libraries
pip install llama-index llama-index-llms-ollama llama-index-embeddings-ollama pandas
```

### 3. Data Files

The project expects two plain text files in the root directory:

File Name Content Example
items_names.txt The list of Full Names (one name per line) that serves as the search knowledge base. Central Processing Unit, Graphics Processing Unit
input.txt The list of Short Names (one name per line) that will be used as queries. GPU, CPU

## ⚙️ Usage

### 1. Configure the Script

Open name_matcher.py (or the Python script you used) and verify the Ollama Configuration section matches your setup, particularly the OLLAMA_BASE_URL (usually http://localhost:11434).

```Python

# Ollama Model Configuration (Verify these settings)
EMBED_MODEL_NAME = "embeddinggemma:latest"
LLM_MODEL_NAME = "gemma3:12b-it-qat"
OLLAMA_BASE_URL = "http://localhost:11434"
MIN_SIMILARITY_SCORE = 0.5 # Minimum score to consider a match valid
```

### 2. Run the Matching Script

Execute the Python file:

```bash
python name_matcher.py
```

#### 3. Check the Output

Upon successful execution, a file named output.csv will be generated in the project directory.

output.csv Structure:

| Short Name | Full Name Match          | Similarity Score (Optional) |
| ---------- | ------------------------ | --------------------------- |
| GPU        | Graphics Processing Unit | 0.8541                      |
| USB-A      | Universal Serial Bus     | 0.7910                      |
