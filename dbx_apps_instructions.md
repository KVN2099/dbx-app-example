Databricks Apps – Ground Rules and Best Practices

Purpose
- Establish clear, reusable standards for building Databricks Apps that can power multiple use cases.
- Ensure Apps are secure, configurable, observable, and easy to deploy across environments.

Scope
- Applies to Apps that leverage Genie Space (for conversational UI/agent experiences) and Model Serving (for online inference).
- Complements project-wide guidance in `templates/instructions.md`.

Core Principles
1) Configuration-First
   - All environment-specific values must be externalized (env vars, secrets, or config files). No hard-coded workspace IDs, tokens, or catalog names.
   - Use the `dbx_apps_config.py` configuration class to load/validate settings.

2) Unity Catalog-Centric
   - Use Unity Catalog for data, features, models, and governance.
   - Reference assets with fully qualified names (`<catalog>.<schema>.<name>`).

3) Secure by Default
   - Store credentials in Databricks Secrets; never in source control.
   - Principle of least privilege (service principals, scoped tokens, table ACLs, model permissions).

4) Observability & Traceability
   - Track experiments and models with MLflow; include run and model URIs in logs.
   - Emit structured logs (JSON where possible) and include request IDs for serving calls.

5) Environment Parity & Idempotency
   - Keep `dev`, `staging`, and `prod` as similar as possible.
   - Provision resources via code/notebooks that are idempotent (safe to re-run).

6) Modular Resources
   - Treat Genie Space and Model Serving as pluggable modules with their own configs.
   - Avoid tight coupling between the UI/agent layer and serving endpoints.

App Architecture Guidance
- App Core: Business logic, adapters to Genie Space and Model Serving, and configuration loading.
- Resource Layer:
  - Genie Space for conversational orchestration, tools, and personas.
  - Model Serving endpoints for low-latency inference (LLMs or custom models).
- Data & Models: Managed in Unity Catalog; version via Delta/MLflow.

Configuration Conventions
- Use the `DatabricksAppConfig` from `dbx_apps_config.py`.
- Support three sources (in priority order):
  1. Environment variables (prefix recommended: `APP_`)
  2. JSON config file (checked into repo for structure, not secrets)
  3. Programmatic defaults (safe, non-sensitive)

Recommended Env Vars (prefix `APP_`)
- Workspace & UC: `WORKSPACE_URL`, `CATALOG`, `SCHEMA`, `VOLUME`
- Genie Space: `GENIE_SPACE_ID`, `GENIE_SPACE_NAME`, `GENIE_DEFAULT_PERSONA`, `GENIE_TOOLS` (CSV)
- Model Serving: `SERVING_ENDPOINT`, `SERVING_RATE_LIMIT_RPS`, `SERVING_CONCURRENCY`
- Secrets: `SECRETS_SCOPE` (and key names consumed within your code)

Security & Secrets
- Access tokens and API keys must come from Databricks Secrets or workspace-scoped env vars set in Jobs/Apps.
- Never log raw secrets. Redact before logging.

Genie Space Best Practices
- Keep tools minimal and explicit. Only enable what the space needs.
- Define a default persona aligned to the App’s purpose.
- Validate the space ID/name at startup; fail fast if misconfigured.

Model Serving Best Practices
- Prefer named endpoints with versioned models or routing rules.
- Set conservative defaults for rate limits and concurrency; make them configurable per environment.
- Include request/response timing and status codes in logs.

Deployment & Operations
- Package configuration with the App deployable. Avoid code changes for environment switches.
- Use Databricks Workflows (or your chosen orchestrator) for provisioning, smoke tests, and rollbacks.
- Add health checks for serving endpoints during startup.

Using the Configuration Class
- Import and load configuration early in your App entrypoint. Example:

```python
from templates.databricks_apps.dbx_apps_config import DatabricksAppConfig

config = DatabricksAppConfig.from_env(prefix="APP_")
config.validate()

# Example: access unified resource identifiers
uc_location = f"{config.catalog}.{config.schema}"
serving_endpoint = config.model_serving.endpoint_name
genie_space_id = config.genie_space.space_id
```

Minimal Env Var Set (per environment)
```
APP_WORKSPACE_URL=https://<your-workspace-url>
APP_CATALOG=<catalog>
APP_SCHEMA=<schema>
APP_GENIE_SPACE_ID=<space-id>
APP_SERVING_ENDPOINT=<endpoint-name>
```

Quality Gates
- Lint: Ensure no linter errors in new/modified files.
- Static config validation: `config.validate()` is required at startup.
- Runtime guards: Check external resource reachability (e.g., serving endpoint health) before enabling user access.

Documentation
- Keep this file updated as the App evolves.
- Document any new required/optional config fields and default behaviors.


