# SEIR-1 — Python Domain Verification Playbook

## Purpose

This playbook explains the Python portion of the Microsoft Entra / Google Cloud DNS integration lab.

It is intended for students who:

- Were not present in class.
- Did not watch the class recording.
- Need to understand the purpose of each Python script.
- Need step-by-step instructions for running the scripts.
- Need to understand how the Python workflow compares with PowerShell.

The goal of this lab is to prove that:

```text
Google Cloud DNS
        |
        v
Hosts the custom domain
        |
        v
Microsoft Entra verifies ownership
        |
        v
Microsoft accepts the domain
        |
        v
Microsoft Entra can create users using that domain
```

Example:

```text
Google Cloud DNS

balerica-ai.org
       |
       v
Microsoft Entra ID

IsVerified = True
       |
       v
seirverify@balerica-ai.org
```

---

# What You Are Learning

You are not learning a completely different Azure environment by using Python.

PowerShell and Python are simply two different ways to interact with Microsoft services.

PowerShell:

```text
PowerShell
    |
    v
Microsoft Graph PowerShell Module
    |
    v
Microsoft Graph API
    |
    v
Microsoft Entra ID
```

Python:

```text
Python
    |
    v
Azure Identity + HTTP Requests
    |
    v
Microsoft Graph API
    |
    v
Microsoft Entra ID
```

Both workflows ultimately communicate with:

```text
Microsoft Graph
```

---

# PowerShell vs Python

The PowerShell lab used commands such as:

```powershell
Connect-MgGraph

Get-MgDomain

New-MgUser

Get-MgUser

Remove-MgUser
```

The Python scripts perform the same operations using API requests.

| Task | PowerShell | Python |
|---|---|---|
| Authenticate | `Connect-MgGraph` | `DeviceCodeCredential()` |
| List domains | `Get-MgDomain` | `GET /domains` |
| Check DNS | `nslookup` | `dns.resolver.resolve()` |
| Get verification DNS | `Get-MgDomainVerificationDnsRecord` | `GET /domains/{domain}/verificationDnsRecords` |
| Create user | `New-MgUser` | `POST /users` |
| Find user | `Get-MgUser` | `GET /users/{UPN}` |
| Delete user | `Remove-MgUser` | `DELETE /users/{UPN}` |

---

# Repository Structure

Your folder should contain files similar to:

```text
python-domain-lab/
|
+-- requirements.txt
|
+-- graph_auth.py
|
+-- 01_verify_domains.py
|
+-- 02_verify_dns.py
|
+-- 03_create_test_user.py
|
+-- 04_verify_test_user.py
|
+-- 05_cleanup_test_user.py
```

Each script performs one specific task.

Do not run them randomly.

Run them in numerical order.

---

# Step 1 — Open a Terminal

## Windows

Open:

```text
PowerShell
```

or:

```text
Windows Terminal
```

## macOS

Open:

```text
Terminal
```

## Linux

Open your normal terminal application.

---

# Step 2 — Navigate to the Repository

Use `cd` to enter the folder containing the lab.

Example:

```bash
cd ~/Documents/python-domain-lab
```

Windows example:

```powershell
cd $HOME\Documents\python-domain-lab
```

Verify the files exist.

macOS/Linux:

```bash
ls
```

Windows PowerShell:

```powershell
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

---

# Step 3 — Verify Python

Run:

```bash
python --version
```

If that fails:

```bash
python3 --version
```

You should see something similar to:

```text
Python 3.12.x
```

Use whichever command works on your computer.

For the remainder of this playbook, examples will use:

```bash
python
```

If your computer requires `python3`, substitute it.

---

# Step 4 — Install the Required Python Packages

The lab uses:

```text
azure-identity

requests

dnspython
```

Install them:

```bash
python -m pip install -r requirements.txt
```

If you do not have a `requirements.txt` file:

```bash
python -m pip install azure-identity requests dnspython
```

---

# Step 5 — Understand the Authentication Requirement

Python needs permission to access Microsoft Graph.

The Python application should already have been registered in Microsoft Entra ID.

You need two values:

```text
Tenant ID

Application / Client ID
```

These identify:

```text
Which Microsoft tenant?

Which application is requesting access?
```

---

# Step 6 — Configure Environment Variables

Do not hard-code these values into your Python scripts.

## Windows PowerShell

```powershell
$env:AZURE_TENANT_ID="<your-tenant-id>"

$env:AZURE_CLIENT_ID="<your-client-id>"
```

Verify:

```powershell
$env:AZURE_TENANT_ID

$env:AZURE_CLIENT_ID
```

---

## macOS / Linux

```bash
export AZURE_TENANT_ID="<your-tenant-id>"

export AZURE_CLIENT_ID="<your-client-id>"
```

Verify:

```bash
echo $AZURE_TENANT_ID

echo $AZURE_CLIENT_ID
```

---

# Step 7 — Understand graph_auth.py

Do not run this file by itself unless instructed.

`graph_auth.py` is a helper module.

The other scripts import it.

Conceptually:

```text
01_verify_domains.py
        |
        v
graph_auth.py
        |
        v
Microsoft Authentication
        |
        v
Access Token
```

The important code is:

```python
credential = DeviceCodeCredential(
    tenant_id=tenant_id,
    client_id=client_id
)
```

Then:

```python
token = credential.get_token(
    "https://graph.microsoft.com/.default"
)
```

This is the Python equivalent of:

```powershell
Connect-MgGraph
```

---

# Authentication Flow

When authentication occurs, you may see instructions similar to:

```text
To sign in, use a web browser to open...

Enter code:
XXXXXXXX
```

Follow the instructions.

Sign in using the Microsoft account associated with the lab tenant.

Do not authenticate using a random personal Microsoft account.

---

# Script 1 — Verify Microsoft Entra Domains

Run:

```bash
python 01_verify_domains.py
```

The script asks Microsoft Graph:

```text
Which domains exist in this Microsoft Entra tenant?
```

The API request is conceptually:

```text
GET

https://graph.microsoft.com/v1.0/domains
```

PowerShell equivalent:

```powershell
Get-MgDomain
```

---

# Expected Output

You should see something similar to:

```text
balerica-ai.org           VERIFIED        Managed

balerica-ai.cloud         VERIFIED        Managed

chewygrows.net            VERIFIED        Managed
```

The most important result is:

```text
VERIFIED
```

This means Microsoft Entra accepts Microsoft's proof that the organization controls the domain.

---

# What Does Managed Mean?

You may see:

```text
Managed
```

This refers to the current authentication configuration.

At this stage, Microsoft Entra is still handling authentication normally.

We have not configured SAML federation yet.

Therefore:

```text
Managed
```

is expected.

---

# Stop If the Domain Is Not Verified

If you see:

```text
NOT VERIFIED
```

do not continue to user creation.

The domain must first be successfully verified.

Troubleshoot the DNS verification process.

---

# Script 2 — Verify Public DNS

Run:

```bash
python 02_verify_dns.py
```

This script asks public DNS for:

```text
NS records

TXT records
```

---

# Why Check DNS?

Seeing a DNS zone inside Google Cloud does not automatically prove that the public Internet is actually using that zone.

We want to prove:

```text
Domain Registrar
       |
       v
NS Delegation
       |
       v
Google Cloud DNS
       |
       v
TXT Verification Record
```

---

# NS Records

NS means:

```text
Name Server
```

These records indicate which DNS servers are authoritative for the domain.

The script uses:

```python
dns.resolver.resolve(
    domain,
    "NS"
)
```

PowerShell equivalent:

```powershell
nslookup -type=NS balerica-ai.org
```

---

# TXT Records

The script also requests TXT records:

```python
dns.resolver.resolve(
    domain,
    "TXT"
)
```

PowerShell equivalent:

```powershell
nslookup -type=TXT balerica-ai.org
```

TXT records are commonly used for:

```text
Domain ownership verification

SPF

Other service verification
```

---

# Script 3 — Create a Test User

Run:

```bash
python 03_create_test_user.py
```

This is the most important test in the lab.

The script attempts to create:

```text
seirverify@balerica-ai.org
```

inside Microsoft Entra ID.

---

# Why Is This Important?

Seeing:

```text
IsVerified = True
```

is useful.

Actually creating:

```text
seirverify@balerica-ai.org
```

is stronger proof.

It proves that Microsoft Entra accepts:

```text
balerica-ai.org
```

as a valid UPN suffix.

---

# What Is a UPN?

UPN means:

```text
User Principal Name
```

Example:

```text
chewbacca@balerica-ai.org
```

The UPN is commonly used as a user's Microsoft sign-in identity.

---

# Enter the Temporary Password

The script will ask:

```text
Enter temporary password:
```

Type the temporary password.

The characters may not appear on screen.

That is intentional.

The script uses:

```python
getpass.getpass()
```

instead of:

```python
password = "MyPassword123"
```

This prevents the password from being stored directly in the source code.

---

# Do Not Put Passwords in GitHub

Never write:

```python
password = "SuperSecretPassword123!"
```

inside code that will be committed to GitHub.

Never submit:

```text
Passwords

Tokens

Client secrets

Private keys

MFA codes
```

into the class chat.

---

# What the Script Sends to Microsoft Graph

The Python script sends an HTTP request similar to:

```text
POST

https://graph.microsoft.com/v1.0/users
```

The request contains user information such as:

```text
Display Name

User Principal Name

Mail Nickname

Password Profile

Account Enabled
```

PowerShell hides this API operation behind:

```powershell
New-MgUser
```

Python exposes the operation more directly.

---

# Successful User Creation

You should see:

```text
USER CREATION: PASS
```

followed by information such as:

```text
Display Name:
SEIR Domain Verification

UPN:
seirverify@balerica-ai.org

Object ID:
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

# What Is the Object ID?

The Object ID is the unique identifier Microsoft Entra assigns to the identity.

Example:

```text
Display Name:
Chewbacca

UPN:
chewbacca@balerica-ai.org

Object ID:
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Names can change.

UPNs can change.

The Object ID identifies the actual directory object.

---

# Script 4 — Verify the User

Run:

```bash
python 04_verify_test_user.py
```

This script asks Microsoft:

```text
Does this user actually exist?
```

The API request is conceptually:

```text
GET

https://graph.microsoft.com/v1.0/users/seirverify@balerica-ai.org
```

PowerShell equivalent:

```powershell
Get-MgUser `
    -UserId "seirverify@balerica-ai.org"
```

---

# Why Verify?

Never assume a change succeeded simply because a command did not display an obvious error.

Good automation follows this model:

```text
CREATE
   |
   v
QUERY
   |
   v
VERIFY
```

The script should return:

```text
USER VERIFICATION: PASS
```

and information similar to:

```text
Display Name:
SEIR Domain Verification

UPN:
seirverify@balerica-ai.org

Account Enabled:
True
```

---

# Script 5 — Clean Up

Run:

```bash
python 05_cleanup_test_user.py
```

The script deletes:

```text
seirverify@balerica-ai.org
```

The API request is:

```text
DELETE

https://graph.microsoft.com/v1.0/users/seirverify@balerica-ai.org
```

PowerShell equivalent:

```powershell
Remove-MgUser `
    -UserId "seirverify@balerica-ai.org"
```

---

# Why Cleanup Matters

Cloud engineers should not leave unnecessary test resources behind.

That includes:

```text
Test users

Test groups

Virtual machines

Storage

Role assignments

Temporary credentials

Networking resources
```

A professional workflow should include cleanup.

---

# Complete Execution Order

Run the lab in this order:

```text
STEP 1
Verify Python
      |
      v
STEP 2
Install Packages
      |
      v
STEP 3
Configure Tenant ID and Client ID
      |
      v
STEP 4
Verify Entra Domains
      |
      v
STEP 5
Verify Public DNS
      |
      v
STEP 6
Create Test User
      |
      v
STEP 7
Verify Test User
      |
      v
STEP 8
Delete Test User
```

Commands:

```bash
python 01_verify_domains.py
```

then:

```bash
python 02_verify_dns.py
```

then:

```bash
python 03_create_test_user.py
```

then:

```bash
python 04_verify_test_user.py
```

then:

```bash
python 05_cleanup_test_user.py
```

---

# The Entire Architecture

You should understand this flow:

```text
Domain Registrar
       |
       v
Google Cloud DNS
       |
       | Authoritative DNS
       v
balerica-ai.org
       |
       | TXT Verification
       v
Microsoft Entra ID
       |
       | IsVerified = True
       v
Microsoft Graph API
       |
       | POST /users
       v
seirverify@balerica-ai.org
```

---

# What Python Is Actually Teaching You

PowerShell gives you:

```powershell
New-MgUser
```

Python teaches you that behind that command is fundamentally something similar to:

```text
HTTP POST
        |
        v
Microsoft Graph API
        |
        v
/users
```

This matters professionally.

If one interface stops working, you should understand that there may be another way to interact with the platform.

For example:

```text
PowerShell Module
      |
      X
    Problem
```

You may still have:

```text
Python
   |
   v
REST API
```

or:

```text
Azure CLI
```

or another supported SDK.

---

# Common Error — Missing Python Package

Example:

```text
ModuleNotFoundError
```

Install the requirements:

```bash
python -m pip install -r requirements.txt
```

---

# Common Error — AZURE_TENANT_ID Is Missing

You may see:

```text
AZURE_TENANT_ID environment variable is not set
```

Set it.

Windows:

```powershell
$env:AZURE_TENANT_ID="<tenant-id>"
```

macOS/Linux:

```bash
export AZURE_TENANT_ID="<tenant-id>"
```

---

# Common Error — AZURE_CLIENT_ID Is Missing

Set the Application Client ID.

Windows:

```powershell
$env:AZURE_CLIENT_ID="<client-id>"
```

macOS/Linux:

```bash
export AZURE_CLIENT_ID="<client-id>"
```

---

# Common Error — Authentication Fails

Verify:

```text
Correct tenant

Correct application/client ID

Correct Microsoft user

Required Microsoft Graph permissions

Admin consent
```

Record the exact error message.

Do not report:

```text
Python doesn't work.
```

---

# Common Error — 403 Forbidden

A `403` usually means:

```text
Authentication succeeded
```

but:

```text
Authorization failed
```

In other words:

```text
Microsoft knows who you are.

Microsoft does not believe you are allowed to perform the operation.
```

Check:

```text
Graph permissions

Admin consent

User role

Tenant
```

---

# Common Error — 401 Unauthorized

A `401` usually indicates an authentication or token problem.

Investigate:

```text
Tenant ID

Client ID

Authentication process

Access token
```

---

# Common Error — Domain Not Verified

If:

```text
balerica-ai.org
```

shows:

```text
NOT VERIFIED
```

do not try to solve this by repeatedly running the user creation script.

The problem is earlier in the chain:

```text
DNS
   |
   v
Domain Verification
```

Fix the first failed gate.

---

# Troubleshooting Model

Use this:

```text
Python
   |
   v
Python Packages
   |
   v
Application Registration
   |
   v
Authentication
   |
   v
Microsoft Graph
   |
   v
Domain Verification
   |
   v
User Creation
```

Do not troubleshoot user creation if authentication is failing.

Do not troubleshoot authentication if Python itself does not run.

Always troubleshoot the first failed layer.

---

# Submission

Submit the following:

```text
Domain Verification:
PASS / FAIL

DNS Verification:
PASS / FAIL

User Creation:
PASS / FAIL

User Verification:
PASS / FAIL

Cleanup:
PASS / FAIL
```

Example:

```text
SEIR PYTHON DOMAIN LAB

Domain Verification: PASS

DNS Verification: PASS

User Creation: PASS

User Verification: PASS

Cleanup: PASS
```

---

# Do Not Submit

Do not submit:

```text
Passwords

Access tokens

Refresh tokens

Client secrets

Private keys

Authentication codes
```

---

# Success Criteria

You have completed the lab when:

- [ ] Python runs locally.
- [ ] Required packages are installed.
- [ ] `AZURE_TENANT_ID` is configured.
- [ ] `AZURE_CLIENT_ID` is configured.
- [ ] Microsoft authentication succeeds.
- [ ] The custom domain appears in Microsoft Graph.
- [ ] The custom domain reports `VERIFIED`.
- [ ] Public DNS successfully resolves.
- [ ] Google Cloud DNS remains authoritative.
- [ ] Python successfully creates a Microsoft Entra user using the custom domain.
- [ ] Python successfully retrieves the new user.
- [ ] The test user is removed after verification.
- [ ] You understand the PowerShell equivalent of each operation.

---

# Final Concept

Do not memorize only this:

```python
requests.post(...)
```

Understand the system:

```text
Python
   |
   v
Authentication
   |
   v
Access Token
   |
   v
Microsoft Graph
   |
   v
Microsoft Entra ID
```

The same platform can be controlled by:

```text
PowerShell

Python

CLI

SDKs

REST APIs
```

The syntax changes.

The identity system and control plane do not.

---

# Next Lab

The next phase will move beyond proving that the domain works.

We will begin connecting the identity systems:

```text
Microsoft Entra ID
       |
       | Provisioning
       v
Google Workspace / Cloud Identity
```

The goal will be to synchronize existing identities without unnecessarily creating duplicate Google accounts.

Example:

```text
Microsoft:

chewbacca@balerica-ai.org

        |
        v

Google:

chewbacca@balerica-ai.org
```

The desired result is:

```text
ONE USER
TWO PLATFORMS
MATCHING IDENTITY
```

Not:

```text
Chewbacca

Chewbacca-2

Chewbacca-Final

Chewbacca-Final-Final

Chewbacca-Revenge-of-SCIM
```

If you reach that state, stop creating users and contact the instructor.
