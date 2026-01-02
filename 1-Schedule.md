SEIR-I — 16-Week Curriculum Leading to Lab 1
GCP Infrastructure + Azure AD Identity

Phase 0: Orientation & Mental Models (Weeks 1–2)
Identity first. Tools later.

Week 1 — What Identity Actually Controls
    Focus
    What “identity” means in real systems
    Why identity failures are worse than infrastructure failures
    Difference between authentication, authorization, and trust

Outcomes
  Students can explain:
      why lockouts are outages
      why access recovery is harder than deployment rollback

Artifacts
    Written explanation: “What does identity control in a cloud system?”


Week 2 — Cloud as a Trust Boundary
Focus
    GCP as a resource plane
    Azure AD as a trust plane
    Why clouds are not “just compute”

Outcomes
    Students can diagram:
      user → identity provider → cloud resource
    No automation yet

Artifacts
    Hand-drawn or markdown trust diagram

Phase 1: GCP Foundations (Weeks 3–5)
Infrastructure exists before identity can act on it.

Week 3 — GCP Project & IAM Fundamentals
    Focus
    GCP projects, folders, orgs
    GCP IAM vs identity provider IAM
    Service accounts vs humans

Outcomes
    Students understand:
      who should never use service accounts
      why projects are blast-radius boundaries

Artifacts
    GCP project created manually
    IAM role mapping explanation (no automation)


Week 4 — Compute & Networking (Minimal, Intentional)
Focus
    GCE instances
    VPC basics
    Firewalls as policy, not convenience

Outcomes
Students can:
    deploy a VM
    explain why it should not be public by default

Artifacts
    Single VM
    Network diagram

Week 5 — GCP Logging & Evidence
Focus
    Cloud Logging
    Audit logs
    “If it’s not logged, it didn’t happen”

Outcomes
    Students can find:
      who accessed what
      when access was denied

Artifacts
Screenshot + explanation of a log entry

Phase 2: Azure AD / Entra ID Foundations (Weeks 6–8)
    Trust must be slow, deliberate, and explainable.

Week 6 — Azure AD / Entra ID Core Concepts

Focus
    Tenants
    Users vs groups
    App registrations
    Enterprise apps

Outcomes
    Students can explain:
      why everything starts with a tenant
      why groups matter more than users

Artifacts
    Tenant diagram
    Group strategy write-up


Week 7 — Federation & SSO (Conceptual First)

Focus
    SAML vs OIDC (what problems they solve)
    Why federation exists
    What breaks federation

Outcomes
    Students can:
      explain SSO without buzzwords
      explain why cert rotation breaks things

Artifacts
Federation flow diagram

Week 8 — PowerShell for Identity (Careful Automation)

Focus
    PowerShell basics
    Connecting to Azure AD
    Read-only identity queries

Outcomes
    Students can:
      list users and groups
      explain why write access is dangerous

Artifacts
    PowerShell script (read-only)
    Explanation of what not to automate yet


Phase 3: GCP + Azure AD Integration (Weeks 9–11)

Now the danger starts — and discipline matters.
Week 9 — Workforce Identity Federation (Theory → Practice)

Focus
    Azure AD as IdP
    GCP Workforce Identity Federation
    Trust mapping

Outcomes
    Students understand:
      who authenticates
      who authorizes
      where trust ends

Artifacts
Identity trust map

Week 10 — Controlled Access to GCP via Azure AD
Focus
    Mapping Azure AD groups to GCP IAM
    Least privilege

Outcomes
    Students can:
      log into GCP using Azure AD
      explain why only specific roles are granted

Artifacts
    Working federated login
    Access justification document

Week 11 — Identity Failure & Recovery

Focus
    What happens when federation breaks
    Break-glass concepts
    Recovery planning

Outcomes
    Students can:
      explain recovery steps
      explain why recovery must be manual

Artifacts
    Recovery runbook (written)

Phase 4: Automation with Restraint (Weeks 12–14)
Automation follows understanding — never the reverse.

Week 12 — Python for Evidence, Not Control
Focus
    Python basics
    Reading logs
    Validating access

Outcomes
    Students can:
      write a script to verify access
      not change access

Artifacts
    Python evidence script

Week 13 — PowerShell + Python Together

Focus
    Using PowerShell to query identity
    Python to validate outcomes
    Human in the loop

Outcomes
    Students understand:
      separation of duties
      why automation must be observable

Artifacts
    Combined script + explanation

Week 14 — Pre-Lab Discipline

Focus
    Review of all moving parts
    What Lab 1 will require
    What Lab 1 will not forgive

Outcomes
    Students know:
      where mistakes will hurt
      what evidence is required

Artifacts
    Pre-Lab checklist

Phase 5: Readiness & Gate (Weeks 15–16)
      You don’t “start” Lab 1 — you earn it.

Week 15 — Mock Lab (Identity-Only)

Focus
    Simulated failures
    Log interpretation
    Calm recovery

Outcomes
    Students demonstrate:
      judgment
      restraint
      evidence-based reasoning

Artifacts
    Mock incident report

Week 16 — Lab 1 Readiness Review

Focus
    Oral walkthrough
    Diagram defense
    Script explanation

Outcome
    Students are cleared (or deferred) for Lab 1

No one is forced through.









    
