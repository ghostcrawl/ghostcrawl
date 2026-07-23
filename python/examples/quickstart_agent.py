"""Quickstart: agent task with an explicit 3-step plan.

The task payload supports an ordered ``steps`` list of ``observe`` / ``act`` /
``extract`` instructions. A full task dict is passed via ``task=``.

Run with:

    GHOSTCRAWL_API_KEY=gck_live_... python examples/quickstart_agent.py
"""

from __future__ import annotations

import asyncio
import json
import os

from ghostcrawl import Client


TASK = {
    "goal": "Find the latest changelog entry on the GhostCrawl docs site",
    "steps": [
        {
            "type": "observe",
            "instruction": "locate the changelog navigation link",
        },
        {
            "type": "act",
            "instruction": "click the changelog link",
        },
        {
            "type": "extract",
            "schema": {
                "type": "object",
                "properties": {
                    "version": {"type": "string"},
                    "released_at": {"type": "string"},
                    "highlights": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["version"],
            },
        },
    ],
}


async def main() -> None:
    api_key = os.environ.get("GHOSTCRAWL_API_KEY", "gc_live_replace_me")
    base_url = os.environ.get("GHOSTCRAWL_BASE_URL", "https://api.ghostcrawl.io")

    async with Client(api_key=api_key, base_url=base_url) as gc:
        # `task=` takes a full task dict; `engine=` is forwarded to the request body.
        response = await gc.agent(task=TASK, engine="webkit")

        # The agent capability is gated — when it is not enabled for the
        # account the API replies with a `detail` envelope instead of a result.
        if "detail" in response:
            print(f"Agent endpoint unavailable: {response['detail']}")
            return

        payload = response.get("payload", {})
        print("steps executed:", payload.get("steps_executed"))
        print("extracted     :")
        print(json.dumps(payload.get("extracted", {}), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
