import requests

from graph_auth import graph_headers


GRAPH_URL = "https://graph.microsoft.com/v1.0"

UPN = "seirverify@balerica-ai.org"


print("=" * 70)
print("VERIFY MICROSOFT ENTRA USER")
print("=" * 70)


response = requests.get(
    f"{GRAPH_URL}/users/{UPN}",
    headers=graph_headers(),
    timeout=30,
)


if response.status_code == 200:

    user = response.json()

    print()
    print("USER VERIFICATION: PASS")
    print()

    print(
        "Display Name:",
        user.get("displayName")
    )

    print(
        "UPN:",
        user.get(
            "userPrincipalName"
        )
    )

    print(
        "Object ID:",
        user.get("id")
    )

    print(
        "Account Enabled:",
        user.get(
            "accountEnabled"
        )
    )


else:

    print()
    print("USER VERIFICATION: FAIL")

    print(
        response.text
    )
