"""
Very small RAG pipeline
──────────────────────
• Retrieves top-k passages with retriever.py
• Feeds them to an Ollama mistral model using LangChain's QA chain
"""

import argparse
from pathlib import Path
from typing import List

from langchain_community.llms import Ollama            # 🟡 requires langchain-community ≥0.3
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain.schema import Document

# Local import (retriever.py must be in same folder)
from retriever import retrieve

# ───────── prompt template ─────────
_PROMPT = """
You are an expert pharmacologist. Use only the CONTEXT below to answer the QUESTION.
Cite the drug name(s) you rely on.

CONTEXT:
{context}

QUESTION:
{question}

Answer:""".strip()


def make_prompt(docs: List[Document], question: str) -> str:
    context = "\n\n".join(f"{i+1}. {d.page_content}" for i, d in enumerate(docs))
    return _PROMPT.format(context=context, question=question)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query",   required=True, help="Question to ask")
    parser.add_argument("--topk",    type=int, default=5, help="Passages to retrieve")
    parser.add_argument("--model",   default="mistral",   help="Ollama model name")
    parser.add_argument("--url",     default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--temp",    type=float, default=0.2, help="LLM temperature")
    args = parser.parse_args()

    print("🤖 Loading model and retriever …")
    docs = retrieve(args.query, args.topk)
    if not docs:
        print("⚠️  No contexts found for your query.")
        return

    model = Ollama(model=args.model, base_url=args.url, temperature=args.temp)

    prompt = PromptTemplate.from_template(_PROMPT)
    chain  = load_qa_chain(llm=model, chain_type="stuff", prompt=prompt)

    # LangChain expects Document objects, we already have them.
    response = chain.run(input_documents=docs, question=args.query)
    print("\n📝  Final answer:\n", response.strip())


if __name__ == "__main__":
    main()
