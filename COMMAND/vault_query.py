import sqlite3
import ollama
import os
import argparse
import sys
import json
import math

# Configuration
# Updated to point to the centralized NovaHub database
DB_PATH = "c:/AI Fusion Labs/NovaHub-Project/database/nova_memory.db"
EMBEDDING_MODEL = "nomic-embed-text"
OUTPUT_FILE = "LIBRARIAN_ADVICE.md"

def get_embedding(text):
    """Generate embedding using Ollama nomic-embed-text with query prefix."""
    # Prefix required by nomic-embed-text for queries
    prompt = f"search_query: {text}"
    try:
        response = ollama.embeddings(model=EMBEDDING_MODEL, prompt=prompt)
        return response["embedding"]
    except Exception as e:
        print(f"[ERROR] Embedding Gen Failed: {e}")
        return []

def cosine_similarity(v1, v2):
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a * a for a in v1))
    magnitude2 = math.sqrt(sum(b * b for b in v2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)

def query_vault(query_text):
    print(f"[QUERY] Processing: '{query_text}'")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Embed Query
    query_vec = get_embedding(query_text)
    if not query_vec:
        print("[ERROR] Failed to embed query.")
        conn.close()
        return

    # 2. Fetch Vectors
    cursor.execute("SELECT source_file, content_chunk, embedding FROM KnowledgeVault")
    rows = cursor.fetchall()
    
    if not rows:
        print("[WARN] Knowledge Vault is empty.")
        conn.close()
        return

    # 3. Calculate Similarity
    results = []
    for filename, chunk, emb_json in rows:
        try:
            emb_vec = json.loads(emb_json)
            score = cosine_similarity(query_vec, emb_vec)
            results.append((score, filename, chunk))
        except Exception as e:
            # print(f"[WARN] Failed to process row: {e}")
            continue
    
    # 4. Sort and Select Top 3
    results.sort(key=lambda x: x[0], reverse=True)
    top_results = results[:3]

    # 5. Write to File
    write_advice(query_text, top_results)
    
    conn.close()
    print(f"[SUCCESS] Advice written to {OUTPUT_FILE}")

def write_advice(query, results):
    """Write the results to LIBRARIAN_ADVICE.md"""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# 🧠 LIBRARIAN ADVICE\n")
        f.write(f"**Query:** {query}\n")
        f.write(f"**Generated:** {os.path.basename(__file__)}\n")
        f.write("-" * 40 + "\n\n")
        
        for i, (score, filename, chunk) in enumerate(results, 1):
            f.write(f"## Match {i} (Relevance: {score:.4f})\n")
            f.write(f"**Source:** `{filename}`\n\n")
            f.write("```text\n")
            f.write(chunk.strip())
            f.write("\n```\n")
            f.write("\n" + "-" * 20 + "\n\n")

def main():
    parser = argparse.ArgumentParser(description="Query the Knowledge Vault")
    parser.add_argument("query", type=str, help="The search query (e.g., 'Lucid battery issues')")
    args = parser.parse_args()

    if args.query:
        query_vault(args.query)
    else:
        print("[ERROR] No query provided.")

if __name__ == "__main__":
    main()
