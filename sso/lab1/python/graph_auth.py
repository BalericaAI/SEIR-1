import os
from azure.identity import DeviceCodeCredential

GRAPH_SCOPE = "https://graph.microsoft.com/.default"


def get_graph_token():
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    client_id = os.environ.get("AZURE_CLIENT_ID")

    if not tenant_id:
        raise RuntimeError(
            "AZURE_TENANT_ID environment variable is not set."
        )

    if not client_id:
        raise RuntimeError(
            "AZURE_CLIENT_ID environment variable is not set."
        )

    credential = DeviceCodeCredential(
        tenant_id=tenant_id,
        client_id=client_id,
    )

    token = credential.get_token(GRAPH_SCOPE)

    return token.token


def graph_headers():
    token = get_graph_token()

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
