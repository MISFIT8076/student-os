"""Run the full 'What should I do today?' pipeline from the command line.

    cd backend && python demo.py

Launches every MCP server, gathers items, ranks them, and prints the briefing.
Handy for demos and for debugging without the web server or frontend.
"""
from __future__ import annotations

import asyncio

from app.orchestrator.agent import build_briefing


async def _main() -> None:
    b = await build_briefing()
    print("\n" + "=" * 66)
    print(f"  STUDENT OS — {b.headline}")
    print("=" * 66)
    print(b.summary)
    print(f"\nSources: {', '.join(b.sources_used)}   |   LLM: {b.llm_used}")
    print("-" * 66)
    for i, item in enumerate(b.items, 1):
        due = f"  (due {item.due})" if item.due else ""
        print(f"{i:>2}. [{item.priority.value:^6}] {item.title}{due}")
        print(f"      {item.source}/{item.kind} · {item.detail}")
    print("-" * 66 + "\n")


if __name__ == "__main__":
    asyncio.run(_main())
