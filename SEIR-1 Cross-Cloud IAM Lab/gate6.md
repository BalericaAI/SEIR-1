# SEIR-1 Cross-Cloud IAM Lab

# Gate 6 — Replace Direct User Access with Group-Based RBAC

## Objective

Gate 5 proved that Azure RBAC can authorize a Microsoft Entra user to log into a Windows Server hosted in Google Cloud.

The architecture currently looks like this:

```text id="la1"

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

```text id="la2"

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

```text id="la3"

GROUP MEMBERSHIP
```

---

# Why Groups?

Imagine an organization has:

```text id="la4"

500 Engineers

200 Servers

50 Administrators

100 Contractors
```

Direct RBAC assignments could become:

```text id="la5"

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

```text id="la6"

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

```text id="la7"

USER
  |
  v
PERMISSION
```

we want:

```text id="la8"

USER
  |
  v
GROUP
  |
  v
PERMISSION
```

That produces an important separation:

```text id="la9"

Entra controls:
WHO IS IN THE GROUP

Azure RBAC controls:
WHAT THE GROUP MAY DO
```

---

# Gate 6.1 — Verify Gate 5 Works

Before changing the authorization model, verify that the current direct assignment exists.

Define the user:

```bash id="la10"
USER_UPN="chewbacca@balerica-ai.org"
```

Retrieve the user Object ID:

```bash id="la11"
USER_OBJECT_ID=$(az ad user show \
    --id "$USER_UPN" \
    --query id \
    --output tsv)
```

Retrieve the Arc resource ID:

```bash id="la12"
ARC_RESOURCE_ID=$(az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query id \
    --output tsv)
```

Verify the current role assignment:

```bash id="la13"
az role assignment list \
    --assignee-object-id "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[].{Role:roleDefinitionName,Scope:scope}" \
    --output table
```

You should see:

```text id="la14"

Virtual Machine User Login
```

---

# Current State

```text id="la15"

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

```text id="la16"

SEIR_ARC_Users
```

Run:

```bash id="la17"
az ad group create \
    --display-name "SEIR_ARC_Users" \
    --mail-nickname "SEIRARCUsers" \
    --description "Users authorized for standard login to SEIR Azure Arc servers"
```

Azure CLI supports creating Microsoft Entra groups using `az ad group create`, with display name and mail nickname as required values.

---

# Gate 6.3 — Verify the Group

Run:

```bash id="la18"
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

```text id="la19"

SecurityEnabled = True
```

We want a:

```text id="la20"

SECURITY GROUP
```

not a distribution list.

---

# Gate 6.4 — Record the Group Object ID

Run:

```bash id="la21"
GROUP_OBJECT_ID=$(az ad group show \
    --group "SEIR_ARC_Users" \
    --query id \
    --output tsv)
```

Verify:

```bash id="la22"
echo "$GROUP_OBJECT_ID"
```

Expected:

```text id="la23"

xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

# The Group Is Now an Entra Security Principal

Our architecture currently looks like:

```text id="la24"

Microsoft Entra

Chewbacca

SEIR_ARC_Users
```

But:

```text id="la25"

Chewbacca
    |
    X
    |
SEIR_ARC_Users
```

Chewbacca is not yet a member.

And:

```text id="la26"

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

```bash id="la27"
az ad group member add \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

Azure CLI supports adding an Entra object to a group using:

```text id="la28"

az ad group member add
```

with the member's Object ID.

---

# Gate 6.6 — Verify Membership

Run:

```bash id="la29"
az ad group member check \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

Expected:

```json id="la30"
{
  "value": true
}
```

Microsoft's Azure CLI includes `az ad group member check` specifically for verifying group membership.

---

# List Group Members

Run:

```bash id="la31"
az ad group member list \
    --group "SEIR_ARC_Users" \
    --query "[].{Name:displayName,UPN:userPrincipalName,ObjectId:id}" \
    --output table
```

You should see:

```text id="la32"

Chewbacca
chewbacca@balerica-ai.org
```

---

# Current State

```text id="la33"

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

```text id="la34"

Chewbacca
    |
    v
Virtual Machine User Login
```

Run:

```bash id="la35"
az role assignment delete \
    --assignee-object-id "$USER_OBJECT_ID" \
    --role "Virtual Machine User Login" \
    --scope "$ARC_RESOURCE_ID"
```

---

# Gate 6.8 — Verify Direct Access Is Gone

Run:

```bash id="la36"
az role assignment list \
    --assignee-object-id "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[].roleDefinitionName" \
    --output table
```

You should **not** see:

```text id="la37"

Virtual Machine User Login
```

---

# Architecture Checkpoint

Now:

```text id="la38"

Chewbacca
    |
    v
SEIR_ARC_Users
```

but:

```text id="la39"

SEIR_ARC_Users
    |
    X
    |
seir-crosscloud-01
```

Therefore:

```text id="la40"

NO LOGIN AUTHORIZATION
```

---

# Optional Negative Test

This is an excellent live demonstration.

Completely disconnect the existing RDP session.

Attempt a new Entra login.

Expected:

```text id="la41"

ACCESS DENIED
```

Why?

Because:

```text id="la42"

USER EXISTS             YES

GROUP MEMBERSHIP        YES

GROUP PERMISSION        NO
```

Group membership alone does not create permission.

---

# Gate 6.9 — Assign the Login Role to the Group

Now assign:

```text id="la43"

Virtual Machine User Login
```

to:

```text id="la44"

SEIR_ARC_Users
```

Run:

```bash id="la45"
az role assignment create \
    --assignee-object-id "$GROUP_OBJECT_ID" \
    --assignee-principal-type Group \
    --role "Virtual Machine User Login" \
    --scope "$ARC_RESOURCE_ID"
```

Azure RBAC supports groups as security principals. Using the group's Object ID together with:

```text id="la46"

--assignee-principal-type Group
```

explicitly tells Azure that the principal is an Entra group.

---

# Why Use the Object ID?

We could sometimes use:

```text id="la47"

SEIR_ARC_Users
```

but for automation and infrastructure work, the safer identifier is:

```text id="la48"

GROUP OBJECT ID
```

Names can change.

Object IDs are the actual directory identifiers used by the authorization system.

---

# Gate 6.10 — Verify the Group Role Assignment

Run:

```bash id="la49"
az role assignment list \
    --assignee-object-id "$GROUP_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[].{Role:roleDefinitionName,Scope:scope}" \
    --output table
```

Expected:

```text id="la50"

Role
--------------------------
Virtual Machine User Login
```

---

# The Authorization Chain Is Now Complete

```text id="la51"

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

```text id="la52"

chewbacca@balerica-ai.org
```

Expected:

```text id="la53"

ACCESS GRANTED
```

The important difference is:

```text id="la54"

Gate 5:
User had the role directly.

Gate 6:
Group has the role.
```

---

# Gate 6.12 — Verify the User Has No Direct Role

Run:

```bash id="la55"
az role assignment list \
    --assignee-object-id "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[].roleDefinitionName" \
    --output table
```

There should be no direct:

```text id="la56"

Virtual Machine User Login
```

assignment.

Yet Chewbacca can log in.

Therefore the effective authorization path is:

```text id="la57"

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

```text id="la58"

Bob     -> Server
Alice   -> Server
James   -> Server
Maria   -> Server
Theo    -> Server
```

we use:

```text id="la59"

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

```bash id="la60"
az ad group member remove \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

---

# Gate 6.14 — Verify Removal

Run:

```bash id="la61"
az ad group member check \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

Expected:

```json id="la62"
{
  "value": false
}
```

---

# What Changed?

We did **not** change:

```text id="la63"

GCP VM

Azure Arc

AADLoginForWindows

Azure RBAC Role

Security Group

User Account
```

The only change was:

```text id="la64"

GROUP MEMBERSHIP
```

---

# Current State

```text id="la65"

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

```text id="la66"

ACCESS DENIED
```

Directory membership and authorization changes can require the authentication system to obtain fresh directory and authorization state, so use a new login attempt when validating changes.

---

# The Important Enterprise Lesson

The server's permission did not change.

The group still has:

```text id="la67"

Virtual Machine User Login
```

Chewbacca lost access because:

```text id="la68"

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

```text id="la69"

Server 1

Server 2

Server 3

Server 4

Server 5
```

and remove him individually.

Instead:

```text id="la70"

Remove User
from
Security Group
```

The resource permissions remain attached to the group.

---

# Gate 6.16 — Restore Chewbacca

Add the user back:

```bash id="la71"
az ad group member add \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

Verify:

```bash id="la72"
az ad group member check \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

Expected:

```json id="la73"
{
  "value": true
}
```

---

# Gate 6.17 — Test Login Again

Start another fresh RDP authentication.

Expected:

```text id="la74"

ACCESS GRANTED
```

You have now demonstrated:

```text id="la75"

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

```text id="la76"

GROUP RBAC ASSIGNMENT

Virtual Machine User Login
```

remained unchanged.

That is the point.

---

# Gate 6.18 — Inspect the Final Architecture

## User

```bash id="la77"
az ad user show \
    --id "$USER_UPN" \
    --query "{User:displayName,UPN:userPrincipalName,ObjectId:id}" \
    --output table
```

## Group

```bash id="la78"
az ad group show \
    --group "SEIR_ARC_Users" \
    --query "{Group:displayName,ObjectId:id,Security:securityEnabled}" \
    --output table
```

## Membership

```bash id="la79"
az ad group member check \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

## RBAC

```bash id="la80"
az role assignment list \
    --assignee-object-id "$GROUP_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[].{Role:roleDefinitionName,Scope:scope}" \
    --output table
```

---

# Final Architecture

```text id="la81"

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

```text id="la82"

WHO IS CHEWBACCA?
```

Group membership answers:

```text id="la83"

WHAT TEAM IS CHEWBACCA ON?
```

Azure RBAC answers:

```text id="la84"

WHAT MAY THAT TEAM ACCESS?
```

Azure Arc answers:

```text id="la85"

WHICH EXTERNAL SERVER IS THE RESOURCE?
```

GCP answers:

```text id="la86"

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

```text id="la87"

GCP = COMPUTER
```

## Gate 2

```text id="la88"

ARC = BRIDGE
```

## Gate 3

```text id="la89"

ENTRA = DEVICE IDENTITY
```

## Gate 4

```text id="la90"

ENTRA = USER IDENTITY
```

## Gate 5

```text id="la91"

RBAC = DIRECT USER AUTHORIZATION
```

## Gate 6

```text id="la92"

GROUPS = ENTERPRISE AUTHORIZATION
```

---

# Why Gate 6 Matters

Gate 5 answered:

> Can I give Chewbacca access to this machine?

Gate 6 answers the much more important enterprise question:

> How do I manage access when I have hundreds of Chewbaccas and hundreds of machines?

Answer:

```text id="la93"

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

```text id="la94"

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

```text id="la95"

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

```text id="la96"

MANUAL IMPLEMENTATION
```

Then:

```text id="la97"

AI-ASSISTED IMPLEMENTATION
```

Then students can compare the implementation generated by the tool with the architecture they already built themselves.
