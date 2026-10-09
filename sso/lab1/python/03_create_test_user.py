import getpass
import requests

from graph_auth import graph_headers


GRAPH_URL = "https://graph.microsoft.com/v1.0"

DOMAIN = "balerica-ai.org"

USER_NAME = "seirverify"

UPN = f"{USER_NAME}@{DOMAIN}"


print("=" * 70)
print("CREATE MICROSOFT ENTRA TEST USER")
print("=" * 70)

print()
print(f"User Principal Name: {UPN}")


password = getpass.getpass(
    "\nEnter temporary password: "
)


user_data = {

    "accountEnabled": True,

    "displayName":
        "SEIR Domain Verification",

    "mailNickname":
        USER_NAME,

    "userPrincipalName":
        UPN,

    "passwordProfile": {

        "forceChangePasswordNextSignIn":
            True,

        "password":
            password,
    },
}


response = requests.post(
    f"{GRAPH_URL}/users",
    headers=graph_headers(),
    json=user_data,
    timeout=30,
)


if response.status_code == 201:

    user = response.json()

    print()
    print("USER CREATION: PASS")
    print()
    print(
        "Display Name:",
        user["displayName"]
    )

    print(
        "UPN:",
        user["userPrincipalName"]
    )

    print(
        "Object ID:",
        user["id"]
    )


else:

    print()
    print("USER CREATION: FAIL")
    print()
    print(
        "HTTP Status:",
        response.status_code
    )

    print(
        response.text
    )
