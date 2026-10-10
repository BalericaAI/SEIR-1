# SEIR-1 — Python Domain Lab Troubleshooting Guide

## Purpose

Use this document when the Python domain verification lab does not work.

Do **not** randomly change settings.

Do **not** recreate everything.

Do **not** delete the domain.

Do **not** change MX records.

Instead, determine which layer is failing.

The system has several layers:

```text
LOCAL COMPUTER
      |
      v
Python
      |
      v
Python Packages
      |
      v
GCP Authentication
      |
      v
Google Cloud DNS
      |
      v
Public DNS Delegation
      |
      v
Microsoft Domain Verification
      |
      v
Microsoft Graph Authentication
      |
      v
Microsoft Entra User Creation
```

Always troubleshoot the **first failed layer**.

---

# Rule 1 — Identify the Failed Script

The lab contains:

```text
01_verify_domains.py

02_verify_dns.py

03_create_test_user.py

04_verify_test_user.py

05_cleanup_test_user.py
```

Record which script failed.

Example:

```text
FAILED SCRIPT:

02_verify_dns.py
```

Do not report:

```text
Azure doesn't work.
```

or:

```text
Python doesn't work.
```

Report the actual script and error.

---

# Gate 1 — Verify Python

Run:

```bash
python --version
```

If that fails:

```bash
python3 --version
```

Expected:

```text
Python 3.x
```

If neither command works, Python is not installed or not in your system path.

Stop here.

---

# Gate 2 — Verify You Are in the Correct Directory

macOS / Linux:

```bash
pwd
ls
```

Windows PowerShell:

```powershell
Get-Location
Get-ChildItem
```

You should see:

```text
requirements.txt
graph_auth.py
01_verify_domains.py
02_verify_dns.py
03_create_test_user.py
04_verify_test_user.py
05_cleanup_test_user.py
```

If the files are not present, you are in the wrong directory.

---

# Gate 3 — Verify Python Packages

Run:

```bash
python -m pip show azure-identity
```

Then:

```bash
python -m pip show requests
```

Then:

```bash
python -m pip show dnspython
```

If a package is missing:

```bash
python -m pip install -r requirements.txt
```

Or:

```bash
python -m pip install azure-identity requests dnspython
```

---

# Error — ModuleNotFoundError

Example:

```text
ModuleNotFoundError: No module named 'azure'
```

or:

```text
ModuleNotFoundError: No module named 'dns'
```

Install the required packages:

```bash
python -m pip install azure-identity requests dnspython
```

Then try again.

---

# Gate 4 — Verify GCP Authentication

Some students may have created or migrated DNS zones in Google Cloud but are no longer authenticated to GCP.

Check:

```bash
gcloud auth list
```

You should see an active account.

Example:

```text
Credentialed Accounts

ACTIVE  ACCOUNT
*       student@example.com
```

If no account is active:

```bash
gcloud auth login
```

Complete the browser authentication.

---

# Gate 5 — Verify the Correct GCP Project

Run:

```bash
gcloud config get-value project
```

Expected:

```text
your-gcp-project-id
```

If the wrong project is selected:

```bash
gcloud projects list
```

Then:

```bash
gcloud config set project YOUR_PROJECT_ID
```

Verify again:

```bash
gcloud config get-value project
```

---

# Important

Being authenticated to GCP does **not** prove that the DNS domain exists in the correct project.

It only proves:

```text
You can authenticate to Google Cloud.
```

We still need to verify the DNS zone.

---

# Gate 6 — Verify the Cloud DNS Zone Exists

Run:

```bash
gcloud dns managed-zones list
```

Look for your domain.

Example:

```text
balerica-ai.org
```

You should see a managed zone corresponding to the domain.

If the zone is missing, the domain has not been configured in the current GCP project.

---

# Gate 7 — Inspect the DNS Zone

First identify the managed zone name.

Example:

```text
balerica-ai-org
```

Then run:

```bash
gcloud dns record-sets list \
    --zone="balerica-ai-org"
```

You should see records including:

```text
SOA

NS

TXT
```

Depending on your environment, you may also see:

```text
MX

A

AAAA

CNAME
```

---

# Common Problem — Student Created a Cloud DNS Zone but Never Migrated the Domain

This is extremely common.

Creating this:

```text
Google Cloud
     |
     v
Cloud DNS Zone
```

does **not** automatically cause the Internet to use that zone.

You must also configure the domain registrar to use the Google Cloud DNS name servers.

---

# Gate 8 — Find the Google Cloud DNS Name Servers

Run:

```bash
gcloud dns managed-zones describe balerica-ai-org
```

Look for:

```text
nameServers:
```

You may see something similar to:

```text
ns-cloud-a1.googledomains.com.
ns-cloud-a2.googledomains.com.
ns-cloud-a3.googledomains.com.
ns-cloud-a4.googledomains.com.
```

Your actual servers will be different.

---

# Gate 9 — Check Public DNS Delegation

Now ask the public Internet which DNS servers are authoritative.

Run:

```bash
nslookup -type=NS balerica-ai.org
```

Or on systems with `dig`:

```bash
dig NS balerica-ai.org
```

Compare the public results with the name servers from:

```bash
gcloud dns managed-zones describe balerica-ai-org
```

They should match.

---

# Example — Correct Configuration

Google Cloud says:

```text
ns-cloud-a1.googledomains.com

ns-cloud-a2.googledomains.com

ns-cloud-a3.googledomains.com

ns-cloud-a4.googledomains.com
```

Public DNS says:

```text
ns-cloud-a1.googledomains.com

ns-cloud-a2.googledomains.com

ns-cloud-a3.googledomains.com

ns-cloud-a4.googledomains.com
```

Result:

```text
PASS
```

---

# Example — Domain Was NOT Actually Migrated

Google Cloud says:

```text
ns-cloud-a1.googledomains.com

ns-cloud-a2.googledomains.com
```

but public DNS says:

```text
ns1.oldprovider.com

ns2.oldprovider.com
```

Result:

```text
FAIL
```

The Cloud DNS zone exists, but the registrar is still pointing somewhere else.

The domain has **not actually been delegated to Google Cloud DNS**.

---

# Fix

Log in to the domain registrar.

Change the authoritative name servers to the values Google Cloud DNS assigned.

Do not invent them.

Use the values returned by:

```bash
gcloud dns managed-zones describe YOUR_ZONE
```

---

# Gate 10 — Verify TXT Records Publicly

Run:

```bash
nslookup -type=TXT balerica-ai.org
```

Or:

```bash
dig TXT balerica-ai.org
```

You should see the Microsoft verification TXT record if it is still present.

Example:

```text
MS=msXXXXXXXX
```

---

# Important Distinction

A TXT record can exist inside Google Cloud DNS but still not be visible publicly.

Example:

```text
Cloud DNS Console:

MS=msXXXXXXXX
```

but:

```bash
nslookup -type=TXT balerica-ai.org
```

returns nothing.

That usually means:

```text
Cloud DNS contains the record
```

but:

```text
Public DNS is not using that Cloud DNS zone
```

Check NS delegation.

---

# Gate 11 — Run the Python DNS Test

Run:

```bash
python 02_verify_dns.py
```

If it succeeds, Python should return the public NS and TXT records.

Remember:

```text
02_verify_dns.py
```

does **not** require Google Cloud authentication.

It queries public DNS.

Therefore:

```text
gcloud authentication failure
```

does not automatically explain:

```text
02_verify_dns.py failure
```

---

# Gate 12 — Verify Microsoft Graph Environment Variables

Windows PowerShell:

```powershell
$env:AZURE_TENANT_ID
```

and:

```powershell
$env:AZURE_CLIENT_ID
```

macOS / Linux:

```bash
echo $AZURE_TENANT_ID
```

and:

```bash
echo $AZURE_CLIENT_ID
```

Neither value should be empty.

---

# Error — AZURE_TENANT_ID Is Not Set

Windows:

```powershell
$env:AZURE_TENANT_ID="<your-tenant-id>"
```

macOS / Linux:

```bash
export AZURE_TENANT_ID="<your-tenant-id>"
```

---

# Error — AZURE_CLIENT_ID Is Not Set

Windows:

```powershell
$env:AZURE_CLIENT_ID="<your-client-id>"
```

macOS / Linux:

```bash
export AZURE_CLIENT_ID="<your-client-id>"
```

---

# Gate 13 — Verify the Entra App Registration

Your Python lab application must exist in Microsoft Entra ID.

Verify:

```text
Microsoft Entra ID
        |
        v
App registrations
        |
        v
Your Python Lab Application
```

Confirm that you copied the correct:

```text
Application (client) ID

Directory (tenant) ID
```

A very common mistake is copying the wrong GUID.

---

# Gate 14 — Verify Microsoft Graph Permissions

The lab application should have the required Microsoft Graph permissions.

For this lab, verify permissions such as:

```text
Domain.Read.All

User.ReadWrite.All
```

Also verify that required admin consent has been granted.

The application having a permission listed does not necessarily mean consent was granted.

---

# Gate 15 — Test Microsoft Authentication

Run:

```bash
python 01_verify_domains.py
```

Device authentication should occur.

Follow the browser instructions.

Use the correct Microsoft account.

---

# Common Problem — Student Authenticates to the Wrong Tenant

You may have:

```text
Personal Microsoft Account

School Microsoft Account

Lab Microsoft Account

Company Microsoft Account
```

Do not assume the browser chose the correct one.

The authentication may succeed while the script still cannot find your domains.

Why?

Because you successfully authenticated to the **wrong tenant**.

---

# Symptoms of Wrong Tenant

You may see:

```text
Authentication succeeded
```

but:

```text
balerica-ai.org : NOT FOUND
```

Possible cause:

```text
Wrong Microsoft tenant
```

Check:

```text
AZURE_TENANT_ID
```

and the user account used during device authentication.

---

# Gate 16 — Verify Domains in Microsoft Entra

Run:

```bash
python 01_verify_domains.py
```

Expected:

```text
balerica-ai.org : VERIFIED
```

If you see:

```text
NOT FOUND
```

the domain does not exist in the Microsoft tenant you authenticated against.

---

# If the Domain Is NOT FOUND

Check the Microsoft 365 Admin Center:

```text
Settings
    |
    v
Domains
```

Verify that the domain was actually added.

If the domain appears in GCP but not Microsoft:

```text
GCP DNS configuration exists
```

but:

```text
Microsoft domain configuration does not exist
```

These are separate systems.

---

# If the Domain Is NOT VERIFIED

Example:

```text
balerica-ai.org : NOT VERIFIED
```

Check:

```text
Microsoft verification TXT record
```

Then verify it publicly:

```bash
nslookup -type=TXT balerica-ai.org
```

If Microsoft expects:

```text
MS=ms12345678
```

but public DNS does not show it, fix DNS.

---

# Gate 17 — Compare Microsoft Verification with Public DNS

The expected path is:

```text
Microsoft Entra
      |
      | gives TXT challenge
      v
MS=msXXXXXXXX
      |
      v
Google Cloud DNS
      |
      v
Public DNS
      |
      v
Microsoft verifies ownership
```

Every layer must agree.

---

# Error — HTTP 401

Example:

```text
401 Unauthorized
```

This usually indicates an authentication problem.

Check:

```text
Tenant ID

Client ID

Device login

Token acquisition

App registration
```

---

# Error — HTTP 403

Example:

```text
403 Forbidden
```

This usually means:

```text
Authentication worked
```

but:

```text
Authorization failed
```

Check:

```text
Microsoft Graph permissions

Admin consent

User privileges

Tenant
```

---

# Error — HTTP 404

Example:

```text
404 Not Found
```

This can mean the object does not exist.

Examples:

```text
Wrong UPN

Wrong domain

Wrong tenant

User already deleted
```

---

# Gate 18 — Test User Creation

Run:

```bash
python 03_create_test_user.py
```

The script should attempt to create:

```text
seirverify@balerica-ai.org
```

---

# Error — Domain Is Not Verified

Microsoft may reject a UPN such as:

```text
seirverify@balerica-ai.org
```

if:

```text
balerica-ai.org
```

is not a verified domain.

Go back to:

```bash
python 01_verify_domains.py
```

Do not troubleshoot user creation until:

```text
VERIFIED
```

appears.

---

# Error — User Already Exists

You may receive an error indicating that:

```text
seirverify@balerica-ai.org
```

already exists.

Check:

```bash
python 04_verify_test_user.py
```

If the user exists from a previous lab, either:

```text
Use the existing test user
```

or:

```bash
python 05_cleanup_test_user.py
```

and recreate it.

---

# Error — Duplicate UPN

Microsoft Entra requires a unique UPN.

This cannot happen:

```text
User A
seirverify@balerica-ai.org
```

and:

```text
User B
seirverify@balerica-ai.org
```

at the same time.

Use a different username if necessary.

---

# Error — Invalid Password

Microsoft may reject a temporary password that does not satisfy the tenant password policy.

Use an instructor-approved strong temporary password.

Do not place the password inside the source code.

---

# Gate 19 — Verify User Creation

Run:

```bash
python 04_verify_test_user.py
```

Expected:

```text
USER VERIFICATION: PASS
```

If user creation reported success but verification fails, record:

```text
03_create_test_user.py output

04_verify_test_user.py output
```

and send both to the instructor.

---

# Gate 20 — Cleanup

Run:

```bash
python 05_cleanup_test_user.py
```

Expected:

```text
REMOVED:
seirverify@balerica-ai.org
```

---

# Troubleshooting Scenario 1

## Python Does Not Run

Symptoms:

```text
python: command not found
```

or:

```text
python is not recognized
```

Layer:

```text
LOCAL COMPUTER / PYTHON
```

Do not troubleshoot Azure.

Do not troubleshoot GCP.

Fix Python first.

---

# Troubleshooting Scenario 2

## GCP Authentication Fails

Symptoms:

```bash
gcloud auth list
```

shows no active user.

Layer:

```text
GCP AUTHENTICATION
```

Run:

```bash
gcloud auth login
```

---

# Troubleshooting Scenario 3

## Wrong GCP Project

Symptoms:

```bash
gcloud dns managed-zones list
```

does not show the expected zone.

Check:

```bash
gcloud config get-value project
```

You may simply be using the wrong project.

---

# Troubleshooting Scenario 4

## Cloud DNS Zone Exists but Public DNS Is Wrong

Symptoms:

```bash
gcloud dns managed-zones list
```

shows:

```text
balerica-ai.org
```

but:

```bash
nslookup -type=NS balerica-ai.org
```

shows another provider.

Cause:

```text
Registrar NS delegation was never changed.
```

The domain was not actually migrated to Google Cloud DNS.

---

# Troubleshooting Scenario 5

## TXT Record Exists in GCP but Microsoft Cannot See It

Symptoms:

Cloud DNS contains:

```text
MS=msXXXXXXXX
```

but:

```bash
nslookup -type=TXT balerica-ai.org
```

does not.

Possible causes:

```text
Wrong authoritative DNS provider

Wrong DNS zone

Wrong project

Incorrect record name

DNS propagation
```

---

# Troubleshooting Scenario 6

## Microsoft Authentication Works but Domain Is Missing

Symptoms:

```text
Device authentication succeeds
```

but:

```text
balerica-ai.org : NOT FOUND
```

Likely causes:

```text
Wrong Microsoft tenant

Domain was never added to Microsoft 365

Wrong AZURE_TENANT_ID
```

---

# Troubleshooting Scenario 7

## Domain Exists but Is Not Verified

Symptoms:

```text
balerica-ai.org : NOT VERIFIED
```

Check:

```bash
nslookup -type=TXT balerica-ai.org
```

Then compare the public TXT value to the Microsoft verification record.

---

# Troubleshooting Scenario 8

## Domain Is Verified but User Creation Fails

Check:

```text
Graph permissions

Admin consent

UPN uniqueness

Password policy

Correct tenant

Correct domain spelling
```

---

# Troubleshooting Scenario 9

## PowerShell Works but Python Fails

This is valuable diagnostic information.

If:

```text
PowerShell Graph commands: PASS

Python Graph scripts: FAIL
```

then the domain and Entra environment are probably fine.

Investigate:

```text
Python environment

Client ID

Tenant ID

App registration

Python authentication

Python packages
```

---

# Troubleshooting Scenario 10

## Python Works but gcloud Fails

This is also possible.

Remember:

```text
Microsoft Graph authentication
```

and:

```text
Google Cloud authentication
```

are separate.

You can successfully run:

```bash
python 01_verify_domains.py
```

while:

```bash
gcloud dns managed-zones list
```

fails.

That usually means:

```text
Microsoft authentication works

GCP authentication does not
```

---

# Troubleshooting Scenario 11

## DNS Python Script Works but gcloud Fails

This is completely possible.

Why?

Because:

```text
02_verify_dns.py
```

uses public DNS.

It does not require Google credentials.

Therefore:

```text
PUBLIC DNS QUERY: PASS

GCP LOGIN: FAIL
```

is a valid state.

---

# Master Diagnostic Flow

Follow this order:

```text
Can Python run?
      |
      v
Are packages installed?
      |
      v
Can gcloud authenticate?
      |
      v
Correct GCP project?
      |
      v
Does Cloud DNS zone exist?
      |
      v
Does public NS point to Cloud DNS?
      |
      v
Does public TXT contain Microsoft's record?
      |
      v
Can Python authenticate to Microsoft Graph?
      |
      v
Does Entra contain the domain?
      |
      v
IsVerified = True?
      |
      v
Can Entra create the user?
      |
      v
Can Python retrieve the user?
      |
      v
Cleanup
```

---

# Quick Diagnostic Commands

## Local Python

```bash
python --version
```

```bash
python -m pip list
```

---

## GCP Authentication

```bash
gcloud auth list
```

---

## GCP Project

```bash
gcloud config get-value project
```

---

## Cloud DNS Zones

```bash
gcloud dns managed-zones list
```

---

## Cloud DNS Records

```bash
gcloud dns record-sets list \
    --zone="YOUR_ZONE_NAME"
```

---

## Public DNS Name Servers

```bash
nslookup -type=NS yourdomain.com
```

---

## Public TXT Records

```bash
nslookup -type=TXT yourdomain.com
```

---

## Microsoft Domain Verification

```bash
python 01_verify_domains.py
```

---

## DNS Verification

```bash
python 02_verify_dns.py
```

---

## User Creation

```bash
python 03_create_test_user.py
```

---

## User Verification

```bash
python 04_verify_test_user.py
```

---

## Cleanup

```bash
python 05_cleanup_test_user.py
```

---

# What to Send the Instructor

If the lab still fails, send:

```text
Operating System:

Python Version:

Failed Script:

Exact Error:

GCP Active Account:
YES / NO

Correct GCP Project:
YES / NO

Cloud DNS Zone Exists:
YES / NO

Public NS Points to Google:
YES / NO

Microsoft TXT Visible Publicly:
YES / NO

Microsoft Authentication:
PASS / FAIL

Domain Found in Entra:
YES / NO

Domain Verified:
YES / NO

User Creation:
PASS / FAIL
```

---

# Do Not Send

Never send:

```text
Passwords

Access Tokens

Refresh Tokens

Client Secrets

Private Keys

MFA Codes
```

---

# Final Rule

Do not say:

```text
The script doesn't work.
```

Determine which statement is actually true:

```text
Python does not work.

The required module is missing.

I am not authenticated to GCP.

I am using the wrong GCP project.

The DNS zone does not exist.

The registrar is not delegated to Google Cloud DNS.

The TXT verification record is not public.

I authenticated to the wrong Microsoft tenant.

The domain was never added to Entra.

The domain is not verified.

My Graph application lacks permission.

The test user already exists.

The password violates policy.
```

Those are problems we can troubleshoot.

```text
"It doesn't work."
```

is not.
