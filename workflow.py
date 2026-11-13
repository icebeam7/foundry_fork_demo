"""Fork graph invariants and checkpoints, independent of the web UI."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from prompts import (BULL_PROMPT, BEAR_PROMPT, SHARED_PROMPT,
                     CONTINUE_BULL_PROMPT, CONTINUE_BEAR_PROMPT,
                     RESUME_BULL_PROMPT, RESUME_BEAR_PROMPT, COMPARE_PROMPT)


def step(run: dict, action: str, call: Callable, branch: str | None = None) -> dict:
    """Returns a changed run only after the live API call succeeds."""
    if action == "base":
        if run["base"]:
            raise ValueError("Base already exists. Create a new run to start over.")
        result = call(SHARED_PROMPT)
        run["base"] = result
    elif action == "fork":
        if not run["base"]:
            raise ValueError("Run the shared baseline first.")
        if run["bull"] or run["bear"]:
            raise ValueError("This run already has branches; do not overwrite them.")
        parent = run["base"]["id"]
        # Saving each branch independently also supports partial recovery if one call fails.
        raise ValueError("Use fork_one() for independent durable branch execution.")
    elif action in ("continue", "resume"):
        if branch not in ("bull", "bear") or not run[branch]:
            raise ValueError("Choose an existing bull or bear branch.")
        prompt = (CONTINUE_BULL_PROMPT if branch == "bull" else CONTINUE_BEAR_PROMPT)
        if action == "resume":
            prompt = RESUME_BULL_PROMPT if branch == "bull" else RESUME_BEAR_PROMPT
        parent = run[branch][-1]["id"]
        result = call(prompt, previous_response_id=parent)
        run[branch].append(result)
    elif action == "compare":
        if not run["bull"] or not run["bear"]:
            raise ValueError("Both branches must exist before comparison.")
        prompt = COMPARE_PROMPT.format(
            base=run["base"]["text"],
            bull=run["bull"][-1]["text"],
            bear=run["bear"][-1]["text"])
        # Comparison is an *independent* response from explicit texts, not a merge
        # and not a continuation of either branch.
        result = call(prompt)
        run["comparison"] = result
    else:
        raise ValueError(f"Unknown action: {action}")
    log_event(run, action, branch, result["id"])
    return run


def fork_one(run: dict, branch: str, call: Callable) -> dict:
    if not run["base"]:
        raise ValueError("Shared baseline must be created first.")
    if branch not in ("bull", "bear"):
        raise ValueError("Choose bull or bear")
    if run[branch]:
        raise ValueError(f"{branch} branch already exists")
    parent_id = run["base"]["id"]  # SAME parent for both forks
    prompt = BULL_PROMPT if branch == "bull" else BEAR_PROMPT
    result = call(prompt, previous_response_id=parent_id)
    run[branch].append(result)
    log_event(run, f"fork_{branch}", branch, result["id"])
    return run


def log_event(run: dict, action: str, branch: str | None, response_id: str):
    run["events"].append({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                          "action": action, "branch": branch, "response_id": response_id})
