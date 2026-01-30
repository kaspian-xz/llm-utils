import os

# Load .env first to check EMBED_PROVIDER before setting HF offline mode
from dotenv import load_dotenv
load_dotenv()

# Enable offline mode for HuggingFace only if using HuggingFace provider
EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "huggingface").lower()
if EMBED_PROVIDER == "huggingface":
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

import time
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.llms.ollama import Ollama

# Conditional imports based on provider
if EMBED_PROVIDER == "huggingface":
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
else:
    from llama_index.embeddings.ollama import OllamaEmbedding

# --- Configuration Loaded from .env ---
STORAGE_DIR = os.getenv("STORAGE_DIR", "./storage")
EMBED_MODEL = os.getenv("EMBED_MODEL", "lang-uk/ukr-paraphrase-multilingual-mpnet-base" if EMBED_PROVIDER == "huggingface" else "embeddinggemma:latest")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:4b")

# --- Main Logic ---

def main():
    """Main search application function."""
    if not os.path.exists(STORAGE_DIR):
        print(f"Error: Index directory '{STORAGE_DIR}' not found. Please run index_sync.py first.")
        return

    print("Setting up models and loading index...")

    try:
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Initialize embedding model based on provider
        print(f"Loading embedding model: {EMBED_MODEL} (provider: {EMBED_PROVIDER})...")
        if EMBED_PROVIDER == "huggingface":
            embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)
        else:
            embed_model = OllamaEmbedding(model_name=EMBED_MODEL, base_url=ollama_base_url)

        # Initialize Ollama LLM
        llm = Ollama(model=LLM_MODEL, base_url=ollama_base_url, request_timeout=720.0)

        # Load the index
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        index = load_index_from_storage(storage_context, embed_model=embed_model, llm=llm)

        # Create QueryEngine
        query_engine = index.as_query_engine(
            llm=llm,
            similarity_top_k=5,
            system_prompt="Відповідай українською мовою. Базуй відповідь лише на наданому контексті."
        )

    except Exception as e:
        print(f"Initialization error: Ensure Ollama is running and LLM model ({LLM_MODEL}) is loaded.")
        print(f"Error details: {e}")
        return

    print("\n[OK] System ready. Enter 'exit' to quit.")

    while True:
        query = input("\nYour query: ")
        if query.lower() in ["exit", "quit", "вихід"]:
            break

        print("...Searching...")
        try:
            start_time = time.perf_counter()
            response = query_engine.query(query)
            elapsed_time = time.perf_counter() - start_time
            print(f"Execution time: {elapsed_time:.4f} seconds")

            # Output the model's response
            print("\n" + "="*70)
            print("RESPONSE:")
            print(response.response)
            print("="*70)

            # Output the sources (file paths)
            source_files = set()
            print("\nFOUND IN FILES:")

            for node in response.source_nodes:
                file_path = node.metadata.get('file_path')
                if file_path:
                    source_files.add(os.path.abspath(file_path))

            if source_files:
                for path in source_files:
                    print(f"  - {path}")
            else:
                print("  - Could not find specific source files for this response.")

        except Exception as e:
            print(f"An error occurred during the query: {e}")


if __name__ == "__main__":
    main()
