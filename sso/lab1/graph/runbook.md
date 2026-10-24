# Runbook: Microsoft Graph Access on Azure (Part 1 of 3)

> **Scope:** Register an application in Microsoft Entra ID, grant it Microsoft Graph permissions, create credentials, and verify that Graph accepts its tokens.
> **Next:** Part 2 tests Python connectivity using the values in [Handoff](#8-handoff-values). Part 3 connects Claude Code.

> [!NOTE]
> Microsoft Graph is a Microsoft-hosted API (`https://graph.microsoft.com`), not something you deploy into a subscription. "Installing" it means creating an **app registration** with Graph permissions. Every Entra ID tenant already has Graph available.

---

## Table of contents

1. [Prerequisites](#1-prerequisites)
2. [Decide the auth model](#2-decide-the-auth-model)
3. [Set variables](#3-set-variables)
4. [Create the app registration](#4-create-the-app-registration)
5. [Grant Graph permissions](#5-grant-graph-permissions)
6. [Create credentials](#6-create-credentials)
7. [Verify](#7-verify)
8. [Handoff values](#8-handoff-values)
9. [Rollback](#9-rollback)
10. [Security checklist](#10-security-checklist)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prerequisites

| Item | Requirement |
|---|---|
| Entra role (register app) | **Application Developer**, **Application Administrator**, or **Cloud Application Administrator** |
| Entra role (admin consent for application permissions) | **Privileged Role Administrator** or **Global Administrator** |
| Azure CLI | 2.60 or later: `az version` |
| `jq` | For parsing JSON in the shell |
| `curl` | For the verification step |
| Optional: Key Vault | An existing vault, if you'll store the secret there (recommended) |

```bash
az version
az login --tenant <your-tenant-id-or-domain>
az account show --query "{tenant:tenantId, user:user.name}" -o table
```

- [ ] Signed in to the correct tenant
- [ ] Have (or can borrow) a role that can grant admin consent

---

## 2. Decide the auth model

| Model | Flow | Use when | Used in |
|---|---|---|---|
| **App-only** | Client credentials (secret or certificate) | Unattended scripts, services, CI | Part 2 (Python test) |
| **Delegated** | Device code / interactive | Acting as a signed-in user | Optional for Part 3 |

This runbook sets up **app-only** as the primary path and optionally enables delegated sign-in so Part 3 has both options.

> [!IMPORTANT]
> Start with the smallest permission set. This runbook uses `User.Read.All` (read-only) as the test permission. Add others only when a later part needs them.

---

## 3. Set variables

```bash
export TENANT_ID="$(az account show --query tenantId -o tsv)"
export APP_NAME="graph-connector"
export GRAPH_APP_ID="00000003-0000-0000-c000-000000000000"   # Microsoft Graph's well-known appId

# Optional: Key Vault for the secret
export KV_NAME="<your-key-vault-name>"
```

---

## 4. Create the app registration

### CLI

```bash
# Single-tenant app
az ad app create \
  --display-name "$APP_NAME" \
  --sign-in-audience AzureADMyOrg \
  -o none

export APP_ID="$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv)"
export APP_OBJECT_ID="$(az ad app show --id "$APP_ID" --query id -o tsv)"

# Service principal (enterprise app) — required for app-only tokens and consent
az ad sp create --id "$APP_ID" -o none

echo "APP_ID=$APP_ID"
```

Optional, for delegated device-code sign-in in Part 3:

```bash
az ad app update --id "$APP_ID" --is-fallback-public-client true
```

### Portal equivalent

1. **Entra admin center** → **Identity** → **Applications** → **App registrations** → **New registration**.
2. Name: `graph-connector`. Supported account types: **Accounts in this organizational directory only**.
3. Leave Redirect URI empty → **Register**.
4. Copy **Application (client) ID** and **Directory (tenant) ID** from **Overview**.
5. (Optional) **Authentication** → **Allow public client flows** → **Yes** → **Save**.

- [ ] App registration exists
- [ ] Service principal exists: `az ad sp show --id "$APP_ID" --query displayName -o tsv`

---

## 5. Grant Graph permissions

Look up permission IDs from Graph's service principal rather than hard-coding them:

```bash
# Application permission (app-only)
USER_READ_ALL_ROLE=$(az ad sp show --id "$GRAPH_APP_ID" \
  --query "appRoles[?value=='User.Read.All'].id | [0]" -o tsv)

# Delegated permission (optional, for Part 3)
USER_READ_SCOPE=$(az ad sp show --id "$GRAPH_APP_ID" \
  --query "oauth2PermissionScopes[?value=='User.Read'].id | [0]" -o tsv)

echo "User.Read.All (Role): $USER_READ_ALL_ROLE"
echo "User.Read (Scope):    $USER_READ_SCOPE"
```

Add them to the app:

```bash
az ad app permission add --id "$APP_ID" \
  --api "$GRAPH_APP_ID" \
  --api-permissions "${USER_READ_ALL_ROLE}=Role" "${USER_READ_SCOPE}=Scope"
```

Grant admin consent (requires the admin role from [Prerequisites](#1-prerequisites)):

```bash
az ad app permission admin-consent --id "$APP_ID"
```

> [!TIP]
> Consent can take a minute to propagate. If verification returns `403`, wait 1–2 minutes and retry.

### Portal equivalent

1. App registration → **API permissions** → **Add a permission** → **Microsoft Graph**.
2. **Application permissions** → `User.Read.All` → **Add permissions**.
3. (Optional) **Delegated permissions** → `User.Read`.
4. **Grant admin consent for \<tenant\>** → confirm. Status column should show green checks.

- [ ] Permissions listed: `az ad app permission list --id "$APP_ID" -o table`
- [ ] Admin consent granted (Portal shows **Granted for \<tenant\>**)

---

## 6. Create credentials

Pick **one**. Certificates are preferred for production; a secret is fine for the Part 2 test.

### Option A — Client secret (quickest)

```bash
CLIENT_SECRET=$(az ad app credential reset \
  --id "$APP_ID" \
  --display-name "graph-connector-secret" \
  --years 1 \
  --append \
  --query password -o tsv)
```

> [!WARNING]
> The secret value is shown **only once**. Store it immediately; do not paste it into tickets, chat, or source control.

Store in Key Vault (recommended):

```bash
az keyvault secret set \
  --vault-name "$KV_NAME" \
  --name "graph-connector-client-secret" \
  --value "$CLIENT_SECRET" \
  -o none
```

### Option B — Certificate (recommended for production)

```bash
openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout graph-connector.key \
  -out graph-connector.crt \
  -subj "/CN=graph-connector"

# Upload the public cert to the app
az ad app credential reset --id "$APP_ID" --cert @graph-connector.crt --append -o none

# Combined PEM for the client side (Python, Part 2)
cat graph-connector.key graph-connector.crt > graph-connector.pem
chmod 600 graph-connector.key graph-connector.pem
```

Or generate and keep the cert in Key Vault:

```bash
az ad app credential reset --id "$APP_ID" \
  --create-cert --cert graph-connector-cert --keyvault "$KV_NAME" --append -o none
```

- [ ] Credential listed: `az ad app credential list --id "$APP_ID" -o table` (secrets) or `az ad app show --id "$APP_ID" --query keyCredentials` (certs)
- [ ] Expiry date recorded in the team calendar

---

## 7. Verify

Request an app-only token and call Graph. (Uses Option A; for a certificate, defer verification to Part 2.)

```bash
TOKEN=$(curl -s -X POST \
  "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token" \
  -d "client_id=$APP_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "scope=https://graph.microsoft.com/.default" \
  -d "grant_type=client_credentials" | jq -r .access_token)

test "$TOKEN" != "null" && echo "Token acquired" || echo "Token request FAILED"

curl -s -H "Authorization: Bearer $TOKEN" \
  'https://graph.microsoft.com/v1.0/users?$top=1&$select=displayName,userPrincipalName' | jq
```

**Expected:** JSON with a `value` array containing one user.

Inspect the token's roles (optional):

```bash
echo "$TOKEN" | cut -d. -f2 | tr '_-' '/+' | base64 -d 2>/dev/null | jq '.roles, .aud, .tid'
```

Expect `roles` to include `"User.Read.All"` and `aud` to be `https://graph.microsoft.com`.

- [ ] Token acquired
- [ ] `/v1.0/users` returns data
- [ ] `roles` claim contains `User.Read.All`

Clear the secret from the shell when done:

```bash
unset CLIENT_SECRET TOKEN
```

---

## 8. Handoff values

Record these for Parts 2 and 3. **Never record the secret value itself here.**

| Key | Value |
|---|---|
| `AZURE_TENANT_ID` | `<TENANT_ID>` |
| `AZURE_CLIENT_ID` | `<APP_ID>` |
| Credential type | Secret / Certificate |
| Secret / cert location | `kv://<KV_NAME>/graph-connector-client-secret` or path to `.pem` |
| Credential expiry | `<YYYY-MM-DD>` |
| Granted permissions | `User.Read.All` (Application), `User.Read` (Delegated) |
| Public client flows | Enabled / Disabled |

```bash
echo "AZURE_TENANT_ID=$TENANT_ID"
echo "AZURE_CLIENT_ID=$APP_ID"
```

> [!NOTE]
> The `AZURE_TENANT_ID` / `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` names match what `azure-identity`'s `EnvironmentCredential` reads, which simplifies Part 2.

---

## 9. Rollback

```bash
# Removes the app registration and its service principal
az ad app delete --id "$APP_ID"

# Remove stored secret (soft-delete; purge if required by policy)
az keyvault secret delete --vault-name "$KV_NAME" --name "graph-connector-client-secret"
```

Deleted app registrations remain restorable for 30 days under **App registrations → Deleted applications**.

---

## 10. Security checklist

- [ ] Only the permissions needed for the current part are granted
- [ ] Secret stored in Key Vault (or cert used instead); not in code, `.env` committed to git, or chat
- [ ] Credential expiry ≤ 12 months, with a rotation reminder set
- [ ] App **Owners** set to at least two people (App registration → **Owners**)
- [ ] Sign-in logs reviewed after first use: **Entra** → **Monitoring** → **Sign-in logs** → **Service principal sign-ins**
- [ ] (If licensed) Conditional Access for workload identities considered

---

## 11. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `AADSTS7000215: Invalid client secret` | Used the secret **ID** instead of **value**, or it expired | Create a new secret (§6) |
| `AADSTS700016: Application not found` | Wrong tenant or client ID | Re-check `TENANT_ID` / `APP_ID` |
| `403 Authorization_RequestDenied` | Admin consent missing or not yet propagated | Re-run `admin-consent`; wait 1–2 min |
| Token has no `roles` claim | Permission added as Delegated, not Application | Re-add with `=Role` (§5) |
| `admin-consent` fails with insufficient privileges | Current user lacks the consent role | Have a Privileged Role Admin / Global Admin run it or use the Portal button |
| `az ad sp create` says it already exists | Portal already created the SP | Safe to ignore |
