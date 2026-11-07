# SEIR-1 Cross-Cloud IAM Lab

# Gate 4 — Create and Verify the Microsoft Entra User

## Objective

In Gate 3, Microsoft Entra learned the identity of the **computer**.

You currently have:

```text
Microsoft Entra ID
       |
       v
Device Identity
       |
       v
seir-crosscloud-01
```

Now we will create the **human identity**.

At the end of Gate 4:

```text
Microsoft Entra ID
       |
       +-------------------------+
       |                         |
       v                         v

Device Identity             User Identity

seir-crosscloud-01          Chewbacca
                            chewbacca@YOURDOMAIN
```

However:

```text
Chewbacca
    |
    X
    |
seir-crosscloud-01
```

The user will **not yet** have permission to log into the server.

That authorization will be created in Gate 5.

---

# The Most Important IAM Lesson

Creating an identity does not create authorization.

Remember:

```text
IDENTITY
!=
ACCESS
```

We can have:

```text
User exists: YES
```

while:

```text
May log into server: NO
```

That is exactly the state we want at the end of Gate 4.

---

# Gate 4.1 — Verify Azure CLI Authentication

From your workstation:

```bash
az account show \
    --output table
```

Verify that you are connected to the correct:

```text
Azure Subscription

Microsoft Entra Tenant

Azure Account
```

If necessary:

```bash
az login
```

Then:

```bash
az account set \
    --subscription "YOUR_SUBSCRIPTION_ID"
```

---

# Gate 4.2 — Verify the Custom Domain

Your Microsoft Entra tenant should already contain the domain used earlier in the course.

Run:

```bash
az rest \
    --method GET \
    --url "https://graph.microsoft.com/v1.0/domains"
```

For easier output:

```bash
az rest \
    --method GET \
    --url "https://graph.microsoft.com/v1.0/domains" \
    --query "value[].{Domain:id,Verified:isVerified}" \
    --output table
```

You should see your custom domain.

Example:

```text
Domain                Verified
--------------------  --------
balerica-ai.org       True
```

Do not continue until:

```text
Verified = True
```

---

# Why Does the Domain Matter?

Without the custom domain, we might create:

```text
chewbacca@tenant.onmicrosoft.com
```

Instead, we want:

```text
chewbacca@balerica-ai.org
```

The custom domain gives the identity a normal organizational namespace.

---

# Gate 4.3 — Verify the User Does Not Already Exist

Define the user:

```bash
USER_UPN="chewbacca@balerica-ai.org"
```

Then:

```bash
az ad user show \
    --id "$USER_UPN"
```

If the user does not exist, Azure CLI should report that it cannot find the object.

That is expected.

If the user already exists, either:

```text
Use the existing user
```

or use another lab identity such as:

```text
arcuser01@balerica-ai.org
```

Do not create duplicate identities merely to complete the lab.

---

# Gate 4.4 — Create a Temporary Password

Do not place passwords directly into:

```text
Git repositories

README files

Screenshots

Class chat

Shell scripts
```

## Bash / Git Bash

Use:

```bash
read -s -p "Temporary password: " TEMP_PASSWORD
echo
```

The password will not be displayed while you type it.

---

# Gate 4.5 — Create the Microsoft Entra User

Create the identity:

```bash
az ad user create \
    --display-name "Chewbacca" \
    --user-principal-name "$USER_UPN" \
    --mail-nickname "chewbacca" \
    --password "$TEMP_PASSWORD" \
    --force-change-password-next-sign-in true
```

Microsoft's current Azure CLI requires:

```text
display name

password

user principal name
```

and the UPN must use a domain verified in the tenant.

---

# Gate 4.6 — Immediately Remove the Password Variable

After user creation:

```bash
unset TEMP_PASSWORD
```

Verify:

```bash
echo "$TEMP_PASSWORD"
```

There should be no output.

---

# Gate 4.7 — Verify the User

Run:

```bash
az ad user show \
    --id "$USER_UPN" \
    --output json
```

For cleaner output:

```bash
az ad user show \
    --id "$USER_UPN" \
    --query "{DisplayName:displayName,UPN:userPrincipalName,ObjectId:id,Type:userType}" \
    --output table
```

Expected conceptually:

```text
DisplayName   UPN                            ObjectId        Type
------------  -----------------------------  --------------  ------
Chewbacca     chewbacca@balerica-ai.org      <GUID>          Member
```

---

# Gate 4.8 — Record the User Object ID

Run:

```bash
USER_OBJECT_ID=$(az ad user show \
    --id "$USER_UPN" \
    --query id \
    --output tsv)
```

Verify:

```bash
echo "$USER_OBJECT_ID"
```

You should receive a GUID:

```text
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

This value identifies the Entra user security principal.

---

# Why Do We Care About Object ID?

Humans like:

```text
chewbacca@balerica-ai.org
```

Azure authorization ultimately works against security principals represented by IDs.

Conceptually:

```text
Chewbacca

Friendly Name
      |
      v
chewbacca@balerica-ai.org

User Principal Name
      |
      v
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

Object ID
```

Later Azure RBAC will use that identity.

---

# Gate 4.9 — Verify This Is a Member User

The Arc Entra login scenario requires a standard Microsoft Entra user in the **same tenant** as the Arc-enabled server.

Run:

```bash
az ad user show \
    --id "$USER_UPN" \
    --query userType \
    --output tsv
```

Expected:

```text
Member
```

Do not use:

```text
Guest
```

for this lab.

Microsoft currently states that B2B guest users cannot authenticate to an Arc-enabled Windows Server using this Entra login capability.

---

# Gate 4.10 — Verify the User's Tenant

Check the current tenant:

```bash
az account show \
    --query tenantId \
    --output tsv
```

Now inspect the Arc machine:

```bash
az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query identity.tenantId \
    --output tsv
```

These should identify the same Microsoft Entra tenant.

Conceptually:

```text
Chewbacca
     |
     v
Tenant A


Arc Machine
     |
     v
Tenant A
```

Not:

```text
Chewbacca
     |
     v
Tenant A


Arc Machine
     |
     v
Tenant B
```

Cross-directory managed identity scenarios are not supported for this login model.

---

# Gate 4.11 — Change the Temporary Password

This step is important.

Microsoft Entra users with temporary passwords cannot use that temporary password for RDP to the Arc-enabled server.

The user must first complete the normal password-change process.

Sign into an appropriate Microsoft sign-in page using:

```text
chewbacca@balerica-ai.org
```

and the temporary password.

Microsoft will require the user to establish a new password.

Complete that process.

---

# Important

The final password should belong to the user.

The instructor should not:

```text
Record it

Store it

Place it in Git

Place it in lab documentation

Share it with the class
```

---

# Gate 4.12 — Test Normal Entra Authentication

After changing the password, verify that the identity itself works.

From a fresh browser session, sign in as:

```text
chewbacca@balerica-ai.org
```

A successful authentication proves:

```text
USER EXISTS

+

PASSWORD WORKS

+

TENANT AUTHENTICATION WORKS
```

It does **not** prove VM access.

---

# Gate 4.13 — Retrieve the Arc Resource ID

Now identify the resource we will eventually authorize against.

Run:

```bash
ARC_RESOURCE_ID=$(az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query id \
    --output tsv)
```

Verify:

```bash
echo "$ARC_RESOURCE_ID"
```

It should resemble:

```text
/subscriptions/<subscription-id>
/resourceGroups/SEIR-ARC-RG
/providers/Microsoft.HybridCompute
/machines/seir-crosscloud-01
```

This will become the RBAC **scope**.

---

# Recall the RBAC Formula

From our earlier Azure IAM lessons:

```text
PRINCIPAL
+
ROLE
+
SCOPE
=
ACCESS
```

We already have two of those concepts.

---

# PRINCIPAL

```text
Chewbacca

chewbacca@balerica-ai.org
```

---

# SCOPE

```text
seir-crosscloud-01
```

---

# ROLE

Currently:

```text
NONE
```

Therefore:

```text
Chewbacca
+
NO LOGIN ROLE
+
seir-crosscloud-01
=
NO LOGIN ACCESS
```

Exactly what we want.

---

# Gate 4.14 — Prove No VM Login Role Exists

Run:

```bash
az role assignment list \
    --assignee "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --include-inherited \
    --output table
```

Inspect the output.

You should **not** find:

```text
Virtual Machine User Login
```

or:

```text
Virtual Machine Administrator Login
```

---

# Important

The user may potentially have other Azure permissions.

For example:

```text
Reader

Contributor

Owner
```

Those roles are not equivalent to Windows login authorization.

Microsoft intentionally separates:

```text
WHO MAY MANAGE THE RESOURCE
```

from:

```text
WHO MAY LOG INTO THE OPERATING SYSTEM
```

Even Azure `Owner` or `Contributor` does not automatically give the user permission to RDP into this Arc-enabled server.

---

# Gate 4.15 — Specifically Search for Login Roles

Run:

```bash
az role assignment list \
    --assignee "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --include-inherited \
    --query "[].roleDefinitionName" \
    --output tsv
```

You must not see:

```text
Virtual Machine User Login
```

or:

```text
Virtual Machine Administrator Login
```

If either role already exists, the lab no longer has a clean before-state.

Remove the preexisting login assignment or use another test user.

---

# Gate 4.16 — Optional Negative Test

This is an excellent classroom demonstration.

At this point:

```text
Device exists.

User exists.

Entra works.

Password works.

Arc works.
```

But there is no login role.

Attempting to use the Entra identity for the server should therefore fail authorization.

That failure is expected.

The important lesson is:

```text
Authentication may succeed

BUT

Authorization may fail
```

---

# Authentication vs Authorization

## Authentication

Answers:

```text
Who are you?
```

Microsoft Entra answers:

```text
You are Chewbacca.
```

---

## Authorization

Answers:

```text
What are you allowed to do?
```

Azure RBAC currently answers:

```text
You are NOT allowed to log into this server.
```

---

# Current Architecture

```text
                         MICROSOFT ENTRA ID
                               |
                +--------------+--------------+
                |                             |
                v                             v

        Device Identity                User Identity
   seir-crosscloud-01                   Chewbacca
                |                             |
                |                             |
                |                       Authenticated
                |                             |
                |                             X
                |                        NO RBAC ROLE
                |                             |
                +--------------+--------------+
                               |
                               v
                           Azure Arc
                               |
                               v
                       Windows Server 2025
                               |
                               v
                              GCP
```

---

# Why No Microsoft 365 License?

Chewbacca does **not** need an Office 365 or Microsoft 365 product license merely to exist as an Entra identity for this lab.

We are using:

```text
Microsoft Entra identity
```

for:

```text
Windows infrastructure authentication
```

We are not attempting to provide:

```text
Exchange Online

Office applications

Teams

OneDrive
```

Those are separate Microsoft 365 services and licensing concerns.

This is another useful distinction:

```text
Entra User
!=
Office 365 User License
```

---

# Gate 4 Verification Commands

## User

```bash
az ad user show \
    --id "$USER_UPN" \
    --query "{Name:displayName,UPN:userPrincipalName,ObjectId:id,Type:userType}" \
    --output table
```

---

## Device

```bash
az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query "{Name:name,Status:status}" \
    --output table
```

Expected:

```text
Connected
```

---

## Scope

```bash
echo "$ARC_RESOURCE_ID"
```

---

## Login Authorization

```bash
az role assignment list \
    --assignee "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --include-inherited \
    --query "[].roleDefinitionName" \
    --output table
```

Verify that neither login role exists.

---

# Success Criteria

Gate 4 is complete when:

- [ ] The custom domain is verified in Microsoft Entra.
- [ ] The user exists.
- [ ] The user UPN uses the custom domain.
- [ ] The user's type is `Member`.
- [ ] The user's Object ID has been recorded.
- [ ] The user belongs to the same Entra tenant as the Arc machine.
- [ ] The temporary password has been changed.
- [ ] The user can successfully authenticate to Microsoft Entra.
- [ ] The Arc resource ID has been identified.
- [ ] The user does not have `Virtual Machine User Login`.
- [ ] The user does not have `Virtual Machine Administrator Login`.
- [ ] The user cannot yet log into the GCP Windows Server using Entra authorization.

---

# Stop Condition

If the user cannot authenticate normally to Microsoft Entra:

```text
STOP.
```

Do not troubleshoot:

```text
RDP

Azure Arc Login

Windows authorization

Azure RBAC
```

The problem is still at the identity layer.

Likewise, if the user is:

```text
Guest
```

do not continue with that identity.

Use a standard same-tenant:

```text
Member
```

account.

---

# Gate 4 Mental Model

We now know:

```text
GATE 1

Does the computer work?

YES
```

```text
GATE 2

Can Azure manage the computer?

YES
```

```text
GATE 3

Does Entra know the computer?

YES
```

```text
GATE 4

Does Entra know the human?

YES
```

But:

```text
Can the human log into the computer?

NO
```

That is deliberate.

---

# Next Gate — Authorization

Gate 5 will finally connect:

```text
USER
```

to:

```text
DEVICE
```

using:

```text
AZURE RBAC
```

The formula becomes:

```text
Chewbacca
      +
Virtual Machine User Login
      +
seir-crosscloud-01
      =
AUTHORIZED ACCESS
```

That will be the moment where the entire lab comes together:

```text
GCP COMPUTE

+

AZURE ARC

+

MICROSOFT ENTRA

+

AZURE RBAC

=

CROSS-CLOUD USER ACCESS
```
