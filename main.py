from __future__ import annotations

import asyncio
import os

from app.orchestrator import ResearchOrchestrator


async def main() -> None:
    query = input("Research question: ").strip()
    if not query:
        print("Please provide a non-empty question.")
        return

    orchestrator = ResearchOrchestrator()
    result = await orchestrator.run(query)

    print("\n=== Research plan ===")
    print(result["plan"].model_dump_json(indent=2))
    print(f"\n=== Summary saved to: {result['run_dir']} ===")
    print(result["summary"][:1200])
    print("\n=== Quality assessment ===")
    print(result["quality"])


if __name__ == "__main__":
    required = [
        "SEARXNG_BASE_URL",
        "SEARXNG_SECRET",
        "HUGGINGFACE_HUB_TOKEN",
    ]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        print("Missing required environment variables: " + ", ".join(missing))
        raise SystemExit(1)
    asyncio.run(main())
