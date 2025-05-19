import json, math, os, sys, torch
from pathlib import Path
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from tqdm import tqdm

IN_JSON  = Path("data/processed/parsed_drugs.json")
OUT_JSON = Path("data/processed/nlp_processed.json")

TEXT_FIELDS = [
    "description",
    "indication",
    "pharmacodynamics",
    "mechanism_of_action",
    "metabolism",
    "absorption",
    "toxicity",
]

PRIMARY_MODEL = "kamalkraj/biobert_ner"   # public biomedical NER
FALLBACK_MODEL = "dslim/bert-base-NER"    # generic, always public

def get_device() -> int:
    return 0 if torch.cuda.is_available() else -1

def truncated(txt: str, max_toks: int = 512) -> str:
    toks = txt.split()
    return " ".join(toks[:max_toks]) if len(toks) > max_toks else txt

def load_pipeline(model_id: str):
    print(f"[INFO] Loading model: {model_id}")
    tok = AutoTokenizer.from_pretrained(model_id)
    mdl = AutoModelForTokenClassification.from_pretrained(model_id)
    return pipeline(
        "ner",
        model=mdl,
        tokenizer=tok,
        aggregation_strategy="simple",
        device=get_device(),
    )

def main() -> None:
    if not IN_JSON.exists():
        sys.exit(f"[ERROR] {IN_JSON} not found. Run xml_parser.py first.")

    drugs = json.loads(IN_JSON.read_text())
    print(f"[INFO] Loaded {len(drugs):,} drug records")

    # --------------------------------------------------- load model with fallback
    try:
        ner = load_pipeline(PRIMARY_MODEL)
    except Exception as e:
        print(f"[WARN] Primary model unavailable → {e}")
        print(f"[INFO] Falling back to {FALLBACK_MODEL}")
        ner = load_pipeline(FALLBACK_MODEL)

    # --------------------------------------------------- gather texts
    texts, idx_map = [], []
    for i, d in enumerate(tqdm(drugs, desc="Collect texts")):
        combined = "  ".join(d.get(f, "") or "" for f in TEXT_FIELDS).strip()
        if combined:
            texts.append(truncated(combined))
            idx_map.append(i)
        else:
            d["entities"] = []

    if not texts:
        print("[WARN] No descriptions found → nothing to annotate.")
        OUT_JSON.write_text(json.dumps(drugs, indent=2))
        return

    # --------------------------------------------------- batched inference
    BATCH = 64 if get_device() == -1 else 256
    batches = math.ceil(len(texts) / BATCH)

    for b in tqdm(range(batches), desc="NER inference"):
        batch_texts = texts[b * BATCH : (b + 1) * BATCH]
        outputs = ner(batch_texts)
        for j, ents in enumerate(outputs):
            gidx = idx_map[b * BATCH + j]
            uniq = {(e["word"].strip(), e["entity_group"]) for e in ents}
            drugs[gidx]["entities"] = sorted(uniq)

    # --------------------------------------------------- save
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(drugs, indent=2))
    print(f"[✓] Annotated {len(drugs):,} drugs → {OUT_JSON}")

if __name__ == "__main__":
    main()