# Runbook: Connect Claude Code to Azure and Microsoft Graph (Part 3 of 3)

> **Scope:** Set up Claude Code so you can ask it, in plain language, to query and manage Azure resources and Microsoft Graph data, with guardrails on what it may run.
> **Previous:** [Part 1](runbook.md) (app registration) · [Part 2](runbook-part2.md) (Python test).

> [!NOTE]
> This runbook uses Claude Code as a **client** that operates Azure and Graph. Running Claude models *on* Azure (Microsoft Foundry as the model provider) is a separate topic: see [Claude Code on Microsoft Foundry](https://code.claude.com/docs/en/microsoft-foundry.md).

---

## Table of contents

1. [Architecture](#1-architecture)
2. [Prerequisites](#2-prerequisites)
3. [Install Claude Code](#3-install-claude-code)
4. [Grant Azure resource access](#4-grant-azure-resource-access)
5. [Create the project workspace](#5-create-the-project-workspace)
6. [Set guardrails](#6-set-guardrails)
7. [Add the Azure MCP Server](#7-add-the-azure-mcp-server)
8. [Optional: Microsoft Graph MCP Server (preview)](#8-optional-microsoft-graph-mcp-server-preview)
9. [Launch and verify](#9-launch-and-verify)
10. [Daily use](#10-daily-use)
11. [Rollback](#11-rollback)
12. [Troubleshooting](#12-troubleshooting)
13. [Sign-off](#13-sign-off)

---

## 1. Architecture

Claude Code reaches Azure and Graph through three channels. Channel A works as soon as Claude Code is installed; B and C add structured tools.

| Channel | What Claude Code uses | Reaches | Identity | Status |
|---|---|---|---|---|
| **A. Shell** | `az` CLI, `az rest`, `graph_test.py` via its Bash tool | Azure + Graph | Your `az login` session; the script uses the Part 1 app | Always available |
| **B. Azure MCP Server** | `@azure/mcp` (Microsoft) as a local MCP server | Azure resources | `graph-connector` service principal, falling back to `az login` | GA |
| **C. Microsoft MCP Server for Enterprise** | Microsoft-hosted MCP endpoint | Graph (read-only) | You, signed in (delegated only) | Preview |

```text
            ┌──────────────────────── your machine ────────────────────────┐
  you  ───► │ Claude Code ──Bash──► az CLI / graph_test.py ────────────────┼──► Azure ARM / Graph
            │      │                                                       │
            │      └──MCP (stdio)──► Azure MCP Server ───────────────────┼──► Azure ARM
            │      └──MCP (http)───────────────────────────────────────────┼──► mcp.svc.cloud.microsoft ──► Graph
            └───────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Graph permissions are not Azure resource permissions.** Part 1 gave `graph-connector` `User.Read.All` on Graph only. To list or change subscriptions, resource groups, VMs, storage and so on, the identity also needs an **Azure RBAC role** ([§4](#4-grant-azure-resource-access)).

---

## 2. Prerequisites

| Item | Requirement |
|---|---|
| Parts 1–2 | Completed; `graph_test.py` returns `[PASS]` |
| Claude account | Pro, Max, Team, Enterprise, or Console (the free plan doesn't include Claude Code) |
| OS | macOS 13+, Windows 10 1809+, Ubuntu 20.04+, Debian 10+ (WSL 2 recommended on Windows) |
| Node.js | LTS, for the Azure MCP Server via `npx`: `node --version` |
| Azure CLI | Signed in: `az account show` |
| Azure role (for §4) | **Owner** or **User Access Administrator** on the target scope |
| Optional (for §8) | PowerShell 7 and **Application Administrator** or **Cloud Application Administrator** in Entra |

- [ ] All prerequisites met

---

## 3. Install Claude Code

macOS, Linux, WSL:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://claude.ai/install.ps1 | iex
```

Alternatives: `brew install --cask claude-code` or `winget install Anthropic.ClaudeCode` (these don't auto-update).

Open a **new** terminal, then verify and sign in:

```bash
claude --version     # prints e.g. 2.1.xxx (Claude Code)
claude doctor        # install and settings diagnostics
claude               # first run opens the browser sign-in; type /exit afterwards
```

- [ ] `claude --version` prints a version
- [ ] Signed in

---

## 4. Grant Azure resource access

Give the `graph-connector` service principal **Reader** on one subscription (or a single resource group). Start read-only; widen later only if needed.

```bash
export APP_ID="<client-id from Part 1>"
export SUB_ID="$(az account show --query id -o tsv)"     # or set explicitly
SP_OBJECT_ID="$(az ad sp show --id "$APP_ID" --query id -o tsv)"

az role assignment create \
  --assignee-object-id "$SP_OBJECT_ID" \
  --assignee-principal-type ServicePrincipal \
  --role Reader \
  --scope "/subscriptions/$SUB_ID"
```

Narrower alternative (one resource group):

```bash
--scope "/subscriptions/$SUB_ID/resourceGroups/<rg-name>"
```

> [!TIP]
> Reading data inside a resource (blob contents, Key Vault secrets, Cosmos documents) needs a **data-plane** role such as *Storage Blob Data Reader*. Reader alone covers resource metadata only.

- [ ] `az role assignment list --assignee "$APP_ID" -o table` shows **Reader** at the expected scope

---

## 5. Create the project workspace

Claude Code works per folder. One folder holds the instructions, guardrails and MCP configuration for this project.

```bash
mkdir -p ~/azure-ops && cd ~/azure-ops
git init
cp ~/graph-test/graph_test.py .
cp ~/graph-test/requirements.txt .
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

### 5.1 `.gitignore`

```bash
cat > .gitignore <<'EOF'
.venv/
.env
*.pem
*.key
.claude/settings.local.json
EOF
```

### 5.2 `CLAUDE.md` — project instructions

Claude Code reads `CLAUDE.md` at the start of every session in this folder.

```bash
cat > CLAUDE.md <<'EOF'
# Azure ops workspace

## Environment
- Tenant: <tenant-id>   Subscription: <subscription-id>
- App registration: graph-connector (client ID <client-id>), app-only Graph access
- Service principal has Reader on the subscription (no write access through it)

## Tools available
- `azure` MCP server: preferred for Azure resource queries.
- `az` CLI: runs as the signed-in human user. Use `-o table` or `-o json --query` to keep output short.
- Graph (app-only): `.venv/bin/python graph_test.py` to verify; `az rest --method get --url https://graph.microsoft.com/v1.0/...` for ad-hoc delegated reads.

## Rules
- Read before you change. Show the exact command and wait for approval before any create/update/delete.
- Never print, echo, or write secrets, keys, or tokens.
- Prefer resource-group scope over subscription scope for any change.
- When a command fails, show the error and the `request-id`/correlation ID; don't retry destructive commands.
EOF
```

- [ ] `CLAUDE.md` filled in with your IDs

---

## 6. Set guardrails

Project settings in `.claude/settings.json` decide what Claude Code may run without asking, what always prompts, and what is blocked.

```bash
mkdir -p .claude
cat > .claude/settings.json <<'EOF'
{
  "permissions": {
    "allow": [
      "Bash(az account show *)",
      "Bash(az account list *)",
      "Bash(az group list *)",
      "Bash(az resource list *)",
      "Bash(az role assignment list *)",
      "Bash(.venv/bin/python graph_test.py *)"
    ],
    "ask": [
      "Bash(az * create *)",
      "Bash(az * update *)",
      "Bash(az * set *)",
      "Bash(az * start *)",
      "Bash(az * stop *)",
      "Bash(az * restart *)",
      "Bash(az role *)",
      "Bash(az rest *)"
    ],
    "deny": [
      "Bash(az * delete*)",
      "Bash(az * purge*)",
      "Bash(az keyvault secret show *)",
      "Bash(az ad app credential *)",
      "Bash(az ad sp credential *)",
      "Read(./.env)",
      "Read(./*.pem)",
      "Read(./*.key)"
    ]
  }
}
EOF
```

How rules combine: **deny** beats **ask**, which beats **allow**. Anything not listed prompts you by default.

> [!WARNING]
> Bash pattern rules are a convenience, not a security boundary: a command can be rephrased (`bash -c '…'`, full paths) to slip past a pattern. The real limit is the **identity's Azure role**. Keep the service principal at Reader and review every prompt for write operations.

- [ ] `.claude/settings.json` committed
- [ ] `claude doctor` reports no settings errors

---

## 7. Add the Azure MCP Server

### 7.1 Project MCP config (`.mcp.json`)

The file references environment variables only, so it's safe to commit.

```bash
cat > .mcp.json <<'EOF'
{
  "mcpServers": {
    "azure": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@azure/mcp@latest", "server", "start"],
      "env": {
        "AZURE_TENANT_ID": "${AZURE_TENANT_ID:-}",
        "AZURE_CLIENT_ID": "${AZURE_CLIENT_ID:-}",
        "AZURE_CLIENT_SECRET": "${AZURE_CLIENT_SECRET:-}"
      }
    }
  }
}
EOF
```

How it authenticates: the server tries the service principal variables first; if they're empty, it falls back to your `az login` session (then Azure PowerShell, then browser sign-in).

<details>
<summary>CLI equivalent instead of editing <code>.mcp.json</code></summary>

```bash
claude mcp add --scope project --transport stdio azure \
  -- npx -y @azure/mcp@latest server start
```

Credentials then come from the environment Claude Code is launched with ([§7.2](#72-launcher-script)).
</details>

<details>
<summary>Alternative: Microsoft's Azure plugin for Claude Code</summary>

Inside a Claude Code session:

```text
/plugin install azure@claude-plugins-official
```

This bundles the same MCP server with Azure-specific skills. Use it **instead of** `.mcp.json`, not as well, to avoid two copies of the server.
</details>

### 7.2 Launcher script

Load the secret from Key Vault into the environment at launch, so it never sits in a file.

```bash
cat > start-claude.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

export AZURE_TENANT_ID="<tenant-id>"
export AZURE_CLIENT_ID="<client-id>"
export AZURE_CLIENT_SECRET="$(az keyvault secret show \
  --vault-name "<your-key-vault-name>" \
  --name graph-connector-client-secret \
  --query value -o tsv)"

exec claude "$@"
EOF
chmod +x start-claude.sh
```

> [!NOTE]
> Processes Claude Code starts inherit this environment, which is why §6 denies commands that print secrets. For stronger isolation, use the certificate from Part 1: replace `AZURE_CLIENT_SECRET` with `AZURE_CLIENT_CERTIFICATE_PATH` in both files.

- [ ] `.mcp.json` and `start-claude.sh` created
- [ ] `start-claude.sh` contains no literal secret

---

## 8. Optional: Microsoft Graph MCP Server (preview)

Microsoft MCP Server for Enterprise exposes Graph to MCP clients through three **read-only** tools (`microsoft_graph_suggest_queries`, `microsoft_graph_get`, `microsoft_graph_list_properties`).

> [!CAUTION]
> - **Preview**: behavior and setup may change.
> - **Delegated only**: Claude Code acts as *you*, limited to your own Entra rights. The Part 1 app-only credentials don't apply.
> - Limited to 100 calls per minute per user, plus normal Graph throttling. Global cloud only.

### 8.1 Provision the server in the tenant (once)

PowerShell 7, as Application Administrator or Cloud Application Administrator:

```powershell
Install-Module Microsoft.Entra.Beta -Force -AllowClobber     # 1.0.13 or later
Connect-Entra -Scopes 'Application.ReadWrite.All','Directory.Read.All','DelegatedPermissionGrant.ReadWrite.All'
Get-EntraContext                                            # confirm tenant and account
Grant-EntraBetaMCPServerPermission -ApplicationName VisualStudioCode
```

This registers the MCP server (appId `e8c77dc2-69b3-43f4-bc51-3213c9d915b4`) in your tenant. Scopes follow the pattern `MCP.<GraphScope>`, for example `MCP.User.Read.All`.

### 8.2 Authorize Claude Code as a client

> [!IMPORTANT]
> Microsoft's published one-step grant covers **VS Code** only. For other clients, follow the **Custom MCP clients** tab on Microsoft's [Get started](https://learn.microsoft.com/en-us/graph/mcp-server/get-started) page. I couldn't verify that tab's exact steps, so treat 8.2–8.3 as the expected shape and confirm against it.

Expected shape: register a public-client app for Claude Code with redirect URI `http://localhost:8080/callback`, then grant it the `MCP.*` scopes you want using the method in that tab.

```bash
az ad app create --display-name "claude-code-graph-mcp" \
  --sign-in-audience AzureADMyOrg \
  --public-client-redirect-uris "http://localhost:8080/callback" \
  --is-fallback-public-client true
export MCP_CLIENT_ID="$(az ad app list --display-name claude-code-graph-mcp --query '[0].appId' -o tsv)"
```

### 8.3 Add the server to Claude Code

```bash
claude mcp add --scope user --transport http \
  --client-id "$MCP_CLIENT_ID" --callback-port 8080 \
  ms-graph https://mcp.svc.cloud.microsoft/enterprise
```

Then authenticate inside a session:

```text
/mcp        → select ms-graph → Authenticate → sign in in the browser
```

User scope makes it available in every project; use `--scope project` to keep it to `~/azure-ops`.

- [ ] `/mcp` shows `ms-graph` as connected
- [ ] Graph MCP sign-ins visible in Graph activity logs (filter appId `e8c77dc2-69b3-43f4-bc51-3213c9d915b4`)

---

## 9. Launch and verify

```bash
cd ~/azure-ops
./start-claude.sh
```

First launch prompts you to approve the project's `azure` MCP server: approve it.

Inside the session:

```text
/mcp
```

Expect `azure` (and `ms-graph`, if §8 was done) listed as connected.

Run these prompts in order:

| # | Prompt | Expected |
|---|---|---|
| 1 | `Which Azure subscription and identity are the azure MCP tools using?` | Your subscription; the `graph-connector` service principal |
| 2 | `List the resource groups in my subscription.` | Table of resource groups (via MCP) |
| 3 | `Run graph_test.py and summarize the result.` | `[PASS]` with up to 5 users, no approval prompt |
| 4 | `Show my signed-in az account.` | Your user account (Channel A) |
| 5 | `Create a resource group called rg-claude-test in eastus.` | **Prompt** asking approval (`ask` rule), or an authorization error via MCP since the SP is Reader. Decline. |
| 6 | `Delete resource group rg-anything.` | Blocked by the `deny` rule |
| 7 *(if §8)* | `Using Microsoft Graph, how many users are in my tenant?` | A number, via `ms-graph` tools |

- [ ] Prompts 1–4 succeed
- [ ] Prompt 5 asks for approval or is refused by Azure
- [ ] Prompt 6 is blocked
- [ ] (If §8) Prompt 7 succeeds

---

## 10. Daily use

```bash
cd ~/azure-ops && ./start-claude.sh
```

Example asks:

- "Which VMs in rg-prod are stopped, and how long since each was last started?"
- "Find storage accounts that allow public blob access."
- "List users created in the last 7 days." *(Graph)*
- "Draft the `az` commands to add a tag `owner=ops` to every resource in rg-dev. Don't run them yet."

Habits:

- Ask for the command first, run it second, for anything that changes state.
- `claude --continue` resumes the last session in this folder.
- Rotate the secret before expiry (Part 1 §6). Nothing in this workspace needs editing afterwards, because the launcher reads Key Vault.

---

## 11. Rollback

```bash
# Remove MCP servers
claude mcp remove azure
claude mcp remove ms-graph --scope user        # if added; also clears its OAuth tokens

# Remove the Azure role
az role assignment delete --assignee "$APP_ID" --role Reader --scope "/subscriptions/$SUB_ID"

# Remove the Graph MCP client app (if created)
az ad app delete --id "$MCP_CLIENT_ID"

# Remove the workspace
rm -rf ~/azure-ops
```

Disable the Graph MCP server tenant-wide (it can't be deleted):

```http
PATCH https://graph.microsoft.com/v1.0/servicePrincipals(appId='e8c77dc2-69b3-43f4-bc51-3213c9d915b4')
Content-Type: application/json

{ "accountEnabled": false }
```

Uninstall Claude Code (native install, macOS/Linux):

```bash
rm -f ~/.local/bin/claude && rm -rf ~/.local/share/claude
```

---

## 12. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `claude: command not found` | New terminal not opened, or PATH not updated | Open a new terminal; see [install troubleshooting](https://code.claude.com/docs/en/troubleshoot-install.md) |
| `/mcp` shows `azure` failed | Node.js missing or old, or first `npx` download slow | `node --version`; run `npx -y @azure/mcp@latest server start --help` once by hand |
| `azure` server not offered at launch | Launched outside `~/azure-ops`, or approval previously declined | `cd ~/azure-ops`; `claude mcp reset-project-choices` |
| MCP calls return `AuthorizationFailed` | Service principal lacks RBAC on that scope | §4; allow a few minutes for role propagation |
| MCP tools act as your user, not the SP | `AZURE_*` variables empty, so the server fell back to `az login` | Start with `./start-claude.sh`, not `claude` |
| `AADSTS7000215` from MCP | Expired or wrong secret in Key Vault | New secret (Part 1 §6), update Key Vault |
| Everything prompts, even allowed commands | Command shape doesn't match the rule (extra wrapper, full path) | Adjust the rule, or approve with "don't ask again" |
| `ms-graph` auth fails with redirect mismatch | Callback port differs from registered redirect URI | Re-add with matching `--callback-port`; update Claude Code (`claude update`) |
| `ms-graph` returns 403 | Your account or the client lacks the `MCP.*` scope | Re-check §8.2 against Microsoft's custom-client steps |

---

## 13. Sign-off

| Check | Result |
|---|---|
| Date / operator | `<YYYY-MM-DD>` / `<name>` |
| Claude Code version | `<claude --version>` |
| Service principal role and scope | Reader / `<scope>` |
| MCP servers connected | azure / ms-graph |
| Verification prompts 1–6 (7) | Pass / Fail |

- [ ] Workspace committed (no secrets): `git status` clean, `git log` shows `.mcp.json`, `.claude/settings.json`, `CLAUDE.md`

**References:** [Claude Code setup](https://code.claude.com/docs/en/setup) · [Claude Code MCP](https://code.claude.com/docs/en/mcp) · [Claude Code permissions](https://code.claude.com/docs/en/permissions) · [Azure MCP Server](https://github.com/mcp/com.microsoft/azure) · [Microsoft MCP Server for Enterprise](https://learn.microsoft.com/graph/mcp-server/overview) · [Get started (Graph MCP)](https://learn.microsoft.com/en-us/graph/mcp-server/get-started)
