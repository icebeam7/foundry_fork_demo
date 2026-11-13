# Branch, Explore, Resume — Microsoft Foundry Agents v2 demo

A **real** Python + Streamlit live presentation app. The UI walks through four stages:

1. Generate a shared baseline analysis in an existing Microsoft Foundry **Prompt Agent**.
2. Fork bullish and bearish responses from the **same** `previous_response_id`.
3. Continue either branch from its own latest response ID (no history mixing).
4. Restart/reopen the app, reload SQLite checkpoints, resume a branch, and generate a neutral comparison.

## Architecture

```text
Streamlit browser -> app.py -> workflow.py -> foundry.py
                         |                   |
                         v                   v
                    SQLite local      AIProjectClient
                    data/*.sqlite3        |
                                           v
                                  Existing Foundry Prompt Agent
                                  Agents v2 Responses API

                           BASE response.id
                            /           \
      previous_response_id=BASE           previous_response_id=BASE
                    BULL #1              BEAR #1
                       |                     |
             previous=BULL #1        previous=BEAR #1
                    BULL #2              BEAR #2
                       |                     |
                     ...                   ...
                       \                     /
                      texts explicitly supplied
                       to a new comparison response
```

**Important:** Resuming conversation history with `previous_response_id` is different from resuming a **hosted agent sandbox session** (`agent_session_id`). This app demonstrates response-chain continuity for a prompt agent, not a hosted container filesystem.

## Azure resources — create manually (no Bicep deployment necessary)

For this minimal demo, you only need:

- A Microsoft Foundry resource with a **project** and its **project endpoint**.
- A model deployment supported by Foundry Agent Service / Responses API (for example a compatible GPT deployment available in your region).
- A **Prompt Agent** in the project, saved/published with name `investment-analyst` (or another name).
- Your user identity must have permission to invoke the project and agent. Commonly use **Azure AI User** or the suitable project-scoped role described in the Foundry access guidance.

Suggested **agent instructions** (paste when creating the Prompt Agent):

```text
You are a careful analyst for fictional financial scenarios.
Use only figures provided in the user's prompts or inherited conversation context.
Show arithmetic, separate facts from assumptions, and explicitly identify uncertainty.
Do not claim access to stock prices, tools, financial feeds, or outside sources.
Keep answers concise and structured. This is a teaching simulation,
not financial advice.
```

Steps in the Foundry portal:

1. Open https://ai.azure.com and select/create a Foundry project.
2. Deploy an available model that supports Agents v2 Responses API.
3. Create a **Prompt Agent**, set its name to `investment-analyst`, choose the deployment and enter the instructions above. Save/publish the agent (if the portal prompts for a version).
4. From your project Overview, copy the **project endpoint**, typically `https://<resource>.services.ai.azure.com/api/projects/<project>` (not the model-specific chat/completions URL).
5. Ensure your Azure login can access this project and invoke the agent. RBAC propagation might take several minutes.

## Local setup

Requirements: Python **3.10+** (3.11 or 3.12 recommended), Azure CLI, network access to Foundry.

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows PowerShell equivalent:
# py -3 -m venv .venv
# .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Windows PowerShell: Copy-Item .env.example .env

az login

streamlit run app.py
```

The browser normally opens at `http://localhost:8501`.

Fill in `.env` before running:

| Variable | Required | Example / purpose |
|---|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | Yes | `https://my-foundry.services.ai.azure.com/api/projects/my-project` |
| `FOUNDRY_AGENT_NAME` | Yes | `investment-analyst` — **existing** prompt agent name |
| `DEMO_DB_PATH` | No | `./data/demo_state.sqlite3` |

**Authentication:** Uses `DefaultAzureCredential` and your `az login` token. No API keys, Azure client secrets, or model API keys are required. For shared/server deployments replace interactive identity with managed identity and configure access controls.

## Live session runbook

**Step 1 — Shared baseline**

- Click `＋ Create new run` in the sidebar.
- Go to tab 1. The actual prompt and synthetic FY2024/FY2025 figures are displayed.
- Click `1 — Create shared baseline`; point out the returned `response.id` and the calculations.

**Step 2 — Fork two scenarios**

- Open tab 2. Point out **both** prompts reference the **same parent ID**.
- Click `2A — Fork bullish`, then `2B — Fork bearish`.
- Read the separate output texts and distinct child IDs. One failed call can be retried without repeating the successful fork.

**Step 3 — Continue a branch**

- Open tab 3. Select `bull`, then click `3 — Continue selected branch`.
- Inspect how `previous_response_id` equals the bull response ID, **not** the bear response ID.
- Optionally continue the bear branch in the same tab and compare each chain.

**Step 4 — Persistence, resume, comparison**

- Close the browser; optionally stop Streamlit with Ctrl+C. Start it again with `streamlit run app.py`.
- In the sidebar, select the persisted run by ID/label (SQLite is on disk).
- On tab 4, choose a branch and click `4A — Resume saved branch`. It generates a **new live API call** using the saved latest ID.
- Click `4B — Compare latest bull/bear results`. This creates an **independent** neutral response using both saved outputs in the prompt. The two branches are **not merged** server-side.
- Download the checkpoint JSON, then open the `Trace graph` tab to show lineage and the event audit.

## Code walkthrough

Core API call, implemented in [`foundry.py`](foundry.py):

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project = AIProjectClient(
    endpoint=FOUNDRY_PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)
openai = project.get_openai_client(agent_name=FOUNDRY_AGENT_NAME)

base = openai.responses.create(input=SHARED_PROMPT, store=True)
bull = openai.responses.create(
    input=BULL_PROMPT, previous_response_id=base.id, store=True
)
bear = openai.responses.create(
    input=BEAR_PROMPT, previous_response_id=base.id, store=True
)
bull_next = openai.responses.create(
    input=CONTINUE_BULL_PROMPT, previous_response_id=bull.id, store=True
)
```

`store=True` is critical: previous responses must remain available in Foundry. The SQLite store persists **IDs, prompts, visible results and an event log**, not a full replayable server-side response snapshot. If someone deletes a response server-side, moves to an incompatible endpoint, or reaches a service retention limit, an old chain might no longer resume. Exported JSON is an audit artifact; it is not an automatic Foundry restoration procedure.

## Operational details / limitations

- **Synthetic data:** All figures are invented. No stock trades or external market feeds.
- **Single-user local app:** The UI and SQLite database do not enforce user tenancy. Never expose this app to the internet or use with confidential data without adding authentication, user-specific authorization, encryption and retention management.
- **Response IDs are sensitive:** Keep the `.env`, SQLite database, and downloaded JSON private. Do not allow untrusted visitors to select arbitrary previous response IDs.
- **Model costs:** Every click that invokes Foundry consumes billable model inference. Creating a new run is local and free.
- **Two branches don't merge automatically:** The comparison request passes both results as prompt text and creates a fresh response.
- **Partial operations:** Each successful fork persists immediately; if Bear fails after Bull succeeds, just rerun Bear.
- **Checkpoint semantics:** The app checkpoints completed responses only; it does not provide cancellation, task queueing, multi-user locking, or hosted sandbox state restoration.
- **Refreshing page:** This reads the same on-disk checkpoint. Normal app use is sequential; avoid two browsers writing to the same run concurrently.
- **Changing prompts:** Edit `prompts.py`. Already-saved checkpoints retain the original prompts for audit.
- **SDK changes:** Use the project endpoint and agent binding documented in current Microsoft Learn. Validate SDK compatibility when installing in a future environment.

## Troubleshooting

| Symptom | Check |
|---|---|
| `Set FOUNDRY_PROJECT_ENDPOINT ...` | Fill in `.env` at project root; restart Streamlit. |
| `CredentialUnavailableError` | Run `az login`; verify `az account show` and selected tenant/subscription. |
| `403 Forbidden` | Check Foundry project RBAC and agent access permissions. |
| `404 Not Found` | Use the **project** endpoint; verify prompt agent name/version and model deployment. |
| `previous_response_id` invalid or not found | Ensure stored responses remain accessible in the same project/agent, and rerun in a fresh checkpoint if necessary. |
| `429` | Deployment quota/rate limit; retry later or adjust quota. |
| HTTP timeout | Check network and model health; reload checkpoint to see last confirmed saved step. |

## References

- Microsoft Learn — fork pattern, `previous_response_id`, conversation duplication, and resumption: https://learn.microsoft.com/en-us/training/modules/aaai-design-agentic-loops-azure-ai-agent-service/6-implement-fork-based-sessions?pivots=text
- Microsoft Learn — Prompt Agent quickstart: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent?tabs=python
- Microsoft Learn — runtime components and response persistence: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/runtime-components
- Microsoft Learn — hosted sandbox session continuity vs response history: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/manage-hosted-sessions?pivots=python
