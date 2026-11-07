# SEIR-1 Cross-Cloud IAM Lab

# Gate 3 — Enable Microsoft Entra Authentication on the GCP VM

## Objective

In Gate 2, the GCP-hosted Windows Server was onboarded to Azure Arc.

You currently have:

```text
Google Cloud
     |
     v
Windows Server 2025
     |
     | Azure Connected Machine Agent
     v
Azure Arc
     |
     v
System-Assigned Managed Identity
```

In Gate 3, you will enable **Microsoft Entra authentication** on that Arc-enabled Windows Server.

At the end of this gate:

```text
Google Cloud
     |
     v
Windows Server 2025
     |
     v
Azure Arc
     |
     v
AADLoginForWindows
     |
     v
Microsoft Entra ID
     |
     v
AzureAdJoined = YES
```

No human user will be authorized to log in yet.

That occurs in a later gate.

---

# Important Concept

Gate 2 created an Azure representation of the server.

Gate 3 creates the **device identity relationship with Microsoft Entra ID**.

Think:

```text
Gate 2:

Does Azure know this server exists?

YES
```

Now:

```text
Gate 3:

Does Microsoft Entra recognize this server as a joined device?

NOT YET
```

Our goal is:

```text
AzureAdJoined : YES
```

---

# Gate 3.1 — Verify the VM Is Still Healthy in GCP

From your workstation:

```bash
gcloud compute instances describe seir-crosscloud-01 \
    --zone=us-central1-a \
    --format="table(name,status,zone)"
```

Expected:

```text
NAME                  STATUS    ZONE
seir-crosscloud-01    RUNNING   us-central1-a
```

If GCP does not report:

```text
RUNNING
```

stop here.

---

# Gate 3.2 — Verify Azure Arc Status

From your workstation:

```bash
az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query "{Name:name,Status:status,Location:location}" \
    --output table
```

Expected:

```text
Name                  Status       Location
--------------------  -----------  --------
seir-crosscloud-01    Connected    eastus
```

If Azure Arc does not report:

```text
Connected
```

stop here.

Gate 2 is not complete.

---

# Gate 3.3 — Verify the Machine Managed Identity

The Microsoft Entra login extension requires the Arc server to have a **system-assigned managed identity**.

Run:

```bash
az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query identity \
    --output json
```

You should see values similar to:

```json
{
  "principalId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "type": "SystemAssigned"
}
```

The important value is:

```text
type = SystemAssigned
```

---

# Machine Identity vs Device Join

Do not confuse these concepts.

The system-assigned managed identity represents:

```text
THE MACHINE WHEN IT TALKS TO AZURE
```

The Entra device join represents:

```text
THE WINDOWS DEVICE INSIDE MICROSOFT ENTRA
```

After Gate 3, both will exist.

Conceptually:

```text
Microsoft Entra ID
       |
       +---- Managed Identity
       |         |
       |         v
       |    Azure Arc Agent
       |
       +---- Device Identity
                 |
                 v
           Windows Server
```

---

# Gate 3.4 — Verify No Entra Login Extension Exists Yet

From your workstation:

```bash
az connectedmachine extension list \
    --machine-name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --output table
```

You should not yet see:

```text
AADLoginForWindows
```

This is our before-state.

---

# Gate 3.5 — Verify Required Network Connectivity

RDP into the GCP Windows Server using:

```text
seir-local-admin
```

Open **PowerShell as Administrator**.

Test Microsoft authentication:

```powershell
Test-NetConnection `
    login.microsoftonline.com `
    -Port 443
```

Expected:

```text
TcpTestSucceeded : True
```

Test device registration:

```powershell
Test-NetConnection `
    enterpriseregistration.windows.net `
    -Port 443
```

Expected:

```text
TcpTestSucceeded : True
```

Test Azure authorization services:

```powershell
Test-NetConnection `
    pas.windows.net `
    -Port 443
```

Expected:

```text
TcpTestSucceeded : True
```

Microsoft requires outbound HTTPS connectivity to these services for Entra authentication on Arc-enabled Windows Servers.

---

# Gate 3.6 — Verify the Arc Instance Metadata Service

Azure Arc exposes a local metadata service on:

```text
localhost:40342
```

Run:

```powershell
curl.exe `
    -H Metadata:true `
    "http://localhost:40342/metadata/instance?api-version=2017-08-01"
```

You should receive metadata describing the Arc-enabled server.

---

# Gate 3.7 — Verify the Managed Identity Through HIMDS

Run:

```powershell
curl.exe `
    -H Metadata:true `
    "http://localhost:40342/metadata/identity/info?api-version=2018-02-01"
```

You should receive identity information including a tenant ID.

This proves:

```text
Windows Server
      |
      v
HIMDS
      |
      v
System-Assigned Managed Identity
      |
      v
Microsoft Entra Tenant
```

Microsoft specifically recommends these local metadata checks when troubleshooting `AADLoginForWindows`.

---

# Gate 3.8 — Install the Microsoft Entra Login Extension

Return to your normal workstation.

Use Azure CLI.

Run:

```bash
az connectedmachine extension create \
    --resource-group SEIR-ARC-RG \
    --machine-name seir-crosscloud-01 \
    --location eastus \
    --publisher Microsoft.Azure.ActiveDirectory \
    --type AADLoginForWindows \
    --name AADLoginForWindows \
    --settings '{"mdmId":""}'
```

The `mdmId` property is required for the Arc version of the extension.

Its value may remain empty:

```json
{
  "mdmId": ""
}
```

Microsoft's current Arc documentation explicitly requires this setting for `AADLoginForWindows`.

---

# What Is Happening?

The command causes Azure Arc to deliver an extension to the GCP server.

Conceptually:

```text
Student Workstation
       |
       | Azure CLI
       v
Azure Resource Manager
       |
       v
Azure Arc
       |
       | Extension Deployment
       v
Azure Connected Machine Agent
       |
       v
Windows Server 2025
       |
       v
AADLoginForWindows
```

Notice:

```text
The command is issued through Azure.
```

but:

```text
The software is installed on a VM physically running in GCP.
```

This is exactly what Azure Arc is designed to do.

---

# Gate 3.9 — Verify Extension Deployment

From your workstation:

```bash
az connectedmachine extension show \
    --resource-group SEIR-ARC-RG \
    --machine-name seir-crosscloud-01 \
    --name AADLoginForWindows \
    --output json
```

Look for:

```text
provisioningState
```

The desired result is:

```text
Succeeded
```

For cleaner output:

```bash
az connectedmachine extension show \
    --resource-group SEIR-ARC-RG \
    --machine-name seir-crosscloud-01 \
    --name AADLoginForWindows \
    --query "{Name:name,State:provisioningState,Type:properties.type}" \
    --output table
```

Expected conceptually:

```text
Name                 State       Type
-------------------  ----------  ------------------
AADLoginForWindows   Succeeded   AADLoginForWindows
```

Microsoft documents `Succeeded` as the expected provisioning state after successful installation.

---

# Gate 3.10 — Verify Locally on Windows

RDP back into:

```text
seir-crosscloud-01
```

using the local administrator account.

Run:

```powershell
dsregcmd /status
```

Find:

```text
Device State
```

The important result is:

```text
AzureAdJoined : YES
```

Microsoft identifies this as the target state for the Arc-enabled server after the extension completes the Entra join.

---

# Expected Device State

You may see something conceptually similar to:

```text
+----------------------------------------------------------------------+
| Device State                                                         |
+----------------------------------------------------------------------+

AzureAdJoined : YES
EnterpriseJoined : NO
DomainJoined : NO
```

For this lab, the critical value is:

```text
AzureAdJoined : YES
```

---

# Traditional AD Is NOT Required

The server does not need to be joined to:

```text
Active Directory Domain Services
```

for this lab.

The intended architecture is:

```text
DomainJoined     : NO

AzureAdJoined    : YES
```

Microsoft specifically describes this scenario for machines that are **not intended to join another domain**, such as traditional AD DS.

---

# Gate 3.11 — Record the Device ID

Inside the output of:

```powershell
dsregcmd /status
```

look for:

```text
DeviceId
```

Record it.

Example:

```text
DeviceId : xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

This is the Microsoft Entra device identity.

---

# Gate 3.12 — Verify the Device in Microsoft Entra

You can verify the device through:

```text
Microsoft Entra Admin Center
        |
        v
Entra ID
        |
        v
Devices
        |
        v
All Devices
```

Look for:

```text
seir-crosscloud-01
```

The device should show a Microsoft Entra join relationship.

---

# Optional — Verify with Azure CLI

From your workstation:

```bash
az ad device list \
    --filter "displayName eq 'seir-crosscloud-01'" \
    --output table
```

If the Windows hostname appears differently, first verify it inside the server:

```powershell
hostname
```

Use the actual hostname in your query.

---

# Optional — Verify with Microsoft Graph PowerShell

If Microsoft Graph PowerShell is installed:

```powershell
Connect-MgGraph -Scopes "Device.Read.All"
```

Then:

```powershell
Get-MgDevice `
    -Filter "displayName eq 'seir-crosscloud-01'" |
    Select-Object `
        DisplayName,
        DeviceId,
        Id
```

Compare:

```text
DeviceId from Entra
```

with:

```text
DeviceId from dsregcmd /status
```

They should represent the same device.

---

# Gate 3.13 — Verify the Extension Locally

You can inspect extension logs on the Windows Server.

Microsoft documents the extension log location under:

```text
C:\WindowsAzure\Logs\Plugins\
Microsoft.Azure.ActiveDirectory\
AADLoginForWindows\
```

If installation succeeded, you normally do not need to troubleshoot these logs.

If it failed, they become important.

---

# Gate 3.14 — Verify the Full Device Chain

At this point you should be able to prove all four layers:

```text
GCP
 |
 | Compute
 v
Windows Server 2025
 |
 | Connected Machine Agent
 v
Azure Arc
 |
 | AADLoginForWindows
 v
Microsoft Entra ID
 |
 v
Device Identity
```

---

# What We Have NOT Done Yet

We have not granted any human permission to log into this server.

This is intentional.

Right now:

```text
DEVICE IDENTITY
      |
      v
COMPLETE
```

but:

```text
USER AUTHORIZATION
      |
      v
NOT CONFIGURED
```

---

# Important IAM Concept

A device existing in Microsoft Entra does **not** automatically mean that an Entra user may log into it.

These are separate questions.

Question 1:

```text
Who is the computer?
```

Answer:

```text
Microsoft Entra Device Identity
```

Question 2:

```text
Who is the human?
```

Answer:

```text
Microsoft Entra User Identity
```

Question 3:

```text
May that human log into this computer?
```

Answer:

```text
Azure RBAC
```

Gate 3 answers only Question 1.

---

# Final Gate 3 Architecture

```text
                       MICROSOFT ENTRA ID
                              |
                              v
                        Device Identity
                              |
                    AzureAdJoined = YES
                              |
                              v
                    AADLoginForWindows
                              |
                              v
                          AZURE ARC
                              |
                              v
               Azure Connected Machine Agent
                              |
                              v
                     Windows Server 2025
                              |
                              v
                         GOOGLE CLOUD
```

---

# Verification Commands

## GCP Workstation Check

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

## Azure Arc Check

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

## Extension Check

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

## Windows Entra Join Check

Inside the Windows Server:

```powershell
dsregcmd /status
```

Expected:

```text
AzureAdJoined : YES
```

---

# Success Criteria

Gate 3 is complete when:

- [ ] GCP reports the VM as `RUNNING`.
- [ ] Azure Arc reports the machine as `Connected`.
- [ ] The Arc server has a system-assigned managed identity.
- [ ] Microsoft authentication endpoints are reachable over HTTPS.
- [ ] The Arc metadata endpoint responds locally.
- [ ] `AADLoginForWindows` is installed.
- [ ] Extension provisioning state is `Succeeded`.
- [ ] `dsregcmd /status` reports `AzureAdJoined : YES`.
- [ ] A Device ID exists.
- [ ] The server appears as a device in Microsoft Entra.
- [ ] No human login role has yet been assigned.

---

# Stop Condition

If:

```text
AADLoginForWindows
```

does not report:

```text
Succeeded
```

or:

```powershell
dsregcmd /status
```

does not show:

```text
AzureAdJoined : YES
```

stop here.

Do not proceed to user authorization.

---

# Common Failure — No Managed Identity

If the extension reports a failure associated with tenant identity information, verify:

```bash
az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query identity
```

The machine must have:

```text
SystemAssigned
```

identity enabled before installing `AADLoginForWindows`.

---

# Common Failure — Device Registration Endpoint

If Entra join fails, test:

```powershell
curl.exe https://enterpriseregistration.windows.net/ -D -
```

A response such as:

```text
404
```

can still prove that the endpoint is reachable.

The objective is connectivity, not a web page.

---

# Common Failure — Check Tenant Metadata

Run:

```powershell
curl.exe `
    -H Metadata:true `
    "http://localhost:40342/metadata/identity/info?api-version=2018-02-01"
```

You should receive a valid tenant ID.

If you do not, troubleshoot the Azure Arc managed identity before troubleshooting Entra user login.

---

# Common Failure — Logs

Inspect:

```text
C:\WindowsAzure\Logs\Plugins\
Microsoft.Azure.ActiveDirectory\
AADLoginForWindows\
```

Microsoft Entra device registration events can also be viewed under:

```text
Event Viewer
    |
    v
Applications and Services Logs
    |
    v
Microsoft
    |
    v
Windows
    |
    v
User Device Registration
    |
    v
Admin
```

---

# Important Security Note

Do not manually add an Entra user to:

```text
Local Administrators
```

using commands such as:

```text
net localgroup administrators ...
```

for this lab.

Microsoft's supported Arc login model requires Azure role assignments such as:

```text
Virtual Machine User Login
```

or:

```text
Virtual Machine Administrator Login
```

User authorization belongs in the next IAM stage, not in local group manipulation.

---

# Gate 3 Mental Model

Remember:

```text
GATE 1

Does the computer work?

YES
```

```text
GATE 2

Can Azure Arc manage the computer?

YES
```

```text
GATE 3

Does Microsoft Entra recognize the computer?

YES
```

But:

```text
Can Chewbacca log in?

NOT YET
```

---

# Next Gate

The next stage introduces the human identity:

```text
Microsoft Entra ID

Device:
seir-crosscloud-01

User:
Chewbacca
```

At first, they will simply coexist.

Then Azure RBAC will connect them:

```text
Chewbacca
     |
     | Virtual Machine User Login
     v
seir-crosscloud-01
```

That is where:

```text
IDENTITY
+
AUTHORIZATION
+
CROSS-CLOUD COMPUTE
```

finally come together.
