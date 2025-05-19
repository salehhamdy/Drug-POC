import json, pandas as pd
from pathlib import Path
from tqdm import tqdm

IN_JSON = Path("data/processed/nlp_processed.json")
OUT_CSV = Path("data/processed/kg_triples.csv")

def add(bag, s, r, t):
    if s and t:
        bag.add((s, r, t))

def main():
    drugs = json.loads(IN_JSON.read_text(encoding="utf-8"))
    triples = set()

    for d in tqdm(drugs, desc="Building triples"):
        drug = d["name"]

        # IDs & synonyms
        add(triples, drug, "has_primary_id", d.get("primary_id", ""))
        for sid in d.get("secondary_ids", []):
            add(triples, drug, "has_secondary_id", sid)
        for syn in d.get("synonyms", []):
            add(triples, drug, "synonym", syn)

        # groups / categories / classyfire
        for g in d.get("groups", []):
            add(triples, drug, "in_group", g)
        for atc in d.get("atc_codes", []):
            add(triples, drug, "has_atc_code", atc)
        for mesh in d.get("mesh_categories", []):
            add(triples, drug, "has_mesh_category", mesh)

        cf = d.get("classyfire", {})
        for k, v in cf.items():
            if v:
                add(triples, drug, f"classified_as_{k}", v)

        # physical props
        if d.get("state"):
            add(triples, drug, "has_state", d["state"])
        if d.get("average_mass"):
            add(triples, drug, "has_average_mass", d["average_mass"])
        if d.get("monoisotopic_mass"):
            add(triples, drug, "has_monoisotopic_mass", d["monoisotopic_mass"])

        # interactions
        for x in d.get("drug_interactions", []):
            add(triples, drug, "interacts_with", x.get("name", ""))
        for fi in d.get("food_interactions", []):
            add(triples, drug, "food_interaction", fi)

        # BioBERT entities
        for txt, label in d.get("entities", []):
            add(triples, drug, f"mentions_{label.lower()}", txt)

        # biological actors
        for t in d.get("targets", []):
            add(triples, drug, "has_target", t)
        for e in d.get("enzymes", []):
            add(triples, drug, "has_enzyme", e)
        for c in d.get("carriers", []):
            add(triples, drug, "has_carrier", c)
        for tr in d.get("transporters", []):
            add(triples, drug, "has_transporter", tr)

        # pathways / reactions
        for pw in d.get("pathways", []):
            add(triples, drug, "in_pathway", pw)
        for rx in d.get("reactions", []):
            add(triples, drug, "has_reaction", rx)

        # SNPs
        for rs in d.get("snp_effects", []) + d.get("snp_adrs", []):
            add(triples, drug, "associated_snp", rs)

        # dosages
        for ds in d.get("dosages", []):
            descr = f"{ds.get('dosage_form','')}|{ds.get('route','')}|{ds.get('strength','')}"
            add(triples, drug, "has_dosage", descr)

        # products
        for p in d.get("products", []):
            pname = p.get("name")
            if pname:
                add(triples, drug, "has_product", pname)
                add(triples, pname, "product_of", drug)

        # patents / prices
        for p in d.get("patents", []):
            add(triples, drug, "has_patent", p.get("number", ""))
        for p in d.get("prices", []):
            add(triples, drug, "has_price", p.get("description", ""))

        # external IDs & links
        for ex in d.get("external_identifiers", []):
            add(triples, drug, "has_external_id",
                f"{ex.get('resource')}:{ex.get('identifier')}")
        for link in d.get("external_links", []):
            add(triples, drug, "has_external_link", link.get("url", ""))

    # save
    df = pd.DataFrame(sorted(triples), columns=["source", "relation", "target"])
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"[✓] Wrote {len(df):,} triples → {OUT_CSV}")

if __name__ == "__main__":
    main()