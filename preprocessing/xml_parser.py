import json, os, sys
from lxml import etree
from tqdm import tqdm
from typing import List, Dict

IN_XML   = "data/raw/full_database.xml"
OUT_JSON = "data/processed/parsed_drugs.json"


# ------------------------------------------------------------------ helpers
def text(e: etree._Element, path: str):
    """Return stripped .text of first match or None."""
    x = e.find(path)
    return x.text.strip() if x is not None and x.text else None


def texts(e: etree._Element, path: str) -> List[str]:
    """Return stripped .text of all matches."""
    return [x.text.strip() for x in e.findall(path) if x.text]


def attr_texts(e: etree._Element, path: str, attr: str) -> List[str]:
    """Return attribute values (@attr) for all matches."""
    return [x.get(attr).strip() for x in e.findall(path) if x.get(attr)]


# ------------------------------------------------------------------ main
def parse() -> None:
    if not os.path.exists(IN_XML):
        sys.exit(f"[ERROR] XML file not found: {IN_XML}")

    context = etree.iterparse(IN_XML, events=("end",), tag="{*}drug")
    records: List[Dict] = []

    for _ev, d in tqdm(context, desc="Parsing <drug>"):
        # ---------- identifiers
        primary_id = text(d, ".//{*}drugbank-id[@primary='true']")
        if not primary_id:  # fallback to first id if none flagged primary
            primary_id = text(d, ".//{*}drugbank-id")
        secondary_ids = [
            x.text.strip() for x in d.findall(".//{*}drugbank-id")
            if (x.text and x.get("primary") != "true")
        ]

        # ---------- build record
        rec = {
            "primary_id":    primary_id,
            "secondary_ids": secondary_ids,
            "unii":          text(d, ".//{*}unii"),
            "cas_number":    text(d, ".//{*}cas-number"),

            # basic info
            "name":          text(d, ".//{*}name"),
            "description":   text(d, ".//{*}description"),
            "indication":    text(d, ".//{*}indication"),
            "pharmacodynamics": text(d, ".//{*}pharmacodynamics"),
            "mechanism_of_action": text(d, ".//{*}mechanism-of-action"),

            # physical / chemical
            "average_mass":       text(d, ".//{*}average-mass"),
            "monoisotopic_mass":  text(d, ".//{*}monoisotopic-mass"),
            "state":              text(d, ".//{*}state"),
            "calculated_properties": [
                {
                    "kind":  x.get("kind"),
                    "value": text(x, ".//{*}value"),
                }
                for x in d.findall(".//{*}calculated-properties/{*}property")
            ],
            "experimental_properties": [
                {
                    "kind":  x.get("kind"),
                    "value": text(x, ".//{*}value"),
                    "source":text(x, ".//{*}source"),
                }
                for x in d.findall(".//{*}experimental-properties/{*}property")
            ],

            # pharmacokinetics
            "absorption":          text(d, ".//{*}absorption"),
            "metabolism":          text(d, ".//{*}metabolism"),
            "half_life":           text(d, ".//{*}half-life"),
            "protein_binding":     text(d, ".//{*}protein-binding"),
            "clearance":           text(d, ".//{*}clearance"),
            "volume_of_distribution": text(d, ".//{*}volume-of-distribution"),
            "route_of_elimination":   text(d, ".//{*}route-of-elimination"),

            # classification & grouping
            "groups":          texts(d, ".//{*}groups/{*}group"),
            "classyfire": {
                "kingdom":    text(d, ".//{*}classification/{*}kingdom"),
                "superclass": text(d, ".//{*}classification/{*}superclass"),
                "class":      text(d, ".//{*}classification/{*}class"),
                "subclass":   text(d, ".//{*}classification/{*}subclass"),
            },
            "atc_codes":      attr_texts(d, ".//{*}atc-codes/{*}atc-code", "code"),
            "mesh_categories": texts(d, ".//{*}categories/{*}category/{*}category"),

            # interactions
            "drug_interactions": [
                {
                    "drugbank_id": text(x, ".//{*}drugbank-id"),
                    "name":        text(x, ".//{*}name"),
                    "description": text(x, ".//{*}description"),
                }
                for x in d.findall(".//{*}drug-interaction")
            ],
            "food_interactions": texts(d, ".//{*}food-interaction"),

            # commercial / regulatory
            "products": [
                {
                    "name":       text(p, ".//{*}name"),
                    "labeller":   text(p, ".//{*}labeller"),
                    "dosage_form":text(p, ".//{*}dosage-form"),
                    "route":      text(p, ".//{*}route"),
                    "started":    text(p, ".//{*}started-marketing-on"),
                    "ended":      text(p, ".//{*}ended-marketing-on"),
                    "country":    text(p, ".//{*}country"),
                    "approved":   text(p, ".//{*}approved"),
                }
                for p in d.findall(".//{*}products/{*}product")
            ],
            "patents": [
                {
                    "number":   text(p, ".//{*}number"),
                    "country":  text(p, ".//{*}country"),
                    "expires":  text(p, ".//{*}expires"),
                }
                for p in d.findall(".//{*}patents/{*}patent")
            ],
            "prices": [
                {
                    "description": text(p, ".//{*}description"),
                    "cost":        text(p, ".//{*}cost"),
                    "unit":        text(p, ".//{*}unit"),
                }
                for p in d.findall(".//{*}prices/{*}price")
            ],

            # biological interactions (IDs only for brevity)
            "targets":      attr_texts(d, ".//{*}targets/{*}target", "id"),
            "enzymes":      attr_texts(d, ".//{*}enzymes/{*}enzyme", "id"),
            "carriers":     attr_texts(d, ".//{*}carriers/{*}carrier", "id"),
            "transporters": attr_texts(d, ".//{*}transporters/{*}transporter", "id"),

            # pathways & reactions (just IDs / names)
            "pathways": [
                text(p, ".//{*}name") for p in d.findall(".//{*}pathways/{*}pathway")
            ],
            "reactions": attr_texts(d, ".//{*}reactions/{*}reaction", "id"),

            # SNPs (ids only)
            "snp_effects": attr_texts(d, ".//{*}snp-effects/{*}snp-effect", "rs-id"),
            "snp_adrs":    attr_texts(d, ".//{*}snp-adverse-drug-reactions/{*}snp-adverse-drug-reaction", "rs-id"),

            # references & external
            "external_identifiers": [
                {
                    "resource":  text(x, ".//{*}resource"),
                    "identifier":text(x, ".//{*}identifier"),
                }
                for x in d.findall(".//{*}external-identifiers/{*}external-identifier")
            ],
            "external_links": [
                {
                    "resource": x.get("resource"),
                    "url":      x.text.strip() if x.text else None
                }
                for x in d.findall(".//{*}external-links/{*}external-link")
            ],
            "synonyms": texts(d, ".//{*}synonyms/{*}synonym"),
        }

        records.append(rec)
        d.clear()   # free memory

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"[✓] Parsed {len(records):,} drug records → {OUT_JSON}")


if __name__ == "__main__":
    parse()