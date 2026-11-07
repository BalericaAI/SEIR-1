# SEIR-1 Cross-Cloud IAM Lab

# Gate 5 — Authorize the Entra User to Log Into the GCP VM

## Objective

We have reached the authorization stage.

At the end of Gate 4:

```text
COMPUTER EXISTS          YES
AZURE ARC CONNECTED      YES
DEVICE IN ENTRA          YES
USER IN ENTRA            YES
USER CAN LOG INTO VM     NO
```

That last result was intentional.

Gate 5 changes exactly one thing:

```text
AZURE RBAC AUTHORIZATION
```

We will assign:

```text
Virtual Machine User Login
```

to:

```text
chewbacca@balerica-ai.org
```

at the scope of:

```text
seir-crosscloud-01
```

Then we will prove that the user can sign into a Windows Server physically running in Google Cloud.

---

# The IAM Formula Returns

Remember:

```text
PRINCIPAL
+
ROLE
+
SCOPE
=
ACCESS
```

For this lab:

```text
PRINCIPAL

Chewbacca
chewbacca@balerica-ai.org
```

plus:

```text
ROLE

Virtual Machine User Login
```

plus:

```text
SCOPE

seir-crosscloud-01
```

equals:

```text
AUTHORIZED WINDOWS LOGIN
```

---

# Before Gate 5

Our architecture currently looks like:

```text
                   MICROSOFT ENTRA ID
                          |
            +-------------+-------------+
            |                           |
            v                           v

      Device Identity              User Identity
   seir-crosscloud-01               Chewbacca
            |                           |
            |                           X
            |                      NO LOGIN ROLE
            |                           |
            +-------------+-------------+
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

Authentication works.

Authorization does not.

---

# Gate 5.1 — Run the Gates 1–4 Verifier

Before changing anything:

```bash
python 1-4-verify_all_gates.py \
  --user-upn chewbacca@balerica-ai.org
```

Gate 4 should report:

```text
[PASS] No VM login role assigned yet
```

This is our known-good **before state**.

Do not proceed if earlier gates are failing.

---

# Gate 5.2 — Define the User

From your workstation:

## Bash / Git Bash

```bash
USER_UPN="chewbacca@balerica-ai.org"
```

Retrieve the user's Entra Object ID:

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

Expected:

```text
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

# Gate 5.3 — Retrieve the Arc Resource ID

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

This resource ID becomes our RBAC scope.

---

# Why Use the Individual Server as Scope?

Azure roles can be assigned at several levels:

```text
Management Group

Subscription

Resource Group

Individual Resource
```

For this lab, we use:

```text
Individual Resource
```

because we want the students to see exactly what is happening.

```text
Chewbacca

may access

ONE SERVER
```

not:

```text
every Arc server
```

This is an excellent demonstration of least privilege.

---

# Gate 5.4 — Verify the Login Role Exists

Run:

```bash
az role definition list \
    --name "Virtual Machine User Login" \
    --query "[].{RoleName:roleName,RoleType:roleType}" \
    --output table
```

Expected:

```text
RoleName                    RoleType
--------------------------  ---------
Virtual Machine User Login  BuiltInRole
```

Microsoft provides two dedicated login roles:

```text
Virtual Machine User Login
```

and:

```text
Virtual Machine Administrator Login
```

The first creates a normal Windows user session.

The second grants administrative privileges.

For this lab:

```text
Virtual Machine User Login
```

is enough.

---

# Important

Do not assign:

```text
Virtual Machine Administrator Login
```

merely because it is easier.

We are demonstrating:

```text
LEAST PRIVILEGE
```

not:

```text
EVERYONE IS DOMAIN EMPEROR
```

---

# Gate 5.5 — Verify the Student Can Create Role Assignments

The account running the next command requires permission for:

```text
Microsoft.Authorization/roleAssignments/write
```

An appropriate Azure RBAC administration role can provide that permission.

If the command returns:

```text
AuthorizationFailed
```

do not troubleshoot:

```text
Entra

Windows

GCP

RDP
```

The administrator performing the lab simply lacks permission to create the RBAC assignment. Microsoft documents role-assignment write permission as a prerequisite for assigning Azure roles.

---

# Gate 5.6 — Assign Virtual Machine User Login

Now make the authorization change.

Run:

```bash
az role assignment create \
    --assignee-object-id "$USER_OBJECT_ID" \
    --assignee-principal-type User \
    --role "Virtual Machine User Login" \
    --scope "$ARC_RESOURCE_ID"
```

Azure should return a role assignment.

Conceptually:

```text
Chewbacca
      |
      | Azure RBAC
      |
      v
Virtual Machine User Login
      |
      | Scope
      v
seir-crosscloud-01
```

Microsoft supports `--assignee-object-id`, `--assignee-principal-type`, role, and scope as the explicit components of an Azure CLI role assignment.

---

# Gate 5.7 — Verify the Assignment

Run:

```bash
az role assignment list \
    --assignee-object-id "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --include-inherited \
    --query "[].{Role:roleDefinitionName,Scope:scope}" \
    --output table
```

You should now see:

```text
Role                        Scope
--------------------------  -----------------------------------
Virtual Machine User Login  .../machines/seir-crosscloud-01
```

This is the crucial state transition.

---

# Before

```text
Chewbacca
+
NO LOGIN ROLE
+
seir-crosscloud-01

=

ACCESS DENIED
```

# After

```text
Chewbacca
+
Virtual Machine User Login
+
seir-crosscloud-01

=

ACCESS AUTHORIZED
```

---

# Gate 5.8 — Verify the Rest of the Architecture Did Not Change

GCP:

```bash
gcloud compute instances describe seir-crosscloud-01 \
    --zone=us-central1-a \
    --format="table(name,status)"
```

Expected:

```text
RUNNING
```

Azure Arc:

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

Extension:

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

Nothing changed except RBAC.

---

# Gate 5.9 — Choose the RDP Authentication Method

Microsoft currently supports two useful approaches.

For this lab, the recommended classroom approach is:

```text
WEB ACCOUNT SIGN-IN
```

Why?

Because the workstation does not itself have to be Entra joined or registered when using the web-account RDP flow.

Microsoft specifically supports this method for Windows Server 2025 Arc-enabled servers.

---

# PATH A — Recommended

# Passwordless / Web Account RDP

This requires a Windows RDP client using:

```text
mstsc.exe
```

The remote computer must be accessed by its **hostname**.

You cannot use the IP address for web-account sign-in.

Microsoft requires the name to match the hostname represented in Microsoft Entra and resolve to the server's IP address.

---

# Gate 5.10 — Determine the Actual Windows Hostname

Do not guess.

Inside the server:

```powershell
hostname
```

Also inspect:

```powershell
dsregcmd /status
```

Use the device name that actually appears in Microsoft Entra.

For example:

```text
SEIR-CROSSCLD01
```

Use your actual value in the remaining commands.

---

# Gate 5.11 — Retrieve the GCP External IP

From the workstation:

```bash
gcloud compute instances describe seir-crosscloud-01 \
    --zone=us-central1-a \
    --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
```

Example:

```text
34.xxx.xxx.xxx
```

---

# Gate 5.12 — Ensure the Hostname Resolves

From a Windows workstation:

```powershell
Resolve-DnsName SEIR-CROSSCLD01
```

If your environment already resolves the hostname correctly, continue.

If not, for a temporary lab-only test you can add a local hosts-file entry.

Run PowerShell as Administrator:

```powershell
$VMIP = "34.xxx.xxx.xxx"
$VMHOST = "SEIR-CROSSCLD01"

Add-Content `
    -Path "C:\Windows\System32\drivers\etc\hosts" `
    -Value "$VMIP`t$VMHOST"
```

Verify:

```powershell
Resolve-DnsName $VMHOST
```

or:

```powershell
ping $VMHOST
```

The hostname should resolve to the GCP VM.

---

# Why Can't We Use the IP Address?

With web-account Entra authentication:

```text
34.xxx.xxx.xxx
```

is not sufficient.

The authentication relationship is built around the device identity.

Microsoft requires the remote name to correspond to the hostname of the device in Entra.

This is another important distinction:

```text
NETWORK DESTINATION
```

is not the same concept as:

```text
DEVICE IDENTITY
```

---

# Gate 5.13 — Launch Remote Desktop

Run:

```powershell
mstsc.exe
```

Before connecting:

```text
Show Options
```

Then:

```text
Advanced
```

Enable:

```text
Use a web account to sign in to the remote computer
```

---

# Gate 5.14 — Enter the Computer Name

Enter the hostname:

```text
SEIR-CROSSCLD01
```

Do not enter:

```text
34.xxx.xxx.xxx
```

for this authentication path.

Click:

```text
Connect
```

---

# Gate 5.15 — Authenticate With Microsoft Entra

When the browser authentication appears, sign in as:

```text
chewbacca@balerica-ai.org
```

Use the user's normal Microsoft Entra authentication method.

Microsoft supports passwordless Entra credentials including methods such as FIDO2/passkeys where configured.

---

# Gate 5.16 — Successful Login

If everything is configured correctly:

```text
Microsoft Entra
       |
       | Authenticate
       v
Chewbacca
       |
       | Azure RBAC
       v
Virtual Machine User Login
       |
       | Scope
       v
Azure Arc Resource
       |
       v
Windows Server
       |
       v
GCP
```

You should receive a Windows desktop session.

---

# Gate 5.17 — Prove Who You Are

Inside the remote Windows session:

```powershell
whoami
```

Then:

```powershell
whoami /user
```

And:

```powershell
whoami /groups
```

Also run:

```powershell
$env:USERNAME
```

The important point is that you are no longer using:

```text
seir-local-admin
```

You are using the Microsoft Entra-authorized identity.

---

# Gate 5.18 — Prove You Are NOT an Administrator

Because we assigned:

```text
Virtual Machine User Login
```

rather than:

```text
Virtual Machine Administrator Login
```

the session should not automatically have local administrative privileges.

Try:

```powershell
net session
```

A standard user normally receives an access-denied response.

That is a good result.

Remember:

```text
LOGIN ACCESS
```

does not mean:

```text
ADMINISTRATOR ACCESS
```

---

# PATH B — Password-Based Entra RDP

Microsoft also supports traditional password-based RDP.

However, the initiating Windows computer must be appropriately:

```text
Microsoft Entra joined

or

Microsoft Entra hybrid joined

or

Microsoft Entra registered
```

to the same directory.

For an Entra-registered client, use:

```text
AzureAD\chewbacca@balerica-ai.org
```

as the username.

Microsoft documents these client-device requirements for conventional Entra RDP authentication.

For a heterogeneous classroom, Path A is usually simpler.

---

# Gate 5.19 — The Authorization Proof

Now inspect the role assignment again:

```bash
az role assignment list \
    --assignee-object-id "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --include-inherited \
    --query "[].{Role:roleDefinitionName,Scope:scope}" \
    --output table
```

You should see:

```text
Virtual Machine User Login
```

And we have independently proven:

```text
RDP LOGIN SUCCEEDED
```

Therefore:

```text
IDENTITY
+
ROLE
+
SCOPE
=
ACCESS
```

has been demonstrated.

---

# Gate 5.20 — The Sith Test

Now remove the user's permission.

Run:

```bash
az role assignment delete \
    --assignee-object-id "$USER_OBJECT_ID" \
    --role "Virtual Machine User Login" \
    --scope "$ARC_RESOURCE_ID"
```

Verify:

```bash
az role assignment list \
    --assignee-object-id "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --include-inherited \
    --query "[].roleDefinitionName" \
    --output table
```

`Virtual Machine User Login` should no longer appear.

---

# Gate 5.21 — Attempt the Login Again

Disconnect the existing RDP session completely.

Do not merely lock it.

Start a new authentication attempt.

Expected:

```text
ACCESS DENIED
```

A common Microsoft error in this state is conceptually:

```text
Your account is configured to prevent you
from using this device.
```

Microsoft specifically associates that failure with a missing VM login role.

---

# What Just Happened?

We did not:

```text
Delete Chewbacca

Disable Chewbacca

Delete the VM

Remove the device from Entra

Disconnect Azure Arc

Uninstall AADLoginForWindows

Change the GCP firewall

Change the password
```

We changed only:

```text
Azure RBAC
```

And access disappeared.

---

# Gate 5.22 — Restore the Role

Reassign it:

```bash
az role assignment create \
    --assignee-object-id "$USER_OBJECT_ID" \
    --assignee-principal-type User \
    --role "Virtual Machine User Login" \
    --scope "$ARC_RESOURCE_ID"
```

Verify:

```bash
az role assignment list \
    --assignee-object-id "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --query "[].roleDefinitionName" \
    --output table
```

Expected:

```text
Virtual Machine User Login
```

---

# Gate 5.23 — Final Login Test

Start a new RDP connection.

Authenticate again.

Expected:

```text
ACCESS GRANTED
```

The student has now demonstrated:

```text
ROLE PRESENT
     |
     v
LOGIN ALLOWED


ROLE REMOVED
     |
     v
LOGIN DENIED


ROLE RESTORED
     |
     v
LOGIN ALLOWED
```

This is Azure RBAC operating as an authorization system.

---

# Final Architecture

```text
                         MICROSOFT ENTRA ID
                                |
                                |
                         Chewbacca Identity
                                |
                         AUTHENTICATION
                                |
                                v
                           AZURE RBAC
                                |
                  Virtual Machine User Login
                                |
                              SCOPE
                                |
                                v
                           AZURE ARC
                                |
                    Arc Resource Representation
                                |
                                v
                     AADLoginForWindows
                                |
                                v
                      Windows Server 2025
                                |
                                v
                       GOOGLE CLOUD PLATFORM
```

---

# Control Plane Separation

Notice who controls each layer.

```text
GCP
|
+-- VM
+-- CPU
+-- RAM
+-- Disk
+-- VPC
+-- Firewall
+-- External IP
```

```text
Azure Arc
|
+-- External server representation
+-- Extensions
+-- Management relationship
```

```text
Microsoft Entra
|
+-- User identity
+-- Device identity
+-- Authentication
```

```text
Azure RBAC
|
+-- Authorization
```

---

# The Important Enterprise Lesson

This is why:

```text
Owner
```

does not mean:

```text
I may log into the operating system.
```

And:

```text
Contributor
```

does not mean:

```text
I may log into the operating system.
```

Microsoft deliberately separates:

```text
CONTROL PLANE ACCESS
```

from:

```text
OPERATING SYSTEM LOGIN ACCESS
```

The dedicated login roles create an auditable separation between people who manage infrastructure and people who may enter the operating system.

---

# Gate 5 Success Criteria

Gate 5 is complete when:

- [ ] Gates 1–4 still pass.
- [ ] The Entra user Object ID is known.
- [ ] The Arc resource ID is known.
- [ ] `Virtual Machine User Login` exists.
- [ ] The role is assigned at the Arc machine scope.
- [ ] The assignment can be verified with Azure CLI.
- [ ] The GCP VM remains `RUNNING`.
- [ ] Azure Arc remains `Connected`.
- [ ] `AADLoginForWindows` remains `Succeeded`.
- [ ] The user successfully authenticates with Entra.
- [ ] The user successfully reaches a Windows session.
- [ ] The session is a normal user session.
- [ ] Removing the RBAC role prevents a new login.
- [ ] Restoring the RBAC role restores login access.

---

# Failure Gate — Authentication Works, Login Denied

If Microsoft accepts the identity but Windows reports that the account isn't permitted to use the device, check:

```bash
az role assignment list \
    --assignee-object-id "$USER_OBJECT_ID" \
    --scope "$ARC_RESOURCE_ID" \
    --include-inherited \
    --output table
```

You need:

```text
Virtual Machine User Login
```

or:

```text
Virtual Machine Administrator Login
```

Microsoft identifies absence of these roles as a primary cause of the "account configured to prevent you from using this device" error.

---

# Failure Gate — Credentials Didn't Work

Check:

```text
Temporary password already changed?
```

Then:

```text
Correct tenant?
```

Then:

```text
UserType = Member?
```

Then:

```text
AADLoginForWindows = Succeeded?
```

Then:

```powershell
dsregcmd /status
```

Look for:

```text
AzureAdJoined : YES
```

Microsoft does not support temporary passwords for this RDP scenario.

---

# Failure Gate — Web Account Cannot Find the Computer

Remember:

```text
Web Account Sign-In
```

cannot use:

```text
34.xxx.xxx.xxx
```

Use the hostname registered with Entra.

Verify:

```powershell
Resolve-DnsName YOUR_HOSTNAME
```

The name must resolve to the GCP VM's IP.

---

# Final Mental Model

Gate 1:

```text
GCP = COMPUTER
```

Gate 2:

```text
ARC = BRIDGE
```

Gate 3:

```text
ENTRA = DEVICE IDENTITY
```

Gate 4:

```text
ENTRA = HUMAN IDENTITY
```

Gate 5:

```text
RBAC = PERMISSION
```

Together:

```text
                     WHO ARE YOU?
                          |
                        ENTRA
                          |
                          v
                  WHAT MAY YOU DO?
                          |
                         RBAC
                          |
                          v
                 WHERE MAY YOU DO IT?
                          |
                      AZURE ARC
                          |
                          v
                 WHERE IS IT RUNNING?
                          |
                          GCP
```

# Final Result

> A Microsoft Entra user has been authorized through Azure RBAC to interactively sign into a Windows Server 2025 machine physically hosted in Google Cloud Platform.
