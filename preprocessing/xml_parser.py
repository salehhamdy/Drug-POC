import os, sys, json
from lxml import etree
from tqdm import tqdm

INPUT_XML   = "data/raw/full_database.xml"          # adjust if filename differs
OUTPUT_JSON = "data/processed/parsed_drugs.json"


def parse_xml(xml_path: str, out_path: str) -> None:
    if not os.path.exists(xml_path):
        sys.exit(f"[ERROR] XML file not found: {xml_path}")

    # Iterate over *closing* </drug> tags; `{*}` makes us namespace-agnostic
    context = etree.iterparse(xml_path, events=("end",), tag="{*}drug")

    records = []
    for _, drug in tqdm(context, desc="Parsing <drug> elements"):
        rec = {
            "drugbank_id": drug.findtext(".//{*}drugbank-id[@primary='true']")
                           or drug.findtext(".//{*}drugbank-id"),
            "name":        drug.findtext(".//{*}name"),
            "description": drug.findtext(".//{*}description"),
            "cas_number":  drug.findtext(".//{*}cas-number"),
            "state":       drug.findtext(".//{*}state"),
            "approval_status": drug.findtext(".//{*}groups/{*}group"),
        }
        if rec["name"] or rec["description"]:
            records.append(rec)

        drug.clear()        # free memory as we stream

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"[✓] Parsed {len(records)} drug records → {out_path}")


if __name__ == "__main__":
    parse_xml(INPUT_XML, OUTPUT_JSON)