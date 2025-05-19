import os
import sys
from dotenv import load_dotenv

from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_community.llms import Ollama

def main():
    load_dotenv()  # load vars from project-root/.env

    # 1) Connect to Neo4j
    uri      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user     = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    graph = Neo4jGraph(url=uri, username=user, password=password)

    # 2) Initialize Ollama LLM
    llm = Ollama(
        model       = os.getenv("OLLAMA_MODEL", "mistral:latest"),
        base_url    = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature = float(os.getenv("OLLAMA_TEMPERATURE", 0)),
    )

    # 3) System‐level prompt to forbid SQL
    system_message = """\
You are an expert in Neo4j Cypher.
Respond ONLY with valid Neo4j Cypher queries.
NEVER use any SQL syntax (no SELECT, FROM, subqueries, etc.).\
"""

   # 4) Human‐level template
    human_message = """\
User Question: What is Sprycel used for?\
Generate JUST the Cypher query to answer the above, using MATCH, WHERE,
RETURN, and (if needed) DISTINCT—but do NOT use any SQL patterns.\
"""

    # 5) Build the QA chain
    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        allow_dangerous_requests=True,
        system_message=system_message,
        human_message=human_message,
    )

    # 6) Obtain the question (CLI args or default)
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "What is Sprycel used for?"

    # 7) Run the chain and print
    print("\n[LLM] Generating Cypher and fetching answer…\n")
    answer = chain.run(question)
    print("\n[Answer]\n", answer)

if __name__ == "__main__":
    main()