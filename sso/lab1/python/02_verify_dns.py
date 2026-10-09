import dns.resolver


DOMAINS = [
    "balerica-ai.org",
    "balerica-ai.cloud",
    "chewygrows.net",
]


def query_dns(domain, record_type):

    print(
        f"\n{domain} "
        f"{record_type} records"
    )

    print("-" * 60)

    try:

        answers = dns.resolver.resolve(
            domain,
            record_type,
        )

        for answer in answers:
            print(answer)

        return True

    except Exception as error:

        print(
            f"DNS QUERY FAILED: "
            f"{error}"
        )

        return False


print("=" * 70)
print("PUBLIC DNS VERIFICATION")
print("=" * 70)


for domain in DOMAINS:

    query_dns(
        domain,
        "NS",
    )

    query_dns(
        domain,
        "TXT",
    )
