# SEIR-1 — Verify GCP-Hosted Domains in Microsoft Entra ID

## Objective

In this lab, you will verify that a domain whose DNS is hosted in **Google Cloud DNS** has been successfully verified by **Microsoft Entra ID**.

You will then prove that Microsoft Entra ID can use that domain when creating user accounts.

The important architecture is:

```text
Google Cloud DNS
       |
       | Hosts authoritative DNS
       v
studentdomain.com
       |
       | Domain ownership verified
       v
Microsoft Entra ID
       |
       | Domain available as UPN suffix
       v
user@studentdomain.com
```

---

# Important Terminology

Google Cloud is **not creating Microsoft users**.

Google Cloud DNS is hosting the DNS records that prove ownership of the domain.

Microsoft Entra ID then recognizes that domain as verified and allows it to be used for user identities.

For example:

```text
GCP Cloud DNS

balerica-ai.org
       |
       | TXT verification
       v
Microsoft Entra ID

balerica-ai.org
IsVerified = True
       |
       v
chewbacca@balerica-ai.org
```

---

# Lab Domains

The example environment contains:

```text
balerica-ai.org

balerica-ai.cloud

chewygrows.net
```

Your environment may use different domains.

---

# Gate 1 — Connect to Microsoft Graph

Start PowerShell.

Connect to Microsoft Graph:

```powershell
Connect-MgGraph -Scopes `
    "Domain.Read.All", `
    "User.ReadWrite.All"
```

Verify the Microsoft Graph session:

```powershell
Get-MgContext
```

Review:

```text
Account

TenantId

Scopes
```

Make sure you are connected to the correct Microsoft Entra tenant.

---

# Gate 2 — Define the GCP-Hosted Domains

Create an array containing the domains used for this lab:

```powershell
$GcpDomains = @(
    "balerica-ai.org",
    "balerica-ai.cloud",
    "chewygrows.net"
)
```

Verify the variable:

```powershell
$GcpDomains
```

Expected output:

```text
balerica-ai.org
balerica-ai.cloud
chewygrows.net
```

---

# Gate 3 — View All Microsoft Entra Domains

Run:

```powershell
Get-MgDomain |
    Select-Object `
        Id,
        IsVerified,
        IsDefault,
        AuthenticationType
```

Look for your custom domains.

Example:

```text
Id                    IsVerified   IsDefault   AuthenticationType
--                    ----------   ---------   ------------------
balerica-ai.org       True         False       Managed
balerica-ai.cloud     True         False       Managed
chewygrows.net        True         False       Managed
```

The most important value at this stage is:

```text
IsVerified = True
```

---

# Understanding AuthenticationType

At this stage, the domains will normally still show:

```text
Managed
```

This means Microsoft Entra ID is currently responsible for authentication.

We have **not configured federation yet**.

Later, SSO configuration may change the authentication architecture.

For this lab, the important state is:

```text
Domain Exists

+

IsVerified = True
```

---

# Gate 4 — Verify Only the GCP Domains

Instead of looking through every Microsoft domain, check only the domains used in this lab.

Run:

```powershell
foreach ($Domain in $GcpDomains) {

    $DomainInfo = Get-MgDomain -DomainId $Domain

    [PSCustomObject]@{
        Domain             = $DomainInfo.Id
        Verified           = $DomainInfo.IsVerified
        Default            = $DomainInfo.IsDefault
        AuthenticationType = $DomainInfo.AuthenticationType
    }
}
```

Expected result:

```text
Domain               Verified   Default   AuthenticationType
------               --------   -------   ------------------
balerica-ai.org      True       False     Managed
balerica-ai.cloud    True       False     Managed
chewygrows.net       True       False     Managed
```

---

# Gate 5 — Create a PASS / FAIL Domain Test

We can make the verification easier to read.

Run:

```powershell
foreach ($Domain in $GcpDomains) {

    $DomainInfo = Get-MgDomain -DomainId $Domain

    if ($DomainInfo.IsVerified) {

        Write-Host "$Domain : VERIFIED"

    }
    else {

        Write-Host "$Domain : NOT VERIFIED"

    }
}
```

Expected:

```text
balerica-ai.org : VERIFIED
balerica-ai.cloud : VERIFIED
chewygrows.net : VERIFIED
```

If a domain reports:

```text
NOT VERIFIED
```

do not attempt to create users with that domain yet.

---

# Gate 6 — Verify Public DNS

A DNS zone existing inside Google Cloud does not automatically prove that the public Internet is using that zone.

Check the authoritative name servers.

Example:

```powershell
nslookup -type=NS balerica-ai.org
```

Then check the TXT records:

```powershell
nslookup -type=TXT balerica-ai.org
```

Repeat for the other domains:

```powershell
nslookup -type=NS balerica-ai.cloud
nslookup -type=TXT balerica-ai.cloud
```

```powershell
nslookup -type=NS chewygrows.net
nslookup -type=TXT chewygrows.net
```

The architecture being tested is:

```text
Internet
   |
   v
Domain Registrar
   |
   | NS Delegation
   v
Google Cloud DNS
   |
   | TXT Record
   v
Microsoft Domain Verification
```

---

# Gate 7 — Select a Domain for User Testing

Select one verified domain.

Example:

```powershell
$Domain = "balerica-ai.org"
```

Verify it:

```powershell
$Domain
```

Then verify that Microsoft considers it valid:

```powershell
(Get-MgDomain -DomainId $Domain).IsVerified
```

Expected:

```text
True
```

---

# Gate 8 — Create a Test UPN

We will create a temporary Microsoft Entra user.

Define the User Principal Name:

```powershell
$TestUPN = "seirverify@$Domain"
```

Verify:

```powershell
$TestUPN
```

Expected:

```text
seirverify@balerica-ai.org
```

---

# Gate 9 — Create a Temporary Password Profile

Create a password profile for the test account.

Replace the example password with an instructor-approved temporary password.

```powershell
$PasswordProfile = @{
    Password = "<STRONG-TEMPORARY-PASSWORD>"
    ForceChangePasswordNextSignIn = $true
}
```

Do not paste passwords into class chat.

---

# Gate 10 — Create the Microsoft Entra User

Run:

```powershell
$TestUser = New-MgUser `
    -DisplayName "SEIR Domain Verification" `
    -UserPrincipalName $TestUPN `
    -MailNickname "seirverify" `
    -AccountEnabled:$true `
    -PasswordProfile $PasswordProfile
```

The returned Microsoft Entra user object is stored in:

```powershell
$TestUser
```

---

# Gate 11 — Inspect the Created User

Run:

```powershell
$TestUser |
    Select-Object `
        DisplayName,
        UserPrincipalName,
        Id
```

Expected:

```text
DisplayName          SEIR Domain Verification

UserPrincipalName    seirverify@balerica-ai.org

Id                   <Microsoft Entra Object ID>
```

---

# Gate 12 — Query Microsoft Entra Directly

Do not assume that the user exists simply because the creation command did not display an error.

Ask Microsoft Entra directly.

Run:

```powershell
Get-MgUser `
    -UserId $TestUPN |
    Select-Object `
        DisplayName,
        UserPrincipalName,
        Id,
        AccountEnabled
```

Expected:

```text
DisplayName       : SEIR Domain Verification

UserPrincipalName : seirverify@balerica-ai.org

AccountEnabled    : True
```

---

# What Did We Just Prove?

Successful user creation proves this chain:

```text
Google Cloud DNS
       |
       v
balerica-ai.org
       |
       v
Microsoft verifies domain ownership
       |
       v
IsVerified = True
       |
       v
Microsoft accepts the domain as a UPN suffix
       |
       v
seirverify@balerica-ai.org
       |
       v
Microsoft Entra User Created
```

---

# Gate 13 — Test All Three Domains

You can optionally prove that all three domains are available to Microsoft Entra.

First verify them:

```powershell
foreach ($Domain in $GcpDomains) {

    $DomainInfo = Get-MgDomain -DomainId $Domain

    if ($DomainInfo.IsVerified) {

        Write-Host "$Domain : READY FOR USER CREATION"

    }
    else {

        Write-Host "$Domain : NOT READY"

    }
}
```

Expected:

```text
balerica-ai.org : READY FOR USER CREATION

balerica-ai.cloud : READY FOR USER CREATION

chewygrows.net : READY FOR USER CREATION
```

---

# Optional Challenge — Create One Test User Per Domain

This should only be performed in the lab environment.

```powershell
foreach ($Domain in $GcpDomains) {

    $Alias = "seirtest"

    $UPN = "$Alias@$Domain"

    Write-Host "Creating $UPN"

    $PasswordProfile = @{
        Password = "<STRONG-TEMPORARY-PASSWORD>"
        ForceChangePasswordNextSignIn = $true
    }

    New-MgUser `
        -DisplayName "SEIR Test $Domain" `
        -UserPrincipalName $UPN `
        -MailNickname $Alias `
        -AccountEnabled:$true `
        -PasswordProfile $PasswordProfile
}
```

---

# Gate 14 — Verify All Test Users

Run:

```powershell
Get-MgUser -All |
    Where-Object {
        $_.UserPrincipalName -like "seirtest@*"
    } |
    Select-Object `
        DisplayName,
        UserPrincipalName,
        Id
```

Expected:

```text
SEIR Test balerica-ai.org
seirtest@balerica-ai.org

SEIR Test balerica-ai.cloud
seirtest@balerica-ai.cloud

SEIR Test chewygrows.net
seirtest@chewygrows.net
```

This proves that Microsoft Entra accepts all three custom domains for user identities.

---

# Final Verification Script

Run:

```powershell
Write-Host "======================================"
Write-Host "SEIR DOMAIN VERIFICATION"
Write-Host "======================================"

Write-Host "`nDOMAIN STATUS"

foreach ($Domain in $GcpDomains) {

    $DomainInfo = Get-MgDomain -DomainId $Domain

    [PSCustomObject]@{
        Domain             = $DomainInfo.Id
        Verified           = $DomainInfo.IsVerified
        AuthenticationType = $DomainInfo.AuthenticationType
    }
}

Write-Host "`nTEST USER"

Get-MgUser `
    -UserId $TestUPN |
    Select-Object `
        DisplayName,
        UserPrincipalName,
        AccountEnabled,
        Id

Write-Host "`n=== VERIFICATION COMPLETE ==="
```

---

# Expected Final State

The environment should now look like:

```text
                         Google Cloud
                              |
                              v
                         Cloud DNS
                              |
               +--------------+--------------+
               |              |              |
               v              v              v

       balerica-ai.org  balerica-ai.cloud  chewygrows.net

               |              |              |
               +--------------+--------------+
                              |
                              v
                     Microsoft Entra ID
                              |
                    All Domains Verified
                              |
                              v
                      User Creation Works
```

---

# Cleanup

The accounts created during verification are temporary.

## Remove the Single Test User

```powershell
Remove-MgUser `
    -UserId "seirverify@balerica-ai.org"
```

---

# Remove Test Users from All Domains

If you created the `seirtest` accounts:

```powershell
Get-MgUser -All |
    Where-Object {
        $_.UserPrincipalName -like "seirtest@*"
    } |
    ForEach-Object {

        Write-Host "Removing $($_.UserPrincipalName)"

        Remove-MgUser `
            -UserId $_.Id
    }
```

---

# Verify Cleanup

Run:

```powershell
Get-MgUser -All |
    Where-Object {
        $_.UserPrincipalName -like "seirtest@*"
    }
```

No results should be returned.

---

# Success Criteria

You have completed this lab when:

- [ ] You successfully connected to Microsoft Graph.
- [ ] Your GCP-hosted custom domain appears in Microsoft Entra.
- [ ] `IsVerified` equals `True`.
- [ ] Public DNS resolves the domain.
- [ ] Google Cloud DNS remains authoritative for the domain.
- [ ] Microsoft Entra accepts the domain as a UPN suffix.
- [ ] You successfully created a test user using the custom domain.
- [ ] `Get-MgUser` independently verified the user.
- [ ] You understand that Google Cloud DNS is not creating the Microsoft account.
- [ ] Temporary test users were removed after verification.

---

# Important Distinction

This:

```text
balerica-ai.org exists in Google Cloud DNS
```

does **not automatically mean**:

```text
Microsoft Entra may use balerica-ai.org
```

The complete process is:

```text
Domain Registered
       |
       v
DNS Delegated to Google Cloud DNS
       |
       v
Microsoft Verification Record Added
       |
       v
Microsoft Verifies Domain
       |
       v
IsVerified = True
       |
       v
Domain Can Be Used in Microsoft Entra UPNs
```

---

# Key Concept

The strongest proof that domain integration is working is not simply seeing:

```text
Verified
```

in the Azure portal.

The stronger test is:

```text
DNS resolves correctly
        +
Microsoft reports IsVerified = True
        +
Microsoft successfully creates:

user@custom-domain
```

Together, those prove that the custom-domain side of the Microsoft Entra environment is operational.

---

# Next Lab

The next phase changes the architecture from:

```text
Google Account

and

Microsoft Account
```

into:

```text
Microsoft Entra ID
       |
       | Provisioning
       v
Google Workspace / Cloud Identity
```

The next challenge will be determining whether Microsoft Entra correctly matches an existing local Google identity rather than creating a duplicate account.

In other words:

```text
Chewbacca
     |
     v
Existing Google Identity
```

must remain:

```text
Chewbacca
```

and not become:

```text
Chewbacca

Chewbacca-2

Chewbacca-Revenge-of-SCIM
```

That will be the next problem.
