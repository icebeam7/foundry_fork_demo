"""Run: streamlit run app.py. Real Foundry calls; no mock outputs."""
from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from foundry import respond  # noqa: E402
from prompts import (SHARED_PROMPT, BULL_PROMPT, BEAR_PROMPT,
                     CONTINUE_BULL_PROMPT, CONTINUE_BEAR_PROMPT,
                     RESUME_BULL_PROMPT, RESUME_BEAR_PROMPT, COMPARE_PROMPT)
from storage import Store
from workflow import step, fork_one

st.set_page_config(page_title="Foundry Fork Lab", page_icon="🌿", layout="wide")

STORE = Store(os.getenv("DEMO_DB_PATH", "./data/demo_state.sqlite3"))


def active_run():
    run_id = st.session_state.get("run_id")
    return STORE.load(run_id) if run_id else None


def execute(func, *args, **kwargs):
    try:
        with st.spinner("Calling the real Microsoft Foundry agent…"):
            run = active_run()
            updated = func(run, *args, respond, **kwargs)
            STORE.save(updated)
        st.success("Foundry returned a completed response. Checkpoint saved locally.")
        st.rerun()
    except Exception as exc:
        st.error(f"Live operation failed: {type(exc).__name__}: {exc}")
        st.info("Any earlier successful checkpoint remains saved. Fix the error and retry.")


def response_card(title: str, response: dict | None):
    st.markdown(f"#### {title}")
    if response is None:
        st.caption("Not executed yet.")
        return
    st.code(f"Response ID: {response['id']}\nParent ID: {response.get('parent_id') or '(none — independent response)'}", language="text")
    st.markdown(response["text"])
    with st.expander("Exact prompt sent to Foundry"):
        st.code(response["prompt"], language="text")


st.title("🌿 Branch · Explore · Resume")
st.caption("LIVE Microsoft Foundry Agents v2 Responses API · Synthetic financial analysis · No market data feeds")

with st.sidebar:
    st.header("Checkpoint manager")
    configured = bool(os.getenv("FOUNDRY_PROJECT_ENDPOINT") and os.getenv("FOUNDRY_AGENT_NAME"))
    st.write("Foundry configuration:", "✅ ready" if configured else "⚠️ missing .env settings")
    st.caption(f"Agent: `{os.getenv('FOUNDRY_AGENT_NAME', '(not set)')}`")
    st.caption(f"Local DB: `{STORE.path}`")
    if st.button("＋ Create new run", use_container_width=True):
        run = STORE.new()
        st.session_state.run_id = run["id"]
        st.rerun()
    items = STORE.list_runs()
    if items:
        ids = [x[0] for x in items]
        if st.session_state.get("run_id") not in ids:
            st.session_state.run_id = ids[0]
        selected = st.selectbox(
            "Load persisted run", ids,
            index=ids.index(st.session_state.run_id),
            format_func=lambda key: next(f"{label} · {stamp[:16]} · {key[:8]}" for rid,label,stamp in items if rid == key),
        )
        st.session_state.run_id = selected
        st.caption("Close the browser or restart Streamlit. Select the same run to resume.")
    else:
        st.info("Create a run to start the four stages.")

run = active_run()
if run is None:
    st.info("Select 'Create new run' in the sidebar to begin.")
    st.stop()

with st.expander("Live execution configuration and data handling"):
    st.write("**Endpoint:**", os.getenv("FOUNDRY_PROJECT_ENDPOINT", "(not configured)"))
    st.write("**Agent:**", os.getenv("FOUNDRY_AGENT_NAME", "(not configured)"))
    st.write("**Run ID:**", run["id"])
    st.write("**Persistence:** SQLite only for prompts, response IDs, and returned text; Foundry stores server-side response context (`store=True`).")
    st.warning("This is a single-user local teaching app; do not publish it publicly without authentication and per-user authorization.")

steps = st.tabs(["1 · Shared baseline", "2 · Fork bull & bear", "3 · Continue one branch", "4 · Resume & compare", "🔎 Trace graph"])

with steps[0]:
    st.subheader("Create a shared financial-analysis response")
    st.write("One analysis of synthetic facts runs once and becomes the common parent of both branches.")
    st.text_area("Prompt sent to Foundry", SHARED_PROMPT, height=270, disabled=True, key="p_base")
    if st.button("▶ 1 — Create shared baseline", disabled=bool(run["base"]) or not configured, type="primary"):
        execute(step, "base")
    response_card("Shared parent response", run["base"])

with steps[1]:
    st.subheader("Fork two independent scenarios")
    st.write("Both requests use precisely the same `previous_response_id = base.id`. They are executed separately for clarity.")
    if run["base"]:
        st.code(f"SHARED PARENT: {run['base']['id']}", language="text")
    a,b = st.columns(2)
    with a:
        st.text_area("Bull branch prompt", BULL_PROMPT, height=215, disabled=True)
        if st.button("▶ 2A — Fork bullish", disabled=not run["base"] or bool(run["bull"]) or not configured):
            execute(fork_one, "bull")
        response_card("Bull branch (first response)", run["bull"][0] if run["bull"] else None)
    with b:
        st.text_area("Bear branch prompt", BEAR_PROMPT, height=215, disabled=True)
        if st.button("▶ 2B — Fork bearish", disabled=not run["base"] or bool(run["bear"]) or not configured):
            execute(fork_one, "bear")
        response_card("Bear branch (first response)", run["bear"][0] if run["bear"] else None)
    if run["bull"] and run["bear"]:
        st.success("Both forks originate from the same parent response, but have separate child response IDs.")

with steps[2]:
    st.subheader("Continue one branch without mixing histories")
    branch = st.radio("Select branch", ["bull", "bear"], horizontal=True, key="continue_branch")
    prompt = CONTINUE_BULL_PROMPT if branch == "bull" else CONTINUE_BEAR_PROMPT
    st.text_area("Prompt sent to Foundry", prompt, height=175, disabled=True)
    latest = run[branch][-1] if run[branch] else None
    if latest:
        st.info(f"Next request parent = latest {branch.upper()} response ID: {latest['id']}")
    if st.button("▶ 3 — Continue selected branch", disabled=not latest or not configured, type="primary"):
        execute(step, "continue", branch=branch)
    st.write(f"Saved {branch} responses: **{len(run[branch])}**")
    response_card(f"Latest {branch} response", latest)

with steps[3]:
    st.subheader("Reload from SQLite, resume later, compare both results")
    st.write("A browser refresh or app restart does not reset saved IDs. The next request reuses the selected branch's saved last response ID.")
    st.code(f"Saved run ID: {run['id']}\nDB path: {STORE.path}", language="text")
    if st.button("↻ Reload persisted checkpoint"):
        st.rerun()
    selected = st.radio("Branch to resume", ["bull", "bear"], horizontal=True, key="resume_branch")
    resume_prompt = RESUME_BULL_PROMPT if selected == "bull" else RESUME_BEAR_PROMPT
    st.text_area("Resumption prompt", resume_prompt, height=165, disabled=True)
    if st.button("▶ 4A — Resume saved branch", disabled=not run[selected] or not configured):
        execute(step, "resume", branch=selected)
    st.divider()
    st.subheader("Compare saved results (new independent response)")
    st.caption("The comparison prompt embeds both latest outputs as text. It does NOT merge response histories or modify either branch.")
    if run["base"] and run["bull"] and run["bear"]:
        actual_prompt = COMPARE_PROMPT.format(base=run["base"]["text"], bull=run["bull"][-1]["text"], bear=run["bear"][-1]["text"])
        st.text_area("Exact comparison prompt", actual_prompt, height=190, disabled=True)
    else:
        st.text_area("Comparison prompt template", COMPARE_PROMPT, height=140, disabled=True)
    if st.button("▶ 4B — Compare latest bull/bear results", disabled=not run["bull"] or not run["bear"] or not configured, type="primary"):
        execute(step, "compare")
    response_card("Neutral comparison output", run["comparison"])
    st.download_button("⬇ Export saved checkpoint JSON", data=json.dumps(run, indent=2, ensure_ascii=False),
                       file_name=f"fork_checkpoint_{run['id'][:8]}.json", mime="application/json")

with steps[4]:
    st.subheader("Response lineage — visible parent IDs")
    if run["base"]:
        st.code(f"BASE  {run['base']['id']}", language="text")
        for branch in ("bull", "bear"):
            if run[branch]:
                st.markdown(f"**{branch.upper()} chain**")
                for idx, res in enumerate(run[branch], 1):
                    st.code(f"{branch.upper()} #{idx}   {res['id']}\n    └─ previous_response_id: {res['parent_id']}", language="text")
        if run["comparison"]:
            st.code(f"COMPARE  {run['comparison']['id']}  (independent request; no parent)", language="text")
    else:
        st.info("Create the baseline to see the graph.")
    st.subheader("Execution audit")
    st.dataframe(run["events"], use_container_width=True, hide_index=True)
    st.caption("Each successful operation is committed to SQLite immediately, including partial fork progress.")

st.divider()
st.caption("Training use only · Invented company and financial figures · Results are not investment advice")
