import pandas as pd
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.schema import TextNode
from llama_index.llms.ollama import Ollama as OllamaLLM
from llama_index.embeddings.ollama import OllamaEmbedding
import os

# --- Configuration ---
FULL_NAMES_FILE = 'items_names.txt'
SHORT_NAMES_FILE = 'input.txt'
OUTPUT_CSV_FILE = 'output.csv'
TOP_K = 1 # We only want the single best match for each short name
MIN_SIMILARITY_SCORE = 0.75 # Minimum score to consider a match valid (0.0 to 1.0)

# Ollama Model Configuration
EMBED_MODEL_NAME = "embeddinggemma:latest" # Great for embeddings
LLM_MODEL_NAME = "gemma3:12b-it-qat"            # Small, fast model for general LLM tasks
OLLAMA_BASE_URL = "http://localhost:11434" # Default Ollama API endpoint

# --- Helper Function to Read Files ---
def read_names_from_file(file_path):
    """Reads names from a file, one per line."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []

# --- LlamaIndex Implementation with Ollama ---
def find_matches_with_ollama():
    """Builds an index and finds the best match for each short name using Ollama."""

    print(f"1. Configuring LlamaIndex to use Ollama from {OLLAMA_BASE_URL}...")
    
    # Initialize the Ollama Embedding Model
    ollama_embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
        ollama_additional_kwargs={"mirostat": 0},
    )

    # Initialize the Ollama LLM (optional for simple retrieval, but good practice)
    ollama_llm = OllamaLLM(
        model=LLM_MODEL_NAME, 
        base_url=OLLAMA_BASE_URL
    )

    # Set the global settings for LlamaIndex
    Settings.embed_model = ollama_embed_model
    Settings.llm = ollama_llm
    
    print(f"   Using Embedding Model: {EMBED_MODEL_NAME}")
    print(f"   Using LLM Model: {LLM_MODEL_NAME}")

    # 2. Load Data
    full_names = read_names_from_file(FULL_NAMES_FILE)
    short_names = read_names_from_file(SHORT_NAMES_FILE)

    if not full_names or not short_names:
        print("Please ensure both input files are populated.")
        return

    print(f"\n2. Loaded {len(full_names)} full names and {len(short_names)} short names.")

    # Convert full names into LlamaIndex Nodes
    nodes = [TextNode(text=name) for name in full_names]

    # 3. Indexing (Build the Knowledge Base)
    # The index will now use the configured OllamaEmbedding model.
    print("3. Building VectorStoreIndex (This may take a moment)...")
    index = VectorStoreIndex(nodes)

    # 4. Setup Retriever
    # Configure the retriever to find the top 1 most similar result
    retriever = index.as_retriever(similarity_top_k=TOP_K)

    # 5. Matching & Output Preparation
    results = []
    print("4. Starting name matching...")

    for i, short_name in enumerate(short_names):
        # Retrieve the most similar full name
        retrieved_nodes = retriever.retrieve(short_name)

        full_name_match = "NO_MATCH_FOUND"
        score = None

        if retrieved_nodes:
            top_node = retrieved_nodes[0]
            score = top_node.get_score()
            
            if score >= MIN_SIMILARITY_SCORE:
                full_name_match = top_node.get_text()
            else:
                full_name_match = f"NO_MATCH_FOUND"

        results.append({
            'Short Name': short_name,
            'Full Name Match': full_name_match,
            'Similarity Score (Optional)': score
        })

        if (i + 1) % 10 == 0:
            print(f"   Processed {i + 1}/{len(short_names)} short names.")

    # 6. Save Output
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV_FILE, index=False)
    print("\n--- Process Complete ---")
    print(f"Results saved to '{OUTPUT_CSV_FILE}' with {len(df)} pairs.")

# --- Execution ---
if __name__ == "__main__":
    # Create dummy files for demonstration if they don't exist
    if not os.path.exists(FULL_NAMES_FILE):
        print(f"Creating dummy file: {FULL_NAMES_FILE}")
        with open(FULL_NAMES_FILE, 'w') as f:
            f.write("Central Processing Unit\n")
            f.write("Graphics Processing Unit\n")
            f.write("Random Access Memory\n")
            f.write("Solid State Drive\n")
            f.write("Universal Serial Bus\n")

    if not os.path.exists(SHORT_NAMES_FILE):
        print(f"Creating dummy file: {SHORT_NAMES_FILE}")
        with open(SHORT_NAMES_FILE, 'w') as f:
            f.write("GPU\n")
            f.write("RAM\n")
            f.write("USB-A\n") 
            f.write("Processing Unit Central\n") 

    find_matches_with_ollama()