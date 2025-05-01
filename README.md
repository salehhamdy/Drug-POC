Below is a **drop-in `README.md`** you can copy to your project root (`drug-substitution-poc/`).  
It documents the directory layout, full setup on Windows or Linux, every pipeline step, and common troubleshooting tips.

---

```markdown
# Drug-Substitution PoC 📦

A lightweight proof-of-concept that turns a raw DrugBank-style XML dump into a **Knowledge Graph (KG)** and exposes it to Retrieval-Augmented Generation (RAG) and simple CLI queries.

| Stage | Tech |
|-------|------|
| Parsing | `lxml` streaming XML |
| NLP / NER | Hugging Face Transformers (`BioBERT`) |
| KG triples | CSV → Neo4j |
| Retrieval + LLM (future) | `rag/` package |

---

## 1.  Folder Structure

```
drug-substitution-poc/
├─ data/
│  ├─ raw/              # put full_database.xml here
│  └─ processed/        # JSON + CSV outputs land here
├─ preprocessing/       # three pipeline scripts
├─ embeddings/          # (future) sentence/vector embeddings
├─ kg/                  # load & query Neo4j
├─ rag/                 # retriever + generator (future)
├─ interface/           # simple CLI
├─ requirements.txt
└─ README.md
```

---

## 2.  Quick Start (Windows / Linux)

```bash
git clone <your-repo-url> drug-substitution-poc
cd drug-substitution-poc

# ⚠️ Use Python 3.11 (3.12+ is OK, 3.13 fails for some libs)
py -3.11 -m venv venv        # Windows
# python3.11 -m venv venv    # Linux/macOS
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3.  Place the XML Dump

```
data/raw/full_database.xml     <--  ≈1.5 GB DrugBank-style file
```

If your file has a different name, adjust `INPUT_XML` inside
`preprocessing/xml_parser.py`.

---

## 4.  Run the ETL Pipeline

| Step | Command | Output |
|------|---------|--------|
| 1️⃣ Parse XML | `python preprocessing\xml_parser.py` | `data/processed/parsed_drugs.json` |
| 2️⃣ NER with BioBERT | `python preprocessing\text_processing.py` | `data/processed/nlp_processed.json` |
| 3️⃣ Generate KG triples | `python preprocessing\triples_generator.py` | `data/processed/kg_triples.csv` |

### What you should see

```text
Parsing drugs: 100%|█████████| 2500/2500
[✓] Parsed 2500 drug records → data/processed/parsed_drugs.json
Processed 2500 descriptions with BioBERT NER
Saved to data/processed/nlp_processed.json
Generated 12 300 triples
Saved to data/processed/kg_triples.csv
```

---

## 5.  Load into Neo4j (optional)

1. Install Neo4j Desktop or run `docker run -p7474:7474 -p7687:7687 neo4j:5`.
2. Copy `kg_triples.csv` into Neo4j’s `import/` folder.
3. Run:

```cypher
LOAD CSV WITH HEADERS FROM 'file:///kg_triples.csv' AS row
MERGE (s:Entity {name: row.source})
MERGE (t:Entity {name: row.target})
MERGE (s)-[r:RELATION {type: row.relation}]->(t);
```

---

## 6.  Simple CLI Demo

_Edit `interface/cli.py` to suit—example snippet:_

```python
import pandas as pd
triples = pd.read_csv("data/processed/kg_triples.csv")

drug = input("Drug name ➜ ").strip().title()
print(triples[triples["source"] == drug].head(20))
```

```bash
python interface\cli.py
Drug name ➜ Lepirudin
```

---

## 7.  Requirements Reference

```text
transformers
torch
sentence-transformers
lxml
pandas
neo4j
tqdm
```

Install GPU PyTorch if you want faster BioBERT inference.

---

## 8.  Troubleshooting Guide

| Issue | Fix |
|-------|-----|
| `Parsed 0 drugs` | The XML uses a different element. Run the tag-inspection snippet in the README and change `tag="{*}<your_tag>"` in `xml_parser.py`. |
| `FileNotFoundError: full_database.xml` | Check path → `data/raw/full_database.xml`. |
| Very slow NER | Edit `text_processing.py` to slice description (`text[:400]`) or batch processing. |
| Windows build errors | Ensure you’re on Python 3.11 and **not** 3.13. Re-create venv if needed. |

---

## 9.  Roadmap

* ⚙️  Add `embeddings/embedding_utils.py` with SMR-DDI sentence vectors.  
* 🤖  Build `rag/retriever.py` + `rag/generator.py` → Retrieval-Augmented QA.  
* 🖥️  Streamlit / GUI under `interface/gui/`.  
* 🐳  Dockerfile to bundle Neo4j + API.

---

## 10.  License

MIT — see `LICENSE` file.

---

**Happy Hacking!**  Feel free to open issues or PRs as you extend the PoC.
```

---

### How to use

1. Create (or overwrite) `drug-substitution-poc/README.md` with the content above.  
2. Commit & push:

```bash
git add README.md
git commit -m "Add detailed README with setup & pipeline instructions"
git push origin main
```

The README now fully documents installation, pipeline commands, troubleshooting, and the future roadmap.