#!/usr/bin/env python
"""
Drug‑Substitution PoC ─ Command‑Line Interface
================================================
Run end‑to‑end pipeline steps or query the Knowledge‑Graph triples produced by
`drug‑substitution‑poc`.

Usage examples
--------------
❯ python interface/cli.py parse‑xml        # Step 1  – parse DrugBank XML
❯ python interface/cli.py ner             # Step 2  – BioBERT NER over texts
❯ python interface/cli.py triples         # Step 3  – generate KG triples
❯ python interface/cli.py all             # Run the entire ETL in sequence
❯ python interface/cli.py query "Lepirudin"  # Show relations for a drug

If invoked **without** arguments the tool drops into an interactive REPL:

❯ python interface/cli.py
Drug name ➜ _

Dependencies
------------
* Python ≥ 3.11
* pandas (for querying)
* tqdm    (nice progress bars, optional)

All other heavy‑lifting lives in the existing pipeline scripts under
`preprocessing/`.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from textwrap import dedent
from typing import List, Optional

try:
    import pandas as pd  # type: ignore
except ImportError as exc:
    print("[!] pandas is required for the `query` command – install with `pip install pandas`.")
    raise exc

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _run_step(script: Path, extra_args: Optional[List[str]] = None) -> None:
    """Execute a preprocessing script in a subprocess and stream its output."""
    if not script.exists():
        sys.exit(f"[x] Could not find script {script.relative_to(PROJECT_ROOT)}")

    cmd = [sys.executable, str(script)] + (extra_args or [])
    print(f"[▶] Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)


def parse_xml() -> None:
    """Pipeline Step 1 – parse `full_database.xml` → `parsed_drugs.json`."""
    _run_step(PROJECT_ROOT / "preprocessing" / "xml_parser.py")


def ner() -> None:
    """Pipeline Step 2 – run BioBERT NER → `nlp_processed.json`."""
    _run_step(PROJECT_ROOT / "preprocessing" / "text_processing.py")


def triples() -> None:
    """Pipeline Step 3 – create KG triples CSV."""
    _run_step(PROJECT_ROOT / "preprocessing" / "triples_generator.py")


def pipeline_all() -> None:
    """Run the full ETL (parse → NER → triples) in sequence."""
    for fn in (parse_xml, ner, triples):
        fn()


def query(drug_name: str, max_rows: int = 20) -> None:
    """Query the generated `kg_triples.csv` for relations of *drug_name*."""
    csv_path = PROCESSED_DIR / "kg_triples.csv"
    if not csv_path.exists():
        sys.exit("[x] kg_triples.csv not found – run `triples` or `all` first.")

    df = pd.read_csv(csv_path)
    mask = (df["source"].str.title() == drug_name.title()) |\
           (df["target"].str.title() == drug_name.title())
    subset = df.loc[mask]

    if subset.empty:
        print(f"[!] No relations found for '{drug_name}'.")
        return

    print(subset.head(max_rows).to_markdown(index=False))

# ---------------------------------------------------------------------------
# Interactive REPL (default action when no sub‑command is provided)
# ---------------------------------------------------------------------------

def interactive_repl() -> None:
    print("Drug‑Substitution PoC – Interactive Query")
    try:
        while True:
            user_in = input("Drug name ➜ ").strip()
            if not user_in:
                continue
            if user_in.lower() in {"quit", "exit", ":q"}:
                break
            query(user_in)
    except (KeyboardInterrupt, EOFError):
        print("\nbye 👋")

# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="drug‑cli",
        description="Run ETL pipeline steps or query KG triples.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""
            Common examples:
              python interface/cli.py all
              python interface/cli.py query "Aspirin"
        """),
    )

    sub = p.add_subparsers(dest="command", help="Choose a command (default: REPL)")

    sub.add_parser("parse-xml", help="Step 1 – parse full_database.xml")
    sub.add_parser("ner", help="Step 2 – run BioBERT NER over descriptions")
    sub.add_parser("triples", help="Step 3 – generate KG triples CSV")
    sub.add_parser("all", help="Run the full ETL pipeline (1→2→3)")

    q = sub.add_parser("query", help="Lookup relations for a drug in kg_triples.csv")
    q.add_argument("drug", help="Drug name (case‑insensitive)")
    q.add_argument("--limit", "-n", type=int, default=20, help="max rows to show (default: 20)")

    return p

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> None:
    args = build_arg_parser().parse_args(argv)

    match args.command:
        case "parse-xml":
            parse_xml()
        case "ner":
            ner()
        case "triples":
            triples()
        case "all":
            pipeline_all()
        case "query":
            query(args.drug, max_rows=args.limit)
        case None:  # No sub‑command provided → interactive mode
            interactive_repl()
        case other:
            sys.exit(f"Unknown command: {other}")


if __name__ == "__main__":
    main()
