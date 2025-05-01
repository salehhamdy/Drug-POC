import json, os
from transformers import pipeline
from tqdm import tqdm

INPUT  = "data/processed/parsed_drugs.json"
OUTPUT = "data/processed/nlp_processed.json"

def main() -> None:
    if not os.path.exists(INPUT):
        raise FileNotFoundError(INPUT)

    nlp = pipeline(
        "ner",
        model="dmis-lab/biobert-base-cased-v1.2",
        aggregation_strategy="simple"
    )

    with open(INPUT, encoding="utf-8") as f:
        drugs = json.load(f)

    for drug in tqdm(drugs, desc="NER on descriptions"):
        text = drug.get("description") or ""
        if text:
            ents = nlp(text[:512])          # trim long texts
            drug["entities"] = [
                (e["word"], e["entity_group"]) for e in ents
            ]
        else:
            drug["entities"] = []

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(drugs, f, indent=2)

    print(f"[✓] Annotated {len(drugs)} drugs → {OUTPUT}")

if __name__ == "__main__":
    main()
