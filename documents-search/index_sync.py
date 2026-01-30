import os

# Load .env first to check EMBED_PROVIDER before setting HF offline mode
from dotenv import load_dotenv
load_dotenv()

# Enable offline mode for HuggingFace only if using HuggingFace provider
EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "huggingface").lower()
if EMBED_PROVIDER == "huggingface":
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"  # Suppress model loading warnings

import json
import hashlib
import argparse
import shutil
from typing import Dict, List
import chromadb
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.core.node_parser import SentenceSplitter

# Conditional imports based on provider
if EMBED_PROVIDER == "huggingface":
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
else:
    from llama_index.embeddings.ollama import OllamaEmbedding

# --- Configuration Loaded from .env ---
DATA_DIR = os.getenv("DATA_DIR", "./data")
STORAGE_DIR = os.getenv("STORAGE_DIR", "./storage")
EMBED_MODEL = os.getenv("EMBED_MODEL", "lang-uk/ukr-paraphrase-multilingual-mpnet-base" if EMBED_PROVIDER == "huggingface" else "embeddinggemma:latest")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:4b")

HASH_FILE = os.path.join(STORAGE_DIR, "file_hashes.json")

# --- New: Allowed Document Extensions ---
# SimpleDirectoryReader supports various formats (PDF, DOCX, XLSX, TXT, CSV, etc.)
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx',
    '.xls', '.xlsx',
    '.txt', '.csv', '.md', '.html', # Include common text/data formats
}

# --- Utilities ---

def calculate_sha256(filepath: str) -> str:
    """Calculates the SHA-256 hash for a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as file:
        while True:
            chunk = file.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def load_hashes() -> Dict[str, str]:
    """Loads stored file hashes."""
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_hashes(hashes: Dict[str, str]):
    """Saves the current file hashes."""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    with open(HASH_FILE, 'w') as f:
        json.dump(hashes, f, indent=4)

def initialize_index() -> VectorStoreIndex:
    """Initializes or loads the index using Chroma for binary vector storage."""
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Initialize embedding model based on provider
    print(f"Loading embedding model: {EMBED_MODEL} (provider: {EMBED_PROVIDER})...")
    if EMBED_PROVIDER == "huggingface":
        embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)
    else:
        embed_model = OllamaEmbedding(model_name=EMBED_MODEL, base_url=ollama_base_url)

    # Initialize Ollama LLM
    llm = Ollama(model=LLM_MODEL, base_url=ollama_base_url)

    # Initialize Chroma with persistent storage (binary format)
    os.makedirs(STORAGE_DIR, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=STORAGE_DIR)
    chroma_collection = chroma_client.get_or_create_collection("documents")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    # Check if this is a new index or existing
    if chroma_collection.count() == 0:
        print(f"Creating a new index in {STORAGE_DIR}...")
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex([], storage_context=storage_context, embed_model=embed_model, llm=llm)
    else:
        print(f"Loading index from {STORAGE_DIR} ({chroma_collection.count()} vectors)...")
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context, embed_model=embed_model, llm=llm)

    return index

def get_files_to_process(current_hashes: Dict[str, str], stored_hashes: Dict[str, str]) -> tuple[List[str], List[str], List[str]]:
    """Determines which files need to be added, updated, or deleted."""

    files_to_add_or_update = []
    files_to_delete = []

    # Identify new or modified files
    for filepath, current_hash in current_hashes.items():
        if filepath not in stored_hashes or stored_hashes[filepath] != current_hash:
            files_to_add_or_update.append(filepath)

    # Identify deleted files
    for filepath in stored_hashes.keys():
        if filepath not in current_hashes:
            files_to_delete.append(filepath)

    # Identify unchanged files
    files_unchanged = [
        filepath for filepath, current_hash in current_hashes.items()
        if filepath in stored_hashes and stored_hashes[filepath] == current_hash
    ]

    return files_to_add_or_update, files_to_delete, files_unchanged

# --- Main Logic ---

def main(force: bool = False):
    """Main indexing and synchronization function."""
    print(f"Using DATA_DIR: {DATA_DIR}, STORAGE_DIR: {STORAGE_DIR}")

    if not os.path.exists(DATA_DIR):
        print(f"Error: Data directory '{DATA_DIR}' not found.")
        return

    # 1. Load previous hashes
    stored_hashes = load_hashes()

    if force:
        # Force mode: confirm and delete storage folder
        print(f"WARNING: Force re-index will delete the entire index at '{STORAGE_DIR}'")
        while True:
            user_input = input("Are you sure you want to delete the index and re-index all files? (y/n): ").lower()
            if user_input == 'y':
                if os.path.exists(STORAGE_DIR):
                    shutil.rmtree(STORAGE_DIR)
                    print(f"Deleted storage folder: {STORAGE_DIR}")
                stored_hashes = {}  # Reset stored hashes since we deleted the folder
                break
            elif user_input == 'n':
                print("Force re-index canceled.")
                return
            else:
                print("Invalid input. Please enter 'y' (yes) or 'n' (no).")
    elif len(stored_hashes) > 0:
        print(f"Loaded {len(stored_hashes)} stored file hashes.")
        while True:
            user_input = input("Changes detected. Proceed with re-indexing and synchronization? (y/n): ").lower()
            if user_input == 'y':
                break
            elif user_input == 'n':
                print("Synchronization canceled.")
                return
            else:
                print("Invalid input. Please enter 'y' (yes) or 'n' (no).")

    # 2. Calculate current hashes
    current_hashes = {}
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            filepath = os.path.join(root, file)

            # --- MODIFIED FILTER LOGIC ---
            file_extension = os.path.splitext(file)[1].lower()

            # Filter out non-document files (system files, temporary, non-allowed extensions)
            if file.startswith(('.', '~$')) or file.endswith(('~', '#', '.pyc', '.DS_Store')) or file_extension not in ALLOWED_EXTENSIONS:
                 continue

            try:
                current_hashes[filepath] = calculate_sha256(filepath)
            except Exception as e:
                print(f"Error calculating hash for {filepath}: {e}")

    # 3. Determine changes
    if force:
        # Force mode: re-index all files
        files_to_process = list(current_hashes.keys())
        files_to_delete = [f for f in stored_hashes.keys() if f not in current_hashes]
        files_unchanged = []
    else:
        files_to_process, files_to_delete, files_unchanged = get_files_to_process(current_hashes, stored_hashes)

    print("-" * 50)
    print(f"Files to index: {len(files_to_process)}" + (" (forced)" if force else ""))
    print(f"Deleted files found: {len(files_to_delete)}")
    print(f"Unchanged files: {len(files_unchanged)}")
    print("-" * 50)

    # 4. Skip if nothing to do (only in non-force mode)
    if not files_to_process and not files_to_delete:
        print("No changes detected in files. Synchronization is not needed.")
        return

    # 5. Initialize/Load Index
    index = initialize_index()

    # 6. Delete missing files from the index (using Chroma's where filter)
    if files_to_delete:
        print(f"\nDeleting {len(files_to_delete)} records from the index...")
        chroma_collection = index.storage_context.vector_store._collection

        for filepath in files_to_delete:
            # Delete all vectors with matching file_path metadata
            chroma_collection.delete(where={"file_path": filepath})
            print(f"  -> Deleted vectors for: {os.path.basename(filepath)}")

    # 7. Index new/modified files
    if files_to_process:
        print(f"\nIndexing {len(files_to_process)} new/modified files...")

        # For modified files, first delete the old vectors from Chroma
        chroma_collection = index.storage_context.vector_store._collection
        for filepath in files_to_process:
            # Check if file already exists in index and delete old vectors
            existing = chroma_collection.get(where={"file_path": filepath})
            if existing and existing['ids']:
                chroma_collection.delete(where={"file_path": filepath})
                print(f"  -> Deleting old version for {os.path.basename(filepath)}")

        # Read documents
        reader = SimpleDirectoryReader(input_files=files_to_process)
        documents = reader.load_data()

        # Split documents into nodes
        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        nodes = splitter.get_nodes_from_documents(documents, show_progress=True)

        # Insert nodes into the index (this handles embedding automatically)
        index.insert_nodes(nodes, show_progress=True)

        for filepath in files_to_process:
            print(f"  -> Indexed/Updated: {os.path.basename(filepath)}")

    # 8. Save file hashes (Chroma auto-persists vectors)
    save_hashes(current_hashes)
    print("\n[OK] Synchronization complete. Index updated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index and synchronize documents for semantic search.")
    parser.add_argument("-f", "--force", action="store_true", help="Force complete re-index by deleting existing storage and re-indexing all files")
    args = parser.parse_args()
    main(force=args.force)
