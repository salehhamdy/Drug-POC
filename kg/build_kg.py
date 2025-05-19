import os
import csv
from dotenv import load_dotenv
from neo4j import GraphDatabase

def main():
    load_dotenv()  # read .env at project root

    # Neo4j connection
    uri      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user     = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    driver   = GraphDatabase.driver(uri, auth=(user, password))

    # Path _on the host_ to the CSV (we read it client-side)
    csv_path = os.getenv("KG_CSV_PATH", "data/processed/kg_triples.csv")

    with driver.session() as session:
        # 1) Ensure indexes for fast MERGE
        print("[INFO] Creating indexes if needed…")
        session.run("CREATE INDEX IF NOT EXISTS FOR (d:Drug)   ON (d.name)")
        session.run("CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.value)")
        print("[✓] Indexes ready")

        # 2) Stream each row as its own auto-commit transaction
        print(f"[INFO] Streaming load from {csv_path} …")
        count = 0
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                session.run(
                    """
                    MERGE (s:Drug   {name: $source})
                    MERGE (t:Entity {value: $target})
                    MERGE (s)-[:REL {type: $relation}]->(t)
                    """,
                    source   = row["source"],
                    target   = row["target"],
                    relation = row["relation"],
                )
                count += 1
                if count % 1000 == 0:
                    print(f"[INFO]  -- loaded {count} rows so far…")

        print(f"[✓] Streaming load complete: {count} total rows.")

    driver.close()


if __name__ == "__main__":
    main()