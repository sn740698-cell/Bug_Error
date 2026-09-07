"""
CLI Execution Harness for Multi-Agent RAG + LangGraph Backend pipeline.
Supports deterministic mock execution mode out of the box without requiring external API keys.
"""

import os
import sys
import json
import django

# Setup Django Environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.services.execution import PipelineExecutionService


def run_pipeline_test():
    print("=" * 80)
    print("STARTING MULTI-AGENT RAG LANGGRAPH PIPELINE TEST HARNESS")
    print("=" * 80)

    service = PipelineExecutionService()

    sample_name = "Alex Mercer"
    sample_email = "alex.mercer@innovate.org"
    sample_section = "Distributed Systems & Cloud Architecture"
    sample_query = (
        "Design a geo-distributed low-latency consensus protocol "
        "for banking ledger transactions with zero data loss."
    )

    sample_files = [
        (
            "banking_ledger_spec.txt",
            (
                "BANKING LEDGER SYSTEM SPECIFICATION:\n"
                "1. Multi-region consensus required with sub-50ms commit latency.\n"
                "2. Zero RPO (Recovery Point Objective) with synchronous quorum replication.\n"
                "3. Byzantine fault tolerance for untrusted edge nodes.\n"
                "4. Strict ACID transactional semantics for ledger balances."
            ).encode('utf-8')
        )
    ]

    print(f"\n[Test Payload]")
    print(f"User: {sample_name} <{sample_email}>")
    print(f"Section: {sample_section}")
    print(f"Query: {sample_query}")
    print(f"Uploaded Files: {[f[0] for f in sample_files]}")

    print("\n[Executing 8-Agent LangGraph Workflow...]")
    result = service.run_pipeline(
        name=sample_name,
        email=sample_email,
        query=sample_query,
        section=sample_section,
        files=sample_files
    )

    print("\n[Pipeline Execution Result]")
    print(json.dumps(result, indent=2))

    if result.get("status") == "success" and result.get("evaluation_passed"):
        print("\n" + "=" * 80)
        print("PIPELINE SMOKE TEST PASSED SUCCESSFULLY!")
        print("=" * 80)
        return True
    else:
        print("\n" + "=" * 80)
        print("PIPELINE SMOKE TEST FAILED!")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = run_pipeline_test()
    sys.exit(0 if success else 1)
