import requests

from graph_auth import graph_headers


GRAPH_URL = "https://graph.microsoft.com/v1.0"

UPN = "seirverify@balerica-ai.org"


print("=" * 70)
print("REMOVE TEST USER")
print("=" * 70)


response = requests.delete(
    f"{GRAPH_URL}/users/{UPN}",
    headers=graph_headers(),
    timeout=30,
)


if response.status_code == 204:

    print()
    print(
        f"REMOVED: {UPN}"
    )


elif response.status_code == 404:

    print()
    print(
        f"USER NOT FOUND: {UPN}"
    )


else:

    print()
    print("DELETE FAILED")

    print(
        "HTTP Status:",
        response.status_code
    )

    print(
        response.text
    )
