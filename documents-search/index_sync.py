import os
import json
import hashlib
import argparse
from typing import Dict, List
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration Loaded from .env ---
DATA_DIR = os.getenv("DATA_DIR", "./data")
STORAGE_DIR = os.getenv("STORAGE_DIR", "./storage")
EMBED_MODEL = os.getenv("EMBED_MODEL", "qwen3-embedding:8b")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:latest")

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
    """Initializes or loads the index."""
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Initialize Ollama embedding model
    print(f"Loading embedding model: {EMBED_MODEL}...")
    embed_model = OllamaEmbedding(model_name=EMBED_MODEL, base_url=ollama_base_url)

    # Initialize Ollama LLM
    llm = Ollama(model=LLM_MODEL, base_url=ollama_base_url)
    
    # Storage context (Vector DB)
    if not os.path.exists(STORAGE_DIR):
        print(f"Creating a new index in {STORAGE_DIR}...")
        os.makedirs(STORAGE_DIR, exist_ok=True)
        # Create an empty index to set up the storage structure
        index = VectorStoreIndex([], embed_model=embed_model, llm=llm)
        index.storage_context.persist(persist_dir=STORAGE_DIR)
        return index
    else:
        print(f"Loading index from {STORAGE_DIR}...")
        storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
        return load_index_from_storage(storage_context, embed_model=embed_model, llm=llm)

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

    if len(stored_hashes) > 0 and not force:
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
    elif force:
        print("Force re-index enabled. Skipping confirmation.") 

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

    # 6. Delete missing files from the index
    if files_to_delete:
        print(f"\nDeleting {len(files_to_delete)} records from the index...")
        doc_store = index.storage_context.docstore
        
        docs_to_delete_ids = []
        for doc_id, doc in doc_store.docs.items():
            if doc.metadata.get('file_path') in files_to_delete:
                docs_to_delete_ids.append(doc_id)
                
        for doc_id in docs_to_delete_ids:
            index.delete_ref_doc(doc_id, delete_from_docstore=True) 
            print(f"  -> Deleted doc_id {doc_id} (file was removed).")

    # 7. Index new/modified files
    if files_to_process:
        print(f"\nIndexing {len(files_to_process)} new/modified files...")
        
        # For modified files, first delete the old records
        doc_store = index.storage_context.docstore
        for filepath in files_to_process:
            for doc_id, doc in doc_store.docs.items():
                if doc.metadata.get('file_path') == filepath:
                    print(f"  -> Deleting old version for {os.path.basename(filepath)}")
                    index.delete_ref_doc(doc_id, delete_from_docstore=True) 

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

    # 8. Save the updated index and hashes
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    save_hashes(current_hashes)
    print("\n[OK] Synchronization complete. Index updated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index and synchronize documents for semantic search.")
    parser.add_argument("-f", "--force", action="store_true", help="Force re-index without confirmation prompt")
    args = parser.parse_args()
    main(force=args.force)