## Genie Space Databricks App – Vibe‑Code Template

This repo is a **Genie Space–backed Databricks App template** that you can **“vibe code” from Cursor**: customize the UI copy, wiring, and behavior conversationally while the app talks to Databricks Genie.

It is designed as a starter that:
- **Wraps a Genie Space** as the core reasoning/querying engine.
- **Exposes a modern Dash UI** that you can quickly retheme and tweak.
- **Keeps config in env vars** so you can move between dev/stage/prod without code changes.
- **Plays nicely with Cursor + GitHub MCP** for “AI-native” development and documentation.

---

## Project Structure

- **Root**
  - **`README.md`**: This file – high‑level docs, setup, and usage.
  - **`dbx_apps_instructions.md`**: Shared **Databricks Apps best practices** – config, security, UC usage, and deployment guidance for all apps in this workspace.
  - **`genie_serving_app/`**: The actual Genie Space app implementation (Dash UI + Genie client + config).

- **`genie_serving_app/`**
  - **`app.py`**: Dash **entrypoint** and main UI; wires user input to `genie_room.genie_query`, renders chat, tables, and “Generate Insights”.
  - **`genie_room.py`**: **Genie Space client + orchestration**:
    - Handles OAuth via `TokenMinter`.
    - Calls the Genie Space REST APIs (start conversation, send messages, fetch query results).
    - Normalizes responses into either **Markdown text** or **Pandas DataFrames** for the UI.
  - **`config.py`**: Pydantic‑based **`AppConfig`** with branding, welcome text, suggestions, and UX copy loaded from env vars (with safe defaults).
  - **`token_minter.py`**: Pydantic‑based **`TokenMinter`** that uses Databricks **OAuth client credentials** to continuously mint and refresh workspace API tokens.
  - **`app.yaml`**: Minimal **Databricks App runtime manifest**:
    - Specifies the command (`python app.py`) and core env var (`SPACE_ID`).
    - Used by Databricks Apps to run this project as an app.
  - **`requirements.txt`**: Python **runtime dependencies** for the app (Dash, backoff, etc.).
  - **`assets/`**: Static files consumed by Dash:
    - **`style.css`**: App‑wide styling, layout, and theme.
    - **Icons/Images** (e.g., `genie_logo.png`, `menu_icon.svg`, `send_icon.svg`): Used for the chat UI, sidebar, and buttons.
    - **`table*.png` / troubleshooting images**: Example screenshots and UI assets.

---

## Setup & Usage (Cursor + Databricks + MCP)

### 1. Clone repo and create env file

- **Clone the repository** to your local machine.
- **Create an env file** in the project root (or wherever you prefer Cursor to load it from), based on a template:
  - If you already have a `.env.example` elsewhere, **copy it here** and adapt it.
  - Otherwise create `.env` manually with the required keys (see “Requirements & Env Vars” below).

Cursor (and `python-dotenv` in `app.py` / `genie_room.py` / `token_minter.py`) will load these variables when you run or debug the app.

### 2. Configure the GitHub MCP server in Cursor

This project is intended to be **AI‑operated via Cursor** using a **GitHub MCP server** (see the official install guide [Install GitHub MCP Server in Cursor](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-cursor.md)):

- In **Cursor → Settings → MCP**:
  - **Enable the GitHub MCP server** (if not already).
  - Make sure it has **access to this repo** so the agent can:
    - Read/write files.
    - Open/modify PRs.
    - Keep docs (including this `README.md`) in sync with changes.

This lets you “vibe code” the app by asking the agent to:
- Update UI copy.
- Add new callbacks or widgets.
- Adjust Genie wiring and backend logic.

### 3. Add Databricks CLI docs to indexing and Cursor docs

To get **high‑quality inline help** while you tweak the app:

- In **Cursor → Settings → Indexing / Docs** (names may vary slightly by version):
  - **Add the Databricks CLI / Databricks documentation** as a documentation source**, for example the Databricks CLI reference [Databricks CLI commands](https://docs.databricks.com/aws/en/dev-tools/cli/commands):
    - Databricks CLI & SDK docs (including the CLI command reference above).
    - Databricks Apps and Genie Space docs.
  - Ensure Cursor is allowed to **use those docs** while working in this project.

This helps the agent answer questions like:
- How to configure OAuth clients.
- How Genie Spaces endpoints and payloads look.
- How to deploy Databricks Apps and set env vars.

### 4. Run locally

- Create/activate a Python env (3.10+ recommended) and install requirements:

```bash
cd "Test Vibe Code App"
python -m venv .venv
source .venv/bin/activate
pip install -r genie_serving_app/requirements.txt
pip install databricks-sdk python-dotenv pandas requests pydantic
```

- Export or ensure `.env` contains required vars (see below).
- Run:

```bash
cd genie_serving_app
python app.py
```

Dash will start a local server (default `http://127.0.0.1:8050`); open it in a browser to use the chat UI.

### 5. Deploy as a Databricks App

- Ensure `app.yaml` has the correct **`SPACE_ID`** (or override via workspace env vars).
- Follow your workspace’s **Databricks Apps deployment flow**:
  - Create an App pointing at this repo.
  - Configure **env vars and secrets** in the App settings (see next section).
  - Start the App and validate via a browser.

For more environment‑wide standards (UC, secrets, logging, etc.), refer to `dbx_apps_instructions.md`.

---

## Requirements & Environment Variables

### Python & libraries

- **Python**: 3.10+ recommended.
- **Core dependencies** (from `genie_serving_app/requirements.txt` + runtime):
  - **Dash & ecosystem**: `dash`, `dash-bootstrap-components`, `dash-core-components`, `dash-html-components`, `dash-table`, `dash_ag_grid`, `dash_mantine_components`, `dash-leaflet`, `dash-iconify`
  - **Infra/logic**: `backoff`, `python-dotenv`, `pydantic`, `pandas`, `requests`, `databricks-sdk`

### Required env vars (minimal set)

These are either:
- Loaded from `.env` by `python-dotenv`, or
- Set as environment variables in Databricks Apps / Jobs.

- **Genie / Databricks workspace**
  - **`DATABRICKS_HOST`**: Workspace host **without scheme**, e.g. `my-workspace.cloud.databricks.com`.
  - **`SPACE_ID`**: Genie **Space ID** that this app talks to (also referenced in `app.yaml`).

- **OAuth client (for Genie + APIs)**
  - **`DATABRICKS_CLIENT_ID`**: OAuth client ID with access to Genie / workspace APIs.
  - **`DATABRICKS_CLIENT_SECRET`**: OAuth client secret.

- **UI / branding overrides** (all optional; fall back to defaults in `AppConfig`):
  - **`APP_BRAND_TITLE`**: Text in the top navbar (e.g. “Genie Data Copilot”).
  - **`SIDEBAR_HEADER_TEXT`**: Sidebar header above conversation list.
  - **`MODEL_DISPLAY_NAME`**: Label shown next to model avatar.
  - **`USER_DISPLAY_INITIAL`**: User avatar initial (default `"Y"`).
  - **`LOGOUT_LABEL`**: Logout button label.
  - **`WELCOME_TITLE`**, **`WELCOME_DESCRIPTION`**: Welcome hero text.
  - **`DEFAULT_SUGGESTIONS`**: JSON list or `q1||q2||q3||q4` string of welcome suggestion prompts.
  - **`INPUT_PLACEHOLDER`**, **`DISCLAIMER_TEXT`**: Input placeholder and disclaimer under the input area.

### Databricks side requirements

- A **Genie Space** configured with:
  - Appropriate **tools** and **data access** for your use case.
  - Permissions so the OAuth client can start conversations and execute queries.

---

## File‑by‑File Overview

- **`dbx_apps_instructions.md`**
  - Global **Databricks Apps guidelines**:
    - Config‑first, UC‑centric, secure‑by‑default.
    - How to use `DatabricksAppConfig` (if you introduce it here).
    - Recommended env vars, secrets usage, logging, and deployment patterns.

- **`genie_serving_app/app.py`**
  - Defines the **Dash app layout**: navbar, sidebar, welcome panel, chat history, fixed input, and modals.
  - Implements **callback graph**:
    - Handles suggestion buttons and free‑text input.
    - Calls `genie_query` and renders **Markdown** or **Dash tables**.
    - Manages sessions/chat list, thumbs‑up/down feedback, query‑running state, and welcome message customization.
  - Handles all Genie interactions for conversational analysis and table display.

- **`genie_serving_app/genie_room.py`**
  - Implements **`GenieClient`** with:
    - Token refresh via `TokenMinter` for each call.
    - REST methods: `start_conversation`, `send_message`, `get_message`, `get_query_result`, `execute_query`, `wait_for_message_completion`.
  - High‑level helpers:
    - `start_new_conversation`, `continue_conversation`, `genie_query`.
    - `process_genie_response` to return **either text or a `pandas.DataFrame` + SQL**.

- **`genie_serving_app/config.py`**
  - Pydantic **`AppConfig`** model:
    - Centralizes all UI copy and suggestion defaults.
    - `from_env()` pulls values from env vars and falls back to documented defaults.
  - Keeps the rest of the code clean by pulling branding text from a single place.

- **`genie_serving_app/token_minter.py`**
  - Pydantic **`TokenMinterConfig`** to load OAuth config (optionally with `.from_env()`).
  - **`TokenMinter`**:
    - Talks to `https://<DATABRICKS_HOST>/oidc/v1/token` with client credentials.
    - Stores an access token and refreshes it automatically ~5 minutes before expiry using a lock.

- **`genie_serving_app/app.yaml`**
  - Minimal **App definition** for Databricks Apps:
    - Runs `python app.py`.
    - Sets **`SPACE_ID`** (overridable in the App configuration UI).

- **`genie_serving_app/requirements.txt`**
  - Core library versions required to run the app.

- **`genie_serving_app/assets/`**
  - Standard Dash static folder:
    - `style.css` for styling.
    - Icons and images used in the UI.

---

## “Vibe Coding” Ideas / Other Topics

- **Retheme the app**:
  - Use Cursor to modify `assets/style.css` and `AppConfig` branding fields.
  - Swap text/content (welcome prompts, disclaimers, sidebar labels) via env vars or directly in `config.py`, then ask the agent to propagate changes.

- **Extend Genie behavior**:
  - Add new buttons that call `genie_query` with pre‑baked prompts.
  - Extend `process_genie_response` for richer table metadata or chart‑ready outputs.

- **Telemetry & logging**:
  - Hook in structured logging (JSON) in `genie_room.py` and `app.py`.
  - Use MLflow or UC tables to track conversations/responses if you want audit or analytics.

- **Deployment hardening**:
  - Follow `dbx_apps_instructions.md` for:
    - Environment parity (dev/stage/prod).
    - Secrets scopes and principled access control.
    - Health checks and smoke tests before exposing to end users.

Use this README as the **single source of truth** for how the Genie Space app is wired and how to safely extend it. As you customize behavior, keep this file updated so future “vibe coding” sessions remain grounded. 


