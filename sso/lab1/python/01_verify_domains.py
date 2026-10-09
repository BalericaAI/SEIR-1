import requests

from graph_auth import graph_headers


GRAPH_URL = "https://graph.microsoft.com/v1.0"

GCP_DOMAINS = [
    "balerica-ai.org",
    "balerica-ai.cloud",
    "chewygrows.net",
]


print("=" * 70)
print("SEIR DOMAIN VERIFICATION")
print("=" * 70)

response = requests.get(
    f"{GRAPH_URL}/domains",
    headers=graph_headers(),
    timeout=30,
)

response.raise_for_status()

domains = response.json()["value"]


for expected_domain in GCP_DOMAINS:

    match = next(
        (
            domain
            for domain in domains
            if domain["id"].lower()
            == expected_domain.lower()
        ),
        None,
    )

    if match is None:

        print(
            f"{expected_domain:<25} "
            "NOT FOUND"
        )

        continue

    verified = match.get(
        "isVerified",
        False,
    )

    auth_type = match.get(
        "authenticationType",
        "Unknown",
    )

    status = (
        "VERIFIED"
        if verified
        else "NOT VERIFIED"
    )

    print(
        f"{expected_domain:<25} "
        f"{status:<15} "
        f"{auth_type}"
    )
