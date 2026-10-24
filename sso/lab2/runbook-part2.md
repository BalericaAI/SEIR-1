# Runbook: Python Connectivity Test for Microsoft Graph (Part 2 of 3)

> **Scope:** Run a Python script that authenticates as the `graph-connector` app (from Part 1) and reads a few users from Microsoft Graph.
> **Previous:** [Part 1](runbook.md) — app registration, `User.Read.All` permission, credentials.
> **Next:** Part 3 connects Claude Code.

> [!NOTE]
> The test task is **list users** (`GET /v1.0/users`). It is read-only and uses only the permission granted in Part 1, so nothing in the tenant changes.

---

## Table of contents

1. [Prerequisites](#1-prerequisites)
2. [How the script works](#2-how-the-script-works)
3. [Set up the Python environment](#3-set-up-the-python-environment)
4. [Configure credentials](#4-configure-credentials)
5. [Run the test](#5-run-the-test)
6. [Interpret the result](#6-interpret-the-result)
7. [Optional: Graph SDK variant](#7-optional-graph-sdk-variant)
8. [Clean up](#8-clean-up)
9. [Troubleshooting](#9-troubleshooting)
10. [Sign-off](#10-sign-off)

---

## 1. Prerequisites

| Item | Requirement |
|---|---|
| Part 1 | Completed; §7 verification passed |
| Handoff values | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, credential location (Part 1 §8) |
| Python | 3.9 or later: `python3 --version` |
| Network | Outbound HTTPS to `login.microsoftonline.com` and `graph.microsoft.com` |
| Files | `graph_test.py` (supplied with this runbook) |
| Optional | Azure CLI signed in, if pulling the secret from Key Vault |

```bash
python3 --version
curl -sI https://graph.microsoft.com/v1.0/ | head -1    # expect HTTP 401 (reachable, unauthenticated)
```

- [ ] Python 3.9+ available
- [ ] Graph endpoint reachable (401 is the expected response)

---

## 2. How the script works

| Step | What happens | Library |
|---|---|---|
| 1 | Checks required environment variables | stdlib |
| 2 | Gets an app-only token for `https://graph.microsoft.com/.default` | `azure-identity` (`EnvironmentCredential`) |
| 3 | Decodes the token and checks for the `User.Read.All` role | stdlib |
| 4 | Calls `GET /v1.0/users?$top=5&$select=displayName,userPrincipalName` | `requests` |
| 5 | Prints `[PASS]` or `[FAIL]` and exits with a status code | stdlib |

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Authentication failed (token not issued) |
| `2` | Graph call failed (token issued, request rejected) |
| `3` | Configuration missing |

The exit codes make the script usable as a CI health check.

---

## 3. Set up the Python environment

```bash
mkdir -p ~/graph-test && cd ~/graph-test
cp /path/to/graph_test.py .

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

cat > requirements.txt <<'EOF'
azure-identity>=1.17
requests>=2.31
EOF

pip install -r requirements.txt
```

- [ ] `pip show azure-identity requests` lists both packages

---

## 4. Configure credentials

The script reads the same variable names `azure-identity` uses. Use the option matching the credential type you chose in Part 1 §6.

### Option A — Client secret from Key Vault (recommended)

```bash
export AZURE_TENANT_ID="<tenant-id>"
export AZURE_CLIENT_ID="<client-id>"
export AZURE_CLIENT_SECRET="$(az keyvault secret show \
  --vault-name "<your-key-vault-name>" \
  --name graph-connector-client-secret \
  --query value -o tsv)"
```

### Option B — Client secret typed in

```bash
export AZURE_TENANT_ID="<tenant-id>"
export AZURE_CLIENT_ID="<client-id>"
read -rs AZURE_CLIENT_SECRET && export AZURE_CLIENT_SECRET   # paste, press Enter; not echoed
```

### Option C — Certificate

```bash
export AZURE_TENANT_ID="<tenant-id>"
export AZURE_CLIENT_ID="<client-id>"
export AZURE_CLIENT_CERTIFICATE_PATH="$HOME/graph-test/graph-connector.pem"   # key + cert PEM from Part 1
unset AZURE_CLIENT_SECRET
```

> [!WARNING]
> Don't put the secret in `graph_test.py`, a committed `.env` file, or shell history. If you use a local `.env`, add it to `.gitignore`.

Windows PowerShell equivalent:

```powershell
$env:AZURE_TENANT_ID     = "<tenant-id>"
$env:AZURE_CLIENT_ID     = "<client-id>"
$env:AZURE_CLIENT_SECRET = (az keyvault secret show --vault-name "<vault>" --name graph-connector-client-secret --query value -o tsv)
```

- [ ] `env | grep AZURE_ | sed 's/=.*/=***/'` shows the expected variable names

---

## 5. Run the test

```bash
python graph_test.py
```

Options:

```bash
python graph_test.py --top 10      # list up to 10 users
python graph_test.py; echo "exit=$?"
```

**Expected output**

```text
[ OK ] Config found (auth: secret)
[ OK ] Token acquired  tenant=<tenant-id>  app=<client-id>
       roles=['User.Read.All']
[ OK ] GET /users -> HTTP 200, 5 user(s) returned
       - Ada Lovelace <ada@contoso.com>
       - ...
[PASS] Microsoft Graph connectivity verified
```

- [ ] Output ends with `[PASS]`
- [ ] Exit code is `0`
- [ ] `tenant=` and `app=` match the handoff values from Part 1

---

## 6. Interpret the result

| Output line | Meaning | Go to |
|---|---|---|
| `[FAIL] Missing environment variables` | Variables not exported in this shell | §4 |
| `[FAIL] Token request failed: AADSTS…` | Entra rejected the credential | §9 by AADSTS code |
| `[WARN] 'User.Read.All' not in token roles` | Permission or consent missing | Part 1 §5 |
| `[FAIL] GET /users -> HTTP 403` | Token issued but not authorized | Part 1 §5, then wait 1–2 min |
| `[FAIL] GET /users -> HTTP 429` | Throttled | Wait and retry |
| `[PASS]` | Connectivity verified | §10 |

On any `[FAIL]` from Graph, the script prints a `request-id`. Include it if you open a Microsoft support case.

---

## 7. Optional: Graph SDK variant

The main script uses `requests` so every HTTP step is visible. For production code, Microsoft's SDK handles paging, retries and throttling. Equivalent test:

```bash
pip install msgraph-sdk
```

```python
# graph_test_sdk.py
import asyncio
from azure.identity.aio import EnvironmentCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.users_request_builder import UsersRequestBuilder

async def main():
    credential = EnvironmentCredential()
    client = GraphServiceClient(credential, scopes=["https://graph.microsoft.com/.default"])
    query = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters(
        top=5, select=["displayName", "userPrincipalName"]
    )
    config = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(query_parameters=query)
    result = await client.users.get(request_configuration=config)
    for u in result.value:
        print(f"{u.display_name} <{u.user_principal_name}>")
    await credential.close()

asyncio.run(main())
```

```bash
python graph_test_sdk.py
```

---

## 8. Clean up

```bash
unset AZURE_CLIENT_SECRET AZURE_CLIENT_CERTIFICATE_PATH
deactivate
```

Keep `~/graph-test` if you want to reuse it as a health check; delete it otherwise:

```bash
rm -rf ~/graph-test
```

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'azure'` | venv not active or packages not installed | `source .venv/bin/activate && pip install -r requirements.txt` |
| `AADSTS7000215: Invalid client secret` | Secret ID used instead of value, or expired | New secret (Part 1 §6) |
| `AADSTS700016: Application … not found` | Wrong `AZURE_CLIENT_ID` or tenant | Re-check handoff values |
| `AADSTS90002: Tenant … not found` | Wrong `AZURE_TENANT_ID` | Use the GUID from `az account show --query tenantId` |
| `AADSTS700027` (certificate) | Cert not uploaded, expired, or PEM lacks private key | Re-upload cert; PEM must contain key + cert |
| `EnvironmentCredential authentication unavailable` | Variables missing in the process environment | `export` them in the same shell |
| `403 Authorization_RequestDenied` | Admin consent missing or propagating | Part 1 §5; wait 1–2 min |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Corporate TLS-inspecting proxy | `export REQUESTS_CA_BUNDLE=/path/to/corp-ca.pem` (don't disable verification) |
| Timeout | Firewall blocks Microsoft endpoints | Allow `login.microsoftonline.com` and `graph.microsoft.com` on 443 |

---

## 10. Sign-off

| Check | Result |
|---|---|
| Date / operator | `<YYYY-MM-DD>` / `<name>` |
| Credential type used | Secret / Certificate |
| Exit code | `0` |
| Users returned | `<n>` |
| Sign-in visible in Entra (**Monitoring → Sign-in logs → Service principal sign-ins**) | Yes / No |

- [ ] All checks pass; ready for Part 3
