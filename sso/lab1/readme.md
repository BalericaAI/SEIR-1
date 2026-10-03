# SEIR-1 — Lab 1: Prepare Google and Microsoft Entra Identities

## Objective

In this lab, you will prepare an existing Google domain and Google identity for future synchronization with Microsoft Entra ID.

You will **not configure SSO yet**.

You will **not move email yet**.

You will:

1. Identify your existing Google domain.
2. Verify that your Google user exists.
3. Add the same custom domain to Microsoft 365 / Microsoft Entra ID.
4. Verify ownership of the domain using DNS.
5. Confirm that email still points to Google.
6. Verify the domain from Microsoft Graph PowerShell.
7. Align your Microsoft Entra User Principal Name with your Google identity.
8. Create a small pilot synchronization group.
9. Verify that both Google and Microsoft use the same user identity.

---

# Architecture

At the beginning of the lab, your environment may look similar to this:

```text
Google Workspace / Cloud Identity

studentdomain.com
        |
        +---- chewbacca@studentdomain.com


Microsoft Entra ID

yourtenant.onmicrosoft.com
        |
        +---- chewbacca@yourtenant.onmicrosoft.com
```

Our goal is to reach:

```text
               studentdomain.com
                      |
          +-----------+-----------+
          |                       |
          v                       v

Google Workspace             Microsoft Entra ID

chewbacca@                   chewbacca@
studentdomain.com            studentdomain.com
```

The identities should match:

```text
Google Primary Email
        =
Microsoft Entra UPN
```

---

# Important — What We Are NOT Doing Today

This lab prepares the environment.

It does **not** enable synchronization.

It does **not** enable SSO.

It does **not** move Gmail to Exchange Online.

At the end of this lab:

```text
Microsoft Domain Verified:     YES

Matching Entra User:           YES

Matching Google User:          YES

Pilot Group Created:           YES

Automatic Provisioning:        NO

SAML SSO:                      NO

Workforce Federation:          NO

MX Record Changed:             NO

Google Mail Migrated:          NO
```

---

# WARNING — DO NOT CHANGE YOUR MX RECORD

## Seriously.

Do not change your MX record during this lab.

Your current mail flow may look like this:

```text
Internet
    |
    v
studentdomain.com
    |
    v
Google MX Records
    |
    v
Gmail
```

We want it to remain that way.

Today we are only proving that Microsoft also recognizes that you own:

```text
studentdomain.com
```

Domain verification does **not** require moving email.

---

# Prerequisites

Before beginning, you should have:

- A Google Workspace or Cloud Identity domain
- Administrative access to that Google environment
- Access to your domain's DNS records
- A Microsoft 365 / Microsoft Entra tenant
- Administrative access to Microsoft Entra ID
- PowerShell 7
- Microsoft Graph PowerShell installed
- An existing Google user account for testing

This lab will use:

```text
Chewbacca
```

as the example user.

Your instructor may require you to substitute your own user information.

---

# Gate 1 — Identify Your Google Domain

Log in to the Google Admin environment.

Identify your primary domain.

Example:

```text
studentdomain.com
```

Record it.

For the remainder of this lab, we will use:

```text
studentdomain.com
```

as the example.

Replace this value with your own domain.

---

# Gate 2 — Verify the Existing Google User

Verify that your test user already exists in Google Workspace or Cloud Identity.

Example:

```text
Display Name:
Chewbacca

Primary Email:
chewbacca@studentdomain.com
```

## Record the exact primary email address

For example:

```text
chewbacca@studentdomain.com
```

Spelling matters.

The identity created in Microsoft Entra ID should eventually match this value.

---

# Why Matching Matters

Our future provisioning architecture will look like this:

```text
Microsoft Entra ID
       |
       | Provisioning
       v
Google Workspace / Cloud Identity
```

We do not want this:

```text
Google:
chewbacca@studentdomain.com

Microsoft:
chewbacca@someotherdomain.com
```

We want:

```text
Google:
chewbacca@studentdomain.com

Microsoft:
chewbacca@studentdomain.com
```

This makes identity matching much easier when synchronization is enabled.

---

# Gate 3 — Add the Domain to Microsoft 365

Open the Microsoft 365 Admin Center.

Navigate to:

```text
Microsoft 365 Admin Center
        |
        v
Settings
        |
        v
Domains
        |
        v
Add Domain
```

Enter your Google domain.

Example:

```text
studentdomain.com
```

Continue until Microsoft asks you to verify ownership.

---

# Gate 4 — Obtain the Microsoft DNS Verification Record

Microsoft should provide a DNS verification record.

The preferred method for this lab is a **TXT record**.

It will look conceptually similar to:

```text
Type: TXT

Host:
@

Value:
MS=msXXXXXXXX
```

Your actual value will be different.

## Important

Use the value Microsoft gives **your tenant**.

Do not copy an example value from this README.

---

# Gate 5 — Add the TXT Record to DNS

Open the DNS management system for your domain.

This could be managed by:

- Google
- Cloudflare
- GoDaddy
- Namecheap
- Route 53
- Another DNS provider

Add the TXT record Microsoft provided.

Example:

```text
Type: TXT

Name:
@

Value:
MS=msXXXXXXXX
```

Save the record.

---

# Gate 6 — Verify the Domain

Return to Microsoft 365.

Select:

```text
Verify
```

Microsoft will attempt to locate the TXT record.

When successful, Microsoft should recognize:

```text
studentdomain.com
```

as a verified domain.

---

# STOP — Do Not Configure Microsoft DNS Services Yet

Microsoft may offer to configure additional DNS records.

You may see references to:

```text
MX

Autodiscover

SPF

Exchange Online

Teams

Microsoft 365
```

Do **not** change your mail routing during this lab.

Your Google mail configuration should remain intact.

---

# Gate 7 — Verify That Google Mail Still Works

Before continuing, verify that Gmail still operates normally.

Send a test email to:

```text
chewbacca@studentdomain.com
```

Confirm that the message arrives in the existing Google mailbox.

You should still have:

```text
Internet
    |
    v
Google Mail
```

not:

```text
Internet
    |
    v
Exchange Online
```

Exchange migration will occur in a later lab.

---

# Gate 8 — Start PowerShell

Open PowerShell.

Verify the version:

```powershell
$PSVersionTable
```

You should be running a modern PowerShell environment.

---

# Gate 9 — Verify Microsoft Graph PowerShell

Check whether Microsoft Graph PowerShell is installed:

```powershell
Get-Module Microsoft.Graph* -ListAvailable
```

If necessary:

```powershell
Install-Module Microsoft.Graph -Scope CurrentUser
```

---

# Gate 10 — Connect to Microsoft Graph

Connect with the permissions required for this lab:

```powershell
Connect-MgGraph -Scopes `
    "Domain.Read.All", `
    "User.ReadWrite.All", `
    "Group.ReadWrite.All"
```

Verify the connection:

```powershell
Get-MgContext
```

Look for:

```text
Account

TenantId

Scopes
```

---

# Gate 11 — Verify the Custom Domain with PowerShell

Run:

```powershell
Get-MgDomain |
    Select-Object Id, IsVerified, IsDefault
```

Locate your custom domain.

Example:

```text
Id                     IsVerified   IsDefault
--                     ----------   ---------
studentdomain.com       True         False
```

The important value is:

```text
IsVerified = True
```

---

# Optional — Store the Domain in a Variable

Instead of repeatedly typing your domain:

```powershell
$Domain = "studentdomain.com"
```

Verify:

```powershell
$Domain
```

Expected:

```text
studentdomain.com
```

---

# Gate 12 — Locate the Existing Entra User

Locate Chewbacca.

```powershell
$Chewbacca = Get-MgUser `
    -Filter "displayName eq 'Chewbacca'"
```

Display the result:

```powershell
$Chewbacca |
    Select-Object `
        DisplayName,
        UserPrincipalName,
        Id
```

You may currently see:

```text
DisplayName        Chewbacca

UserPrincipalName  chewbacca@yourtenant.onmicrosoft.com
```

That is okay.

We are going to align the UPN with Google.

---

# Gate 13 — Compare Google and Microsoft Identities

Your Google identity may currently be:

```text
chewbacca@studentdomain.com
```

while your Microsoft identity may be:

```text
chewbacca@yourtenant.onmicrosoft.com
```

Current state:

```text
GOOGLE

chewbacca@studentdomain.com


MICROSOFT

chewbacca@yourtenant.onmicrosoft.com
```

These do not match.

Our target is:

```text
GOOGLE

chewbacca@studentdomain.com


MICROSOFT

chewbacca@studentdomain.com
```

---

# Gate 14 — Change the Entra User Principal Name

Create the desired UPN:

```powershell
$NewUPN = "chewbacca@$Domain"
```

Verify the value:

```powershell
$NewUPN
```

Expected:

```text
chewbacca@studentdomain.com
```

Now update Chewbacca:

```powershell
Update-MgUser `
    -UserId $Chewbacca.Id `
    -UserPrincipalName $NewUPN
```

---

# Gate 15 — Verify the Updated Identity

Retrieve Chewbacca again:

```powershell
$Chewbacca = Get-MgUser `
    -UserId $Chewbacca.Id
```

Display:

```powershell
$Chewbacca |
    Select-Object `
        DisplayName,
        UserPrincipalName,
        Id
```

Expected:

```text
DisplayName        Chewbacca

UserPrincipalName  chewbacca@studentdomain.com
```

---

# Identity Checkpoint

You should now have:

```text
Google

Display Name:
Chewbacca

Primary Email:
chewbacca@studentdomain.com
```

and:

```text
Microsoft Entra ID

Display Name:
Chewbacca

UserPrincipalName:
chewbacca@studentdomain.com
```

Therefore:

```text
Google Primary Email
        =
Microsoft Entra UPN
```

---

# Gate 16 — Create the Pilot Synchronization Group

We do **not** want to synchronize every user immediately.

We will create a pilot group:

```text
SEIR_Google_Sync
```

Create it:

```powershell
$GoogleSyncGroup = New-MgGroup `
    -DisplayName "SEIR_Google_Sync" `
    -Description "Pilot group for Microsoft Entra to Google synchronization" `
    -MailEnabled:$false `
    -MailNickname "SEIRGoogleSync" `
    -SecurityEnabled
```

---

# Gate 17 — Verify the Group

Run:

```powershell
$GoogleSyncGroup |
    Select-Object `
        DisplayName,
        Id,
        SecurityEnabled
```

Expected:

```text
DisplayName       SEIR_Google_Sync

SecurityEnabled   True
```

---

# Gate 18 — Add Chewbacca to the Pilot Group

Create the membership reference:

```powershell
$MemberReference = @{
    "@odata.id" = "https://graph.microsoft.com/v1.0/directoryObjects/$($Chewbacca.Id)"
}
```

Add Chewbacca:

```powershell
New-MgGroupMemberByRef `
    -GroupId $GoogleSyncGroup.Id `
    -BodyParameter $MemberReference
```

---

# Gate 19 — Verify Group Membership

Run:

```powershell
Get-MgGroupMember `
    -GroupId $GoogleSyncGroup.Id
```

To verify Chewbacca specifically:

```powershell
Get-MgGroupMember `
    -GroupId $GoogleSyncGroup.Id |
    Where-Object {
        $_.Id -eq $Chewbacca.Id
    }
```

If an object is returned, Chewbacca is a member.

---

# Final Architecture

Your lab environment should now resemble:

```text
                        studentdomain.com
                               |
                  +------------+------------+
                  |                         |
                  v                         v

          Google Workspace          Microsoft Entra ID
          / Cloud Identity
                  |                         |
                  |                         |
                  v                         v

chewbacca@studentdomain.com    chewbacca@studentdomain.com
                                            |
                                            v
                                  SEIR_Google_Sync
```

---

# What Have We Actually Accomplished?

We now have:

```text
DOMAIN
studentdomain.com
       |
       +---- Verified by Google
       |
       +---- Verified by Microsoft
```

and:

```text
IDENTITY

Google
chewbacca@studentdomain.com

        =

Microsoft Entra
chewbacca@studentdomain.com
```

and:

```text
PILOT SCOPE

SEIR_Google_Sync
       |
       v
Chewbacca
```

---

# Why Did We Create a Pilot Group?

Because this:

```text
Microsoft Entra
       |
       v
EVERY USER
       |
       v
Google
```

is a terrible way to test a new synchronization configuration.

Instead:

```text
Microsoft Entra
       |
       v
SEIR_Google_Sync
       |
       v
Chewbacca
       |
       v
Google
```

If something goes wrong, the blast radius is one test identity.

---

# Gate 20 — Verify Nothing Else Changed

Before completing the lab, confirm all of the following.

## Google

```text
Google User Exists:          YES

Google Gmail Works:          YES

Google Domain Works:         YES
```

## Microsoft

```text
Custom Domain Verified:      YES

Matching Entra User Exists:  YES

Pilot Group Exists:          YES
```

## Things We Have NOT Enabled

```text
Automatic Provisioning:      NO

Google SAML SSO:             NO

Workforce Federation:        NO

Exchange MX:                 NO

Mail Migration:              NO
```

---

# Final PowerShell Verification

Run:

```powershell
Write-Host "======================================"
Write-Host "SEIR GOOGLE / ENTRA LAB 1 VERIFICATION"
Write-Host "======================================"

Write-Host "`nDOMAIN"

Get-MgDomain |
    Where-Object {
        $_.Id -eq $Domain
    } |
    Select-Object `
        Id,
        IsVerified,
        IsDefault

Write-Host "`nUSER"

Get-MgUser `
    -UserId $Chewbacca.Id |
    Select-Object `
        DisplayName,
        UserPrincipalName,
        Id

Write-Host "`nSYNC GROUP"

Get-MgGroup `
    -GroupId $GoogleSyncGroup.Id |
    Select-Object `
        DisplayName,
        Id,
        SecurityEnabled

Write-Host "`nGROUP MEMBERSHIP"

Get-MgGroupMember `
    -GroupId $GoogleSyncGroup.Id |
    Where-Object {
        $_.Id -eq $Chewbacca.Id
    }

Write-Host "`n=== LAB COMPLETE ==="
```

---

# Success Criteria

You have completed Lab 1 when:

- [ ] You identified your existing Google domain.
- [ ] Your Google test user exists.
- [ ] You recorded the Google user's primary email.
- [ ] You added the same domain to Microsoft 365.
- [ ] You added Microsoft's TXT verification record to DNS.
- [ ] Microsoft reports the domain as verified.
- [ ] `Get-MgDomain` reports `IsVerified = True`.
- [ ] Your existing Google mail still works.
- [ ] You did **not** change the MX record.
- [ ] Your Microsoft Entra test user exists.
- [ ] The Entra user's UPN matches the Google primary email.
- [ ] `SEIR_Google_Sync` exists.
- [ ] Chewbacca is a member of `SEIR_Google_Sync`.
- [ ] Automatic provisioning is still disabled.
- [ ] SSO is still disabled.

---

# Troubleshooting

## Problem — Microsoft Cannot Verify the Domain

Check:

```text
Did you add the correct TXT record?

Did you copy the complete MS= value?

Did you place the record in the correct DNS zone?

Has DNS had time to propagate?
```

Do not change the MX record to solve a TXT verification problem.

---

## Problem — Get-MgDomain Does Not Show the Domain

First verify your Graph connection:

```powershell
Get-MgContext
```

Then reconnect:

```powershell
Disconnect-MgGraph
```

```powershell
Connect-MgGraph -Scopes `
    "Domain.Read.All", `
    "User.ReadWrite.All", `
    "Group.ReadWrite.All"
```

Try again:

```powershell
Get-MgDomain
```

---

## Problem — Update-MgUser Rejects the New UPN

Verify that the domain exists:

```powershell
Get-MgDomain
```

Verify:

```text
studentdomain.com
```

shows:

```text
IsVerified = True
```

The custom domain must be verified before using it as the domain portion of a Microsoft Entra UPN.

---

## Problem — Chewbacca Cannot Be Found

Try:

```powershell
Get-MgUser -All |
    Where-Object {
        $_.DisplayName -eq "Chewbacca"
    }
```

Then examine:

```powershell
DisplayName
UserPrincipalName
Id
```

---

## Problem — Multiple Chewbaccas Exist

Do not select users based only on:

```text
DisplayName
```

Use the User Principal Name or Object ID.

For example:

```powershell
Get-MgUser `
    -UserId "chewbacca@yourtenant.onmicrosoft.com"
```

Object IDs are even safer when writing automation.

---

# Security Note

Never submit:

```text
Passwords

Authentication Tokens

Refresh Tokens

Client Secrets

Private Keys

MFA Codes
```

You may submit verification information such as:

```text
Domain Name

IsVerified

Display Name

User Principal Name

Group Name

Successful Membership Verification
```

---

# Discussion Questions

## Question 1

Why did we verify the domain in Microsoft before changing Chewbacca's UPN?

---

## Question 2

Why did we leave the Google MX record unchanged?

---

## Question 3

What is the difference between:

```text
Domain Registration
```

and:

```text
DNS Hosting
```

and:

```text
Email Hosting
```

and:

```text
Identity Provider
```

---

## Question 4

Why do we want:

```text
Google Primary Email
        =
Microsoft Entra UPN
```

before enabling automatic provisioning?

---

## Question 5

Why are we synchronizing only:

```text
SEIR_Google_Sync
```

instead of every user?

---

## Question 6

What could happen if you enabled synchronization for the entire directory before testing a single user?

---

# Key Concept

Today you did **not** build federation.

You prepared the identities for federation.

The important state is:

```text
DOMAIN VERIFIED
       +
IDENTITIES ALIGNED
       +
PILOT GROUP CREATED
       =
READY FOR SYNCHRONIZATION
```

---

# Next Lab

In the next lab, we will begin:

```text
Microsoft Entra ID
        |
        | Automatic Provisioning
        v
Google Workspace / Cloud Identity
```

We will attempt to synchronize the pilot user:

```text
Chewbacca
```

without creating a duplicate Google identity.

The question for the next lab is:

> Can Microsoft Entra correctly match the existing Google identity and begin managing it through provisioning?

Only after provisioning works correctly will we move on to:

```text
SAML SSO
```

and later:

```text
Workforce Identity Federation
```
