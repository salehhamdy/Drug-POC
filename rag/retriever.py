"""
Light-weight embedding retriever
────────────────────────────────
• Loads the FAISS index + text metadata saved by embeddings/embedding_utils.py
• Uses the same SentenceTransformer encoder to embed queries.
• Returns LangChain Document objects (page_content + metadata).
"""

import argparse
import json
from pathlib import Path
from typing import List

import faiss                   # type: ignore
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain.schema import Document

# ───────── configuration ─────────
EMBED_DIR   = Path(__file__).resolve().parent.parent / "embeddings"
MODEL_NAME  = "sentence-transformers/all-MiniLM-L6-v2"
DEVICE      = "cpu"            # change to "cuda" if you have a GPU

# ───────── helpers ───────────────
def load_resources():
    """Returns (encoder, faiss_index, doc_texts, doc_ids)"""
    # texts
    docs_path = EMBED_DIR / "docs.json"
    ids_path  = EMBED_DIR / "ids.json"
    index_path = EMBED_DIR / "faiss_index.bin"

    if not (docs_path.exists() and ids_path.exists() and index_path.exists()):
        raise FileNotFoundError(
            "❌ FAISS index or metadata missing – run embeddings/embedding_utils.py --build first."
        )

    texts = json.loads(docs_path.read_text(encoding="utf-8"))
    ids   = json.loads(ids_path.read_text(encoding="utf-8"))
    index = faiss.read_index(str(index_path))

    encoder = SentenceTransformer(MODEL_NAME, device=DEVICE)
    return encoder, index, texts, ids


def retrieve(query: str, k: int = 5) -> List[Document]:
    """Return top-k Documents for the query."""
    encoder, index, texts, ids = load_resources()

    q_emb = encoder.encode([query], normalize_embeddings=True).astype("float32")
    scores, idxs = index.search(q_emb, k)          # (1, k)

    docs: List[Document] = []
    for rank, (score, idx) in enumerate(zip(scores[0], idxs[0]), start=1):
        meta = {
            "rank":   int(rank),
            "score":  float(score),
            "doc_id": ids[idx],
        }
        docs.append(Document(page_content=texts[idx], metadata=meta))
    return docs


# ───────── CLI (optional) ─────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help="Natural-language query")
    ap.add_argument("--topk",  type=int, default=5, help="Number of results")
    args = ap.parse_args()

    for doc in retrieve(args.query, args.topk):
        print(f"\n— rank {doc.metadata['rank']}  score={doc.metadata['score']:.4f}")
        print(doc.page_content[:400], "...")
