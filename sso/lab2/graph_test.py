#!/usr/bin/env python3
"""
graph_test.py - Microsoft Graph connectivity smoke test (app-only).

Acquires a client-credentials token for Microsoft Graph and lists a few users
from the tenant. Uses the app registration created in Part 1.

Required environment variables:
    AZURE_TENANT_ID                 Directory (tenant) ID
    AZURE_CLIENT_ID                 Application (client) ID
    and ONE of:
    AZURE_CLIENT_SECRET             Client secret value
    AZURE_CLIENT_CERTIFICATE_PATH   Path to PEM containing private key + cert

Exit codes:
    0  success
    1  authentication failed
    2  Graph call failed
    3  configuration missing
"""

import argparse
import base64
import json
import os
import sys

import requests
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import EnvironmentCredential

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"
EXPECTED_ROLE = "User.Read.All"


def missing_config() -> list[str]:
    missing = [v for v in ("AZURE_TENANT_ID", "AZURE_CLIENT_ID") if not os.environ.get(v)]
    if not (os.environ.get("AZURE_CLIENT_SECRET") or os.environ.get("AZURE_CLIENT_CERTIFICATE_PATH")):
        missing.append("AZURE_CLIENT_SECRET or AZURE_CLIENT_CERTIFICATE_PATH")
    return missing


def decode_claims(token: str) -> dict:
    """Decode the JWT payload for display only (no signature validation)."""
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def main() -> int:
    parser = argparse.ArgumentParser(description="Microsoft Graph connectivity test")
    parser.add_argument("--top", type=int, default=5, help="number of users to list (default 5)")
    args = parser.parse_args()

    # 1. Configuration
    missing = missing_config()
    if missing:
        print("[FAIL] Missing environment variables: " + ", ".join(missing), file=sys.stderr)
        return 3
    auth_mode = "certificate" if os.environ.get("AZURE_CLIENT_CERTIFICATE_PATH") else "secret"
    print(f"[ OK ] Config found (auth: {auth_mode})")

    # 2. Token
    try:
        token = EnvironmentCredential().get_token(GRAPH_SCOPE).token
    except ClientAuthenticationError as exc:
        first_line = str(exc).strip().splitlines()[0] if str(exc).strip() else repr(exc)
        print(f"[FAIL] Token request failed: {first_line}", file=sys.stderr)
        return 1

    claims = decode_claims(token)
    roles = claims.get("roles", [])
    print(f"[ OK ] Token acquired  tenant={claims.get('tid')}  app={claims.get('appid')}")
    print(f"       roles={roles or 'none'}")
    if EXPECTED_ROLE not in roles:
        print(f"[WARN] '{EXPECTED_ROLE}' not in token roles; the Graph call will likely return 403.")

    # 3. Graph call: list users
    resp = requests.get(
        f"{GRAPH_BASE}/users",
        headers={"Authorization": f"Bearer {token}"},
        params={"$top": args.top, "$select": "displayName,userPrincipalName"},
        timeout=30,
    )
    if not resp.ok:
        try:
            err = resp.json().get("error", {})
        except ValueError:
            err = {}
        print(
            f"[FAIL] GET /users -> HTTP {resp.status_code} "
            f"{err.get('code', '')}: {err.get('message', resp.text[:200])}",
            file=sys.stderr,
        )
        print(f"       request-id={resp.headers.get('request-id')}", file=sys.stderr)
        return 2

    users = resp.json().get("value", [])
    print(f"[ OK ] GET /users -> HTTP {resp.status_code}, {len(users)} user(s) returned")
    for u in users:
        print(f"       - {u.get('displayName') or '(no name)'} <{u.get('userPrincipalName')}>")

    print("[PASS] Microsoft Graph connectivity verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
