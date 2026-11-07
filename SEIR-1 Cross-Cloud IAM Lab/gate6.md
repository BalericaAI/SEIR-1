# SEIR-1 Cross-Cloud IAM Lab

# Gate 6 — Replace Direct User Access with Group-Based RBAC

## Objective

Gate 5 proved that Azure RBAC can authorize a Microsoft Entra user to log into a Windows Server hosted in Google Cloud.

The architecture currently looks like this:

```text

Chewbacca
    |
    | Direct RBAC Assignment
    v
Virtual Machine User Login
    |
    v
seir-crosscloud-01
```

That works.

But in a real organization, directly assigning infrastructure permissions to hundreds or thousands of individual employees becomes difficult to manage.

Gate 6 introduces the more common enterprise pattern:

```text

Chewbacca
    |
    v
SEIR_ARC_Users
    |
    | Azure RBAC
    v
Virtual Machine User Login
    |
    v
seir-crosscloud-01
```

The Azure role will belong to the **group**.

The user's authorization will come from:

```text

GROUP MEMBERSHIP
```

---

# Why Groups?

Imagine an organization has:

```text

500 Engineers

200 Servers

50 Administrators

100 Contractors
```

Direct RBAC assignments could become:

```text

User A -> Server 1
User A -> Server 2
User A -> Server 3

User B -> Server 1
User B -> Server 4

User C -> Server 2
User C -> Server 3

...
```

This quickly becomes difficult to manage.

Instead:

```text

Users
  |
  v
Security Group
  |
  v
Azure Role
  |
  v
Resource
```

Microsoft Entra security groups are specifically intended to help manage access to Azure resources and other organizational resources. Azure RBAC can assign roles to users, groups, managed identities, and service principals.

---

# The Enterprise Model

Instead of:

```text

USER
  |
  v
PERMISSION
```

we want:

```text

USER
  |
  v
GROUP
  |
  v
PERMISSION
```

That produces an important separation:

```text

Entra controls:
WHO IS IN THE GROUP

Azure RBAC controls:
WHAT THE GROUP MAY DO
```

---

# Gate 6.1 — Verify Gate 5 Works

Before changing the authorization model, verify that the current direct assignment exists.

Define the user:

```bash
USER_UPN="chewbacca@balerica-ai.org"
```

Retrieve the user Object ID:

```bash
USER_OBJECT_ID=$(az ad user show \
    --id "$USER_UPN" \
    --query id \
    --output tsv)
```

Retrieve the Arc resource ID:

```bash
ARC_RESOURCE_ID=$(az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query id \
    --output tsv)
```

Verify the current role assignment:

```bash
az role assignment list \
    --assignee-object-id "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[].{Role:roleDefinitionName,Scope:scope}" \
    --output table
```

You should see:

```text

Virtual Machine User Login
```

---

# Current State

```text

Chewbacca
    |
    |
    | DIRECT ASSIGNMENT
    |
    v
Virtual Machine User Login
    |
    v
seir-crosscloud-01
```

We are going to remove this model.

---

# Gate 6.2 — Create an Entra Security Group

Create:

```text

SEIR_ARC_Users
```

Run:

```bash
az ad group create \
    --display-name "SEIR_ARC_Users" \
    --mail-nickname "SEIRARCUsers" \
    --description "Users authorized for standard login to SEIR Azure Arc servers"
```

Azure CLI supports creating Microsoft Entra groups using `az ad group create`, with display name and mail nickname as required values.

---

# Gate 6.3 — Verify the Group

Run:

```bash
az ad group show \
    --group "SEIR_ARC_Users" \
    --query "{
        Name:displayName,
        ObjectId:id,
        SecurityEnabled:securityEnabled,
        MailEnabled:mailEnabled
    }" \
    --output table
```

The important result is:

```text

SecurityEnabled = True
```

We want a:

```text

SECURITY GROUP
```

not a distribution list.

---

# Gate 6.4 — Record the Group Object ID

Run:

```bash
GROUP_OBJECT_ID=$(az ad group show \
    --group "SEIR_ARC_Users" \
    --query id \
    --output tsv)
```

Verify:

```bash
echo "$GROUP_OBJECT_ID"
```

Expected:

```text

xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

# The Group Is Now an Entra Security Principal

Our architecture currently looks like:

```text

Microsoft Entra

Chewbacca

SEIR_ARC_Users
```

But:

```text

Chewbacca
    |
    X
    |
SEIR_ARC_Users
```

Chewbacca is not yet a member.

And:

```text

SEIR_ARC_Users
    |
    X
    |
Azure RBAC
```

The group does not yet have any Azure permission.

---

# Gate 6.5 — Add Chewbacca to the Group

Run:

```bash
az ad group member add \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

Azure CLI supports adding an Entra object to a group using:

```text

az ad group member add
```

with the member's Object ID.

---

# Gate 6.6 — Verify Membership

Run:

```bash
az ad group member check \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

Expected:

```json
{
  "value": true
}
```

Microsoft's Azure CLI includes `az ad group member check` specifically for verifying group membership.

---

# List Group Members

Run:

```bash
az ad group member list \
    --group "SEIR_ARC_Users" \
    --query "[].{Name:displayName,UPN:userPrincipalName,ObjectId:id}" \
    --output table
```

You should see:

```text

Chewbacca
chewbacca@balerica-ai.org
```

---

# Current State

```text

Chewbacca
    |
    | MEMBER
    v
SEIR_ARC_Users
```

But the group still has no Azure permission.

---

# Gate 6.7 — Remove the Direct User Assignment

This step is critical.

If we leave the direct Gate 5 assignment in place, we cannot prove that group authorization works.

Remove:

```text

Chewbacca
    |
    v
Virtual Machine User Login
```

Run:

```bash
az role assignment delete \
    --assignee-object-id "$USER_OBJECT_ID" \
    --role "Virtual Machine User Login" \
    --scope "$ARC_RESOURCE_ID"
```

---

# Gate 6.8 — Verify Direct Access Is Gone

Run:

```bash
az role assignment list \
    --assignee-object-id "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[].roleDefinitionName" \
    --output table
```

You should **not** see:

```text

Virtual Machine User Login
```

---

# Architecture Checkpoint

Now:

```text

Chewbacca
    |
    v
SEIR_ARC_Users
```

but:

```text

SEIR_ARC_Users
    |
    X
    |
seir-crosscloud-01
```

Therefore:

```text

NO LOGIN AUTHORIZATION
```

---

# Optional Negative Test

This is an excellent live demonstration.

Completely disconnect the existing RDP session.

Attempt a new Entra login.

Expected:

```text

ACCESS DENIED
```

Why?

Because:

```text

USER EXISTS             YES

GROUP MEMBERSHIP        YES

GROUP PERMISSION        NO
```

Group membership alone does not create permission.

---

# Gate 6.9 — Assign the Login Role to the Group

Now assign:

```text

Virtual Machine User Login
```

to:

```text

SEIR_ARC_Users
```

Run:

```bash
az role assignment create \
    --assignee-object-id "$GROUP_OBJECT_ID" \
    --assignee-principal-type Group \
    --role "Virtual Machine User Login" \
    --scope "$ARC_RESOURCE_ID"
```

Azure RBAC supports groups as security principals. Using the group's Object ID together with:

```text

--assignee-principal-type Group
```

explicitly tells Azure that the principal is an Entra group.

---

# Why Use the Object ID?

We could sometimes use:

```text

SEIR_ARC_Users
```

but for automation and infrastructure work, the safer identifier is:

```text

GROUP OBJECT ID
```

Names can change.

Object IDs are the actual directory identifiers used by the authorization system.

---

# Gate 6.10 — Verify the Group Role Assignment

Run:

```bash
az role assignment list \
    --assignee-object-id "$GROUP_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[].{Role:roleDefinitionName,Scope:scope}" \
    --output table
```

Expected:

```text

Role
--------------------------
Virtual Machine User Login
```

---

# The Authorization Chain Is Now Complete

```text

Chewbacca
    |
    | MEMBER OF
    v
SEIR_ARC_Users
    |
    | HAS ROLE
    v
Virtual Machine User Login
    |
    | AT SCOPE
    v
seir-crosscloud-01
```

---

# Gate 6.11 — Test Login Again

Start a completely new RDP session.

Use the Entra login method from Gate 5.

Authenticate as:

```text

chewbacca@balerica-ai.org
```

Expected:

```text

ACCESS GRANTED
```

The important difference is:

```text

Gate 5:
User had the role directly.

Gate 6:
Group has the role.
```

---

# Gate 6.12 — Verify the User Has No Direct Role

Run:

```bash
az role assignment list \
    --assignee-object-id "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[].roleDefinitionName" \
    --output table
```

There should be no direct:

```text

Virtual Machine User Login
```

assignment.

Yet Chewbacca can log in.

Therefore the effective authorization path is:

```text

USER
 |
 v
GROUP
 |
 v
RBAC
 |
 v
SERVER
```

---

# This Is the Enterprise Pattern

Instead of:

```text

Bob     -> Server
Alice   -> Server
James   -> Server
Maria   -> Server
Theo    -> Server
```

we use:

```text

Bob
Alice
James
Maria
Theo
  |
  v
SEIR_ARC_Users
  |
  v
Server
```

Azure RBAC explicitly allows roles to be assigned to groups rather than individual users.

---

# Gate 6.13 — Remove Chewbacca From the Group

Now demonstrate access lifecycle management.

Run:

```bash
az ad group member remove \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

---

# Gate 6.14 — Verify Removal

Run:

```bash
az ad group member check \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

Expected:

```json
{
  "value": false
}
```

---

# What Changed?

We did **not** change:

```text

GCP VM

Azure Arc

AADLoginForWindows

Azure RBAC Role

Security Group

User Account
```

The only change was:

```text

GROUP MEMBERSHIP
```

---

# Current State

```text

Chewbacca
    |
    X
    |
SEIR_ARC_Users
    |
    |
    v
Virtual Machine User Login
    |
    v
seir-crosscloud-01
```

Therefore Chewbacca should no longer receive access through that group.

---

# Gate 6.15 — Test Login Again

Fully disconnect the previous RDP session.

Start a **new authentication attempt**.

Do not rely on an existing logged-in Windows session.

Expected:

```text

ACCESS DENIED
```

Directory membership and authorization changes can require the authentication system to obtain fresh directory and authorization state, so use a new login attempt when validating changes.

---

# The Important Enterprise Lesson

The server's permission did not change.

The group still has:

```text

Virtual Machine User Login
```

Chewbacca lost access because:

```text

Chewbacca
   |
   X
   |
SEIR_ARC_Users
```

This is how employee access can be managed centrally.

---

# Imagine Employee Offboarding

Suppose Chewbacca leaves the infrastructure team.

We do not need to find every server:

```text

Server 1

Server 2

Server 3

Server 4

Server 5
```

and remove him individually.

Instead:

```text

Remove User
from
Security Group
```

The resource permissions remain attached to the group.

---

# Gate 6.16 — Restore Chewbacca

Add the user back:

```bash
az ad group member add \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

Verify:

```bash
az ad group member check \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

Expected:

```json
{
  "value": true
}
```

---

# Gate 6.17 — Test Login Again

Start another fresh RDP authentication.

Expected:

```text

ACCESS GRANTED
```

You have now demonstrated:

```text

GROUP MEMBER
     |
     v
ACCESS ALLOWED


MEMBER REMOVED
     |
     v
ACCESS DENIED


MEMBER RESTORED
     |
     v
ACCESS ALLOWED
```

---

# What Never Changed?

During all three tests:

```text

GROUP RBAC ASSIGNMENT

Virtual Machine User Login
```

remained unchanged.

That is the point.

---

# Gate 6.18 — Inspect the Final Architecture

## User

```bash
az ad user show \
    --id "$USER_UPN" \
    --query "{User:displayName,UPN:userPrincipalName,ObjectId:id}" \
    --output table
```

## Group

```bash
az ad group show \
    --group "SEIR_ARC_Users" \
    --query "{Group:displayName,ObjectId:id,Security:securityEnabled}" \
    --output table
```

## Membership

```bash
az ad group member check \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

## RBAC

```bash
az role assignment list \
    --assignee-object-id "$GROUP_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[].{Role:roleDefinitionName,Scope:scope}" \
    --output table
```

---

# Final Architecture

```text

                     MICROSOFT ENTRA ID
                            |
                            |
                    chewbacca@domain
                            |
                         MEMBER
                            |
                            v
                     SEIR_ARC_Users
                            |
                            |
                     AZURE RBAC
                            |
                            v
                Virtual Machine User Login
                            |
                          SCOPE
                            |
                            v
                       AZURE ARC
                            |
                            v
                  seir-crosscloud-01
                            |
                            v
                   Windows Server 2025
                            |
                            v
                            GCP
```

---

# Identity and Authorization Are Now Separated Properly

Microsoft Entra answers:

```text

WHO IS CHEWBACCA?
```

Group membership answers:

```text

WHAT TEAM IS CHEWBACCA ON?
```

Azure RBAC answers:

```text

WHAT MAY THAT TEAM ACCESS?
```

Azure Arc answers:

```text

WHICH EXTERNAL SERVER IS THE RESOURCE?
```

GCP answers:

```text

WHERE DOES THE COMPUTER ACTUALLY RUN?
```

---

# Gate 6 Success Criteria

Gate 6 is complete when:

- [ ] `SEIR_ARC_Users` exists.
- [ ] It is a Microsoft Entra security group.
- [ ] Chewbacca is a member.
- [ ] Chewbacca has no direct VM login role.
- [ ] `SEIR_ARC_Users` has `Virtual Machine User Login`.
- [ ] The role scope is `seir-crosscloud-01`.
- [ ] Chewbacca can log in through group authorization.
- [ ] Removing Chewbacca from the group removes access.
- [ ] The group's Azure RBAC role remains unchanged.
- [ ] Adding Chewbacca back restores access.
- [ ] No local Windows group manipulation was required.

---

# The Progression So Far

## Gate 1

```text

GCP = COMPUTER
```

## Gate 2

```text

ARC = BRIDGE
```

## Gate 3

```text

ENTRA = DEVICE IDENTITY
```

## Gate 4

```text

ENTRA = USER IDENTITY
```

## Gate 5

```text

RBAC = DIRECT USER AUTHORIZATION
```

## Gate 6

```text

GROUPS = ENTERPRISE AUTHORIZATION
```

---

# Why Gate 6 Matters

Gate 5 answered:

> Can I give Chewbacca access to this machine?

Gate 6 answers the much more important enterprise question:

> How do I manage access when I have hundreds of Chewbaccas and hundreds of machines?

Answer:

```text

IDENTITY
    |
    v
GROUP MEMBERSHIP
    |
    v
RBAC
    |
    v
RESOURCE
```

---

# The Office Version

This is similar to how organizations manage many other resources:

```text

Employee
   |
   v
Entra Group
   |
   +---- SharePoint
   |
   +---- Azure
   |
   +---- Applications
   |
   +---- Infrastructure
```

The employee is not individually wired to every resource.

Their organizational membership determines their authorization.

---

# Second-Round Automation

After completing Gate 6 manually, this is an excellent lab to reproduce using an AI coding agent such as Claude Code.

The desired state can be described declaratively:

```text

Create security group:
SEIR_ARC_Users

Ensure:
chewbacca@balerica-ai.org
is a member

Ensure:
SEIR_ARC_Users
has
Virtual Machine User Login

Scope:
seir-crosscloud-01

Ensure:
Chewbacca has no duplicate direct assignment
```

The important rule is:

> Do not ask the coding agent to solve a lab you do not understand.

First:

```text

MANUAL IMPLEMENTATION
```

Then:

```text

AI-ASSISTED IMPLEMENTATION
```

Then students can compare the implementation generated by the tool with the architecture they already built themselves.
