import sqlite3
import ollama
import os
import argparse
import sys
import json
import datetime
from typing import List, Tuple

# Configuration
# Updated to point to the centralized NovaHub database
DB_PATH = "c:/AI Fusion Labs/NovaHub-Project/database/nova_memory.db"
EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_FILES = ["RESEARCH_BRIEF.md", "TAVUS_PENDING.md"]

def init_db():
    """Ensure the KnowledgeVault table exists."""
    # print("[INIT] Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create text table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS KnowledgeVault (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_file TEXT,
        content_chunk TEXT,
        embedding TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    return conn

def get_embedding(text: str) -> List[float]:
    """Generate embedding using Ollama nomic-embed-text."""
    # Prefix required by nomic-embed-text training data for documents
    prompt = f"search_document: {text}"
    try:
        response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=prompt)
        return response["embedding"]
    except Exception as e:
        print(f"[ERROR] Ollama Embedding Failed: {e}")
        return []

def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """Simple chunking by paragraphs or size."""
    # Split by double newline first (paragraphs)
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def index_files(conn, files_to_index):
    """Scan and index specified files."""
    cursor = conn.cursor()
    
    total_chunks = 0
    for filename in files_to_index:
        if not os.path.exists(filename):
            # print(f"[WARN] File not found: {filename}")
            continue
            
        print(f"[INDEX] Processing {filename}...")
        
        # Clear existing entries for this specific file
        cursor.execute("DELETE FROM KnowledgeVault WHERE source_file = ?", (filename,))
        conn.commit()

        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"[ERROR] Reading file {filename}: {e}")
            continue
            
        chunks = chunk_text(content)
        
        # Optimize by getting embeddings in loop
        for chunk in chunks:
            if not chunk: continue
            
            # Reduce verbosity for automated calls
            # print(f"   > Embedding chunk ({len(chunk)} chars)...", flush=True)
            embedding = get_embedding(chunk)
            
            if embedding:
                cursor.execute(
                    "INSERT INTO KnowledgeVault (source_file, content_chunk, embedding) VALUES (?, ?, ?)",
                    (filename, chunk, json.dumps(embedding))
                )
                total_chunks += 1
        
        conn.commit()
        print(f"[SUCCESS] Indexed {filename} ({total_chunks} chunks)")

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = sum(a * a for a in v1) ** 0.5
    magnitude2 = sum(b * b for b in v2) ** 0.5
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)

def semantic_search(conn, query: str):
    """Search the KnowledgeVault."""
    print(f"[SEARCH] Query: '{query}'")
    
    query_prompt = f"search_query: {query}"
    
    try:
        response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=query_prompt)
        query_vec = response["embedding"]
    except Exception as e:
        print(f"[ERROR] Embedding Gen Failed: {e}")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT source_file, content_chunk, embedding FROM KnowledgeVault")
    rows = cursor.fetchall()
    
    results = []
    for filename, chunk, emb_json in rows:
        try:
            emb_vec = json.loads(emb_json)
            score = cosine_similarity(query_vec, emb_vec)
            results.append((score, filename, chunk))
        except:
            continue
    
    # Sort by score descending
    results.sort(key=lambda x: x[0], reverse=True)
    
    print(f"\n[RESULTS] Top Matches for '{query}':")
    print("-" * 40)
    for score, filename, chunk in results[:3]: # Top 3
        print(f"[{score:.4f}] {os.path.basename(filename)}")
        print(f"Preview: {chunk[:100]}...")
        print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Librarian Knowledge Vault Indexer")
    parser.add_argument("--index", action="store_true", help="Run full indexing process (Default list)")
    parser.add_argument("--file", type=str, help="Index a specific file path")
    parser.add_argument("--search", type=str, help="Perform semantic search with query")
    args = parser.parse_args()

    conn = init_db()

    if args.file:
        # Index specific file
        index_files(conn, [args.file])
    elif args.index:
        # Index default files
        index_files(conn, DEFAULT_FILES)
    elif args.search:
        semantic_search(conn, args.search)
    else:
        # If run with no args, assume automated default index
        index_files(conn, DEFAULT_FILES)

    conn.close()

if __name__ == "__main__":
    main()
