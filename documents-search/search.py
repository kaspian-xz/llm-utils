import os
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration Loaded from .env ---
STORAGE_DIR = os.getenv("STORAGE_DIR", "./storage")
# HuggingFace embedding model (multilingual)
EMBED_MODEL = "intfloat/multilingual-e5-large"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:latest")

# --- Main Logic ---

def main():
    """Main search application function."""
    if not os.path.exists(STORAGE_DIR):
        print(f"Error: Index directory '{STORAGE_DIR}' not found. Please run index_sync.py first.")
        return

    print("Setting up models and loading index...")

    try:
        # Initialize HuggingFace embedding model (multilingual)
        print(f"Loading embedding model: {EMBED_MODEL}...")
        embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)

        # Initialize Ollama LLM
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/")
        llm = Ollama(model=LLM_MODEL, base_url=ollama_base_url, request_timeout=120.0)

        # Load the index
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        index = load_index_from_storage(storage_context, embed_model=embed_model, llm=llm)

        # Create QueryEngine
        query_engine = index.as_query_engine(
            llm=llm,
            similarity_top_k=3,
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
            response = query_engine.query(query)

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