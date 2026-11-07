# SEIR-1 Cross-Cloud IAM Lab

# Gate 7 — Revoke Access and Prove Denial

## Objective

Gate 6 established the enterprise authorization model:

```text
Chewbacca
    |
    | Member Of
    v
SEIR_ARC_Users
    |
    | Azure RBAC
    v
Virtual Machine User Login
    |
    | Scope
    v
seir-crosscloud-01
```

The user can log into the Windows Server hosted in Google Cloud because the **group** has permission.

Gate 7 will remove that permission.

We will deliberately **not**:

```text
Delete the user

Disable the user

Delete the group

Delete the VM

Disconnect Azure Arc

Remove AADLoginForWindows

Modify the GCP firewall

Modify Windows local groups
```

We will change only:

```text
AZURE RBAC
```

---

# The Core Security Principle

Access should be removable independently from identity.

These are different operations:

```text
DELETE IDENTITY
```

versus:

```text
REMOVE AUTHORIZATION
```

For this lab we want:

```text
Identity remains.

Authorization disappears.
```

---

# Starting Architecture

Before Gate 7:

```text
                    MICROSOFT ENTRA
                          |
                          v
                       Chewbacca
                          |
                       MEMBER OF
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

# Gate 7.1 — Verify the User Still Exists

Define the user:

```bash
USER_UPN="chewbacca@balerica-ai.org"
```

Retrieve the user:

```bash
az ad user show \
    --id "$USER_UPN" \
    --query "{Name:displayName,UPN:userPrincipalName,ObjectId:id,Enabled:accountEnabled}" \
    --output table
```

Expected:

```text
Name        UPN                            Enabled
----------  -----------------------------  -------
Chewbacca   chewbacca@balerica-ai.org      True
```

The user should remain:

```text
ENABLED
```

---

# Gate 7.2 — Retrieve the User Object ID

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

---

# Gate 7.3 — Verify the Security Group Still Exists

```bash
az ad group show \
    --group "SEIR_ARC_Users" \
    --query "{Group:displayName,ObjectId:id,Security:securityEnabled}" \
    --output table
```

Expected:

```text
Security = True
```

---

# Gate 7.4 — Retrieve the Group Object ID

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

---

# Gate 7.5 — Verify Chewbacca Is Still a Member

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

This is important.

For this experiment we are **not removing the user from the group**.

We will remove the group's permission instead.

---

# Gate 7.6 — Retrieve the Arc Resource ID

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

Expected structure:

```text
/subscriptions/...
/resourceGroups/SEIR-ARC-RG
/providers/Microsoft.HybridCompute
/machines/seir-crosscloud-01
```

---

# Gate 7.7 — Verify the Existing Permission

Before deleting anything, inspect the role assignment.

Run:

```bash
az role assignment list \
    --assignee-object-id "$GROUP_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[].{Role:roleDefinitionName,Scope:scope,AssignmentId:id}" \
    --output table
```

You should see:

```text
Virtual Machine User Login
```

Microsoft recommends listing the role assignment before deleting it so that you know exactly what will be removed. 

---

# Record the Role Assignment ID

Retrieve only the assignment we intend to remove:

```bash
ROLE_ASSIGNMENT_ID=$(az role assignment list \
    --assignee-object-id "$GROUP_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[?roleDefinitionName=='Virtual Machine User Login'].id | [0]" \
    --output tsv)
```

Verify:

```bash
echo "$ROLE_ASSIGNMENT_ID"
```

You should receive an Azure resource ID resembling:

```text
/subscriptions/...
/providers/Microsoft.Authorization/roleAssignments/...
```

---

# Why Capture the Assignment ID?

We could delete using:

```text
principal
+
role
+
scope
```

But using the specific assignment ID makes the operation more explicit.

We know exactly which authorization object we are deleting.

This is safer than broadly deleting anything that happens to match loosely specified criteria.

---

# Gate 7.8 — Baseline Access Test

Before removing permission, perform one final fresh login.

Completely sign out of any existing Windows session.

Do not merely:

```text
Disconnect RDP
```

Use:

```powershell
logoff
```

or select:

```text
Sign Out
```

from Windows.

Then begin a fresh RDP authentication as:

```text
chewbacca@balerica-ai.org
```

Expected:

```text
ACCESS GRANTED
```

This gives us our final positive baseline.

---

# Why Must We Sign Out?

An already authenticated Windows session is not the same thing as a new authentication request.

We are testing:

```text
CAN THE USER START A NEW SESSION?
```

not:

```text
DOES AN OLD SESSION STILL EXIST?
```

Always use a fresh authentication attempt when testing authorization changes.

---

# Gate 7.9 — Remove the Azure RBAC Permission

Now remove the role assignment.

Using the exact assignment ID:

```bash
az role assignment delete \
    --ids "$ROLE_ASSIGNMENT_ID"
```

Azure RBAC defines removal of the role assignment as the mechanism for removing access to the Azure resource. 

---

# Gate 7.10 — Verify the Role Assignment Is Gone

Run the same query again:

```bash
az role assignment list \
    --assignee-object-id "$GROUP_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[].{Role:roleDefinitionName,Scope:scope}" \
    --output table
```

You should no longer see:

```text
Virtual Machine User Login
```

---

# Perform a Specific Check

```bash
az role assignment list \
    --assignee-object-id "$GROUP_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[?roleDefinitionName=='Virtual Machine User Login']" \
    --output json
```

Expected:

```json
[]
```

That empty array is a successful Gate 7 result.

---

# Architecture After Revocation

We now have:

```text
Chewbacca
    |
    | MEMBER
    v
SEIR_ARC_Users
    |
    X
    |
Virtual Machine User Login
```

The user still belongs to the group.

The group still exists.

But:

```text
GROUP HAS NO LOGIN PERMISSION
```

---

# Gate 7.11 — Verify There Is No Direct User Assignment

This matters because a direct assignment would bypass our group removal.

Run:

```bash
az role assignment list \
    --assignee-object-id "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --include-inherited \
    --query "[].{Role:roleDefinitionName,Scope:scope}" \
    --output table
```

Verify that the user does not have:

```text
Virtual Machine User Login
```

or:

```text
Virtual Machine Administrator Login
```

directly.

---

# Effective Authorization Model

We now want:

```text
DIRECT USER LOGIN ROLE

NONE
```

and:

```text
GROUP LOGIN ROLE

NONE
```

Therefore:

```text
EFFECTIVE LOGIN AUTHORIZATION

NONE
```

---

# Gate 7.12 — Verify the VM Is Still Healthy

Now prove that we changed authorization only.

## GCP

```bash
gcloud compute instances describe seir-crosscloud-01 \
    --zone=us-central1-a \
    --format="table(name,status)"
```

Expected:

```text
RUNNING
```

---

# Gate 7.13 — Verify Azure Arc Is Still Healthy

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

# Gate 7.14 — Verify AADLoginForWindows Still Exists

```bash
az connectedmachine extension show \
    --resource-group SEIR-ARC-RG \
    --machine-name seir-crosscloud-01 \
    --name AADLoginForWindows \
    --query provisioningState \
    --output tsv
```

Expected:

```text
Succeeded
```

---

# Notice What Has NOT Changed

```text
GCP VM                         RUNNING

Azure Arc                     CONNECTED

AADLoginForWindows            SUCCEEDED

Entra Device                  EXISTS

Entra User                    EXISTS

Security Group                EXISTS

Group Membership              EXISTS
```

Only:

```text
Azure RBAC Login Role         REMOVED
```

---

# Gate 7.15 — Attempt a Fresh Login

Completely close any old RDP session.

Start:

```powershell
mstsc.exe
```

Authenticate again using the Entra identity.

Expected:

```text
ACCESS DENIED
```

Microsoft requires either:

```text
Virtual Machine User Login
```

or:

```text
Virtual Machine Administrator Login
```

for Entra sign-in to an Arc-enabled Windows Server. Without either role, the user is not authorized to start the Windows session.

---

# Expected Error

A common error is:

```text
Your account is configured to prevent you
from using this device.
```

For this architecture, that is a useful error.

It means:

```text
Authentication reached the server

BUT

Authorization was denied
```

Microsoft specifically lists missing VM login roles as a cause of this sign-in failure.

---

# Gate 7.16 — Understand the Result

Microsoft Entra can still answer:

```text
Who are you?
```

with:

```text
Chewbacca
```

But Azure RBAC now answers:

```text
May Chewbacca's group log into this machine?
```

with:

```text
NO
```

Therefore:

```text
AUTHENTICATION

PASS
```

but:

```text
AUTHORIZATION

FAIL
```

That is the desired result.

---

# Revocation Model

Before:

```text
Chewbacca
    |
    v
SEIR_ARC_Users
    |
    v
Virtual Machine User Login
    |
    v
Server

ACCESS
```

After:

```text
Chewbacca
    |
    v
SEIR_ARC_Users
    |
    X
    |
Server

DENIED
```

---

# Gate 7.17 — Two Different Types of Revocation

There are actually two different enterprise operations.

## Remove One Person

If only Chewbacca should lose access:

```bash
az ad group member remove \
    --group "SEIR_ARC_Users" \
    --member-id "$USER_OBJECT_ID"
```

The group's server permissions remain intact.

Conceptually:

```text
EMPLOYEE OFFBOARDING

User
 |
 X
 |
Group
 |
 v
Resource
```

---

## Remove the Entire Group's Access

What we performed in this Gate:

```text
SERVICE / PERMISSION DECOMMISSIONING

Users
 |
 v
Group
 |
 X
 |
Resource
```

The group exists, but it no longer has permission to the server.

---

# Choosing the Correct Revocation

Use:

```text
REMOVE USER FROM GROUP
```

when:

```text
One person should lose access.
```

Use:

```text
REMOVE RBAC ROLE FROM GROUP
```

when:

```text
The entire team's permission should disappear.
```

---

# Gate 7.18 — Emergency User Revocation

There is another situation:

```text
COMPROMISED ACCOUNT
```

or:

```text
EMPLOYEE TERMINATED
```

In that case, merely removing one infrastructure role may not be sufficient.

Organizations might also disable the user's Entra account.

For example:

```bash
az ad user update \
    --id "$USER_UPN" \
    --account-enabled false
```

That is **not part of our normal Gate 7 workflow**.

Why?

Because:

```text
Removing authorization
```

and:

```text
Disabling identity
```

are different security operations.

We want students to understand both.

Microsoft notes that when an employee's Entra account is disabled or removed, they can no longer use that account to access Arc-enabled Windows resources.

---

# Gate 7.19 — Do NOT Delete the User

For this lab:

```text
DO NOT DELETE CHEWBACCA
```

We still want the identity to exist.

The objective is:

```text
PROVE ACCESS CAN BE REVOKED
```

not:

```text
DESTROY THE IDENTITY
```

---

# Gate 7.20 — Do NOT Touch Windows Local Groups

Do not use:

```powershell
net localgroup administrators
```

Do not use:

```powershell
net localgroup "Remote Desktop Users"
```

Do not manually remove AzureAD users from Windows groups.

The supported Arc authentication model uses Azure RBAC for authorization. Microsoft explicitly says manually elevating Entra users through the Windows local Administrators group isn't the supported authorization model for this feature.

---

# Gate 7.21 — Do NOT Remove AADLoginForWindows

Leave:

```text
AADLoginForWindows
```

installed.

Why?

Because the machine should remain capable of Entra authentication.

We are only saying:

```text
Nobody in SEIR_ARC_Users currently has permission
to use that authentication path.
```

---

# Gate 7.22 — Do NOT Disconnect Azure Arc

Leave:

```text
azcmagent
```

connected.

Azure should still report:

```text
Connected
```

The bridge remains.

Only authorization changes.

---

# Gate 7 Final Architecture

```text
                       MICROSOFT ENTRA
                              |
                  +-----------+-----------+
                  |                       |
                  v                       v

              Chewbacca             Device Identity
                  |                       |
                MEMBER                    |
                  |                       |
                  v                       |
           SEIR_ARC_Users                 |
                  |                       |
                  X                       |
             NO LOGIN ROLE                |
                  |                       |
                  +-----------+-----------+
                              |
                              v
                          AZURE ARC
                              |
                              v
                    Windows Server 2025
                              |
                              v
                              GCP
```

---

# Gate 7 Verification Commands

## User Exists

```bash
az ad user show \
    --id "$USER_UPN" \
    --query "{UPN:userPrincipalName,Enabled:accountEnabled}" \
    --output table
```

Expected:

```text
Enabled = True
```

---

## Group Exists

```bash
az ad group show \
    --group "SEIR_ARC_Users" \
    --query "{Name:displayName,Security:securityEnabled}" \
    --output table
```

Expected:

```text
Security = True
```

---

## Membership Still Exists

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

## Group Login Role

```bash
az role assignment list \
    --assignee-object-id "$GROUP_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[?roleDefinitionName=='Virtual Machine User Login']" \
    --output json
```

Expected:

```json
[]
```

---

## Direct User Login Roles

```bash
az role assignment list \
    --assignee-object-id "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --include-inherited \
    --query "[?roleDefinitionName=='Virtual Machine User Login' || roleDefinitionName=='Virtual Machine Administrator Login']" \
    --output json
```

Expected:

```json
[]
```

---

## GCP

```bash
gcloud compute instances describe seir-crosscloud-01 \
    --zone=us-central1-a \
    --format="get(status)"
```

Expected:

```text
RUNNING
```

---

## Azure Arc

```bash
az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query status \
    --output tsv
```

Expected:

```text
Connected
```

---

## Extension

```bash
az connectedmachine extension show \
    --resource-group SEIR-ARC-RG \
    --machine-name seir-crosscloud-01 \
    --name AADLoginForWindows \
    --query provisioningState \
    --output tsv
```

Expected:

```text
Succeeded
```

---

# Gate 7 Success Criteria

Gate 7 is complete when:

- [ ] The Entra user still exists.
- [ ] The Entra user remains enabled.
- [ ] `SEIR_ARC_Users` still exists.
- [ ] Chewbacca remains a member of `SEIR_ARC_Users`.
- [ ] The group no longer has `Virtual Machine User Login`.
- [ ] The user has no direct VM login assignment.
- [ ] The user has no inherited VM login assignment.
- [ ] GCP reports the VM as `RUNNING`.
- [ ] Azure Arc reports `Connected`.
- [ ] `AADLoginForWindows` remains `Succeeded`.
- [ ] A completely new RDP authentication attempt is denied.
- [ ] No local Windows security groups were modified.
- [ ] No identity was deleted.

---

# Final Gate 7 State

```text
COMPUTE                       HEALTHY

NETWORK                       HEALTHY

AZURE ARC                     HEALTHY

ENTRA DEVICE                  HEALTHY

ENTRA USER                    HEALTHY

GROUP                         HEALTHY

AUTHENTICATION PATH           HEALTHY

AUTHORIZATION                 REMOVED
```

That is exactly what we want.

---

# Gate 7 Mental Model

Gate 1:

```text
BUILD THE COMPUTER
```

Gate 2:

```text
BUILD THE BRIDGE
```

Gate 3:

```text
IDENTIFY THE COMPUTER
```

Gate 4:

```text
IDENTIFY THE HUMAN
```

Gate 5:

```text
GRANT THE HUMAN ACCESS
```

Gate 6:

```text
MANAGE ACCESS THROUGH GROUPS
```

Gate 7:

```text
REVOKE ACCESS WITHOUT BREAKING ANYTHING
```

---

# The Enterprise Lesson

A mature IAM system should allow:

```text
ACCESS ON
```

and:

```text
ACCESS OFF
```

without rebuilding:

```text
Users

Servers

Networks

Operating systems

Cloud infrastructure
```

Authorization should be a controllable relationship.

For this lab:

```text
IDENTITY       remains

DEVICE         remains

COMPUTE        remains

ARC            remains

RBAC           changes
```

That is the point of Gate 7.
