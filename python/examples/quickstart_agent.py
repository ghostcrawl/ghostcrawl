"""Quickstart: agent task with an explicit 3-step plan.

The task payload supports an ordered ``steps`` list of ``observe`` / ``act`` /
``extract`` instructions. A full task dict is passed via ``task=``.

Run with:

    GHOSTCRAWL_API_KEY=gck_live_YOUR_KEY python examples/quickstart_agent.py
"""

from __future__ import annotations

import json
import os

from ghostcrawl import GhostCrawl


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


def main() -> None:
    token = os.environ.get("GHOSTCRAWL_API_KEY", "gck_live_YOUR_KEY")

    gc = GhostCrawl(token=token)
    # `task=` takes a full task dict; `engine=` is forwarded to the request body.
    response = gc.agent(task=TASK, engine="webkit")

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
    main()
