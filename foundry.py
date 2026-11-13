"""Real Microsoft Foundry Prompt Agent / Agents v2 Responses API adapter."""
from __future__ import annotations

import os
from functools import lru_cache

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential


@lru_cache(maxsize=1)
def get_openai_client():
    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "").strip()
    name = os.getenv("FOUNDRY_AGENT_NAME", "").strip()
    if not endpoint or not name:
        raise RuntimeError("Set FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_AGENT_NAME in .env")
    project = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    # Bind the Responses API client to the deployed Prompt Agent, NOT merely a model.
    return project.get_openai_client(agent_name=name)


def respond(prompt: str, *, previous_response_id: str | None = None) -> dict:
    """Call a *real* Foundry agent; persist ID and visible output after success.

    store=True is required so that previous_response_id can resolve on later turns.
    Deliberately do not supply conversation= while using previous_response_id.
    """
    kwargs = {"input": prompt, "store": True}
    if previous_response_id:
        kwargs["previous_response_id"] = previous_response_id
    answer = get_openai_client().responses.create(**kwargs)
    status = getattr(answer, "status", None)
    if status and status != "completed":
        raise RuntimeError(f"Foundry response {answer.id} has status {status!r}; no checkpoint saved")
    output = getattr(answer, "output_text", "") or ""
    if not output.strip():
        raise RuntimeError(f"Foundry response {answer.id} had no visible text; no checkpoint saved")
    return {"id": answer.id, "parent_id": previous_response_id,
            "prompt": prompt, "text": output, "status": status or "completed"}
