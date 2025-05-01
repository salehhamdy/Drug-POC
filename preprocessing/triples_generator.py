import json, os
import pandas as pd
from tqdm import tqdm

INPUT  = "data/processed/nlp_processed.json"
OUTPUT = "data/processed/kg_triples.csv"

def main() -> None:
    if not os.path.exists(INPUT):
        raise FileNotFoundError(INPUT)

    with open(INPUT, encoding="utf-8") as f:
        drugs = json.load(f)

    triples = []
    for d in tqdm(drugs, desc="Building triples"):
        name = d["name"]
        if d["cas_number"]:
            triples.append((name, "has_cas_number", d["cas_number"]))
        if d["state"]:
            triples.append((name, "has_state", d["state"]))
        if d["approval_status"]:
            triples.append((name, "approval_status", d["approval_status"]))

        for txt, label in d.get("entities", []):
            if label == "CHEMICAL":
                triples.append((name, "related_chemical", txt))
            elif label in {"DISEASE", "PATHOLOGICAL_FUNCTION"}:
                triples.append((name, "indication", txt))

    df = pd.DataFrame(triples, columns=["source", "relation", "target"])
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    df.to_csv(OUTPUT, index=False)

    print(f"[✓] Wrote {len(df):,} triples → {OUTPUT}")

if __name__ == "__main__":
    main()
