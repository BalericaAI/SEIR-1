# SEIR-1 Cross-Cloud IAM Lab

# Gate 2 — Onboard the GCP VM to Azure Arc

## Objective

In Gate 1, you created and verified a Windows Server 2025 virtual machine running in Google Cloud Platform.

The machine currently looks like this:

```text
Student Workstation
        |
        v
Google Cloud
        |
        v
Windows Server 2025
seir-crosscloud-01
```

In this gate, you will connect that GCP-hosted Windows Server to **Azure Arc**.

The VM will remain in Google Cloud.

Azure will create a management-plane representation of the machine.

At the end of this gate:

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
Arc-enabled Server Resource
     |
     v
System-Assigned Managed Identity
```

You are **not** enabling Microsoft Entra user login yet.

That will occur in Gate 3.

---

# Important Concept

Azure Arc does not move the VM.

The VM remains:

```text
Compute Provider:
Google Cloud Platform
```

Its:

```text
CPU
Memory
Disk
Network Interface
External IP
VPC
Firewall
```

remain controlled by GCP.

Azure gains a resource representation of the server:

```text
Microsoft.HybridCompute/machines
```

Think of Azure Arc as adding another management plane.

---

# Gate 2.1 — Verify Azure CLI Authentication

Perform this step from your normal workstation.

Run:

```bash
az login
```

If you are already authenticated:

```bash
az account show
```

Verify:

```text
Subscription
Tenant
Account
```

---

# Gate 2.2 — View Available Azure Subscriptions

Run:

```bash
az account list \
    --output table
```

Identify the subscription you will use for the lab.

---

# Gate 2.3 — Select the Correct Subscription

Set the subscription:

```bash
az account set \
    --subscription "YOUR_SUBSCRIPTION_NAME_OR_ID"
```

Verify:

```bash
az account show \
    --output table
```

Do not continue until you know which Azure subscription is active.

---

# Gate 2.4 — Store Azure Values

For easier command reuse, define your lab values.

## Bash / Git Bash

```bash
AZ_SUBSCRIPTION="YOUR_SUBSCRIPTION_ID"
AZ_RESOURCE_GROUP="SEIR-ARC-RG"
AZ_LOCATION="eastus"
ARC_MACHINE="seir-crosscloud-01"
```

## PowerShell

```powershell
$AZ_SUBSCRIPTION = "YOUR_SUBSCRIPTION_ID"
$AZ_RESOURCE_GROUP = "SEIR-ARC-RG"
$AZ_LOCATION = "eastus"
$ARC_MACHINE = "seir-crosscloud-01"
```

---

# Gate 2.5 — Create the Azure Resource Group

First check existing resource groups:

```bash
az group list \
    --output table
```

If `SEIR-ARC-RG` does not exist:

```bash
az group create \
    --name SEIR-ARC-RG \
    --location eastus
```

Verify:

```bash
az group show \
    --name SEIR-ARC-RG \
    --output table
```

Expected conceptually:

```text
Name          Location
------------  --------
SEIR-ARC-RG   eastus
```

---

# Gate 2.6 — Register Azure Arc Resource Providers

Azure Arc requires several Azure resource providers.

Register:

```bash
az provider register \
    --namespace Microsoft.HybridCompute
```

```bash
az provider register \
    --namespace Microsoft.GuestConfiguration
```

```bash
az provider register \
    --namespace Microsoft.HybridConnectivity
```

For later Azure management functionality, also register:

```bash
az provider register \
    --namespace Microsoft.Compute
```

---

# Gate 2.7 — Verify Provider Registration

Run:

```bash
az provider show \
    --namespace Microsoft.HybridCompute \
    --query registrationState \
    --output tsv
```

Expected:

```text
Registered
```

Repeat:

```bash
az provider show \
    --namespace Microsoft.GuestConfiguration \
    --query registrationState \
    --output tsv
```

```bash
az provider show \
    --namespace Microsoft.HybridConnectivity \
    --query registrationState \
    --output tsv
```

```bash
az provider show \
    --namespace Microsoft.Compute \
    --query registrationState \
    --output tsv
```

All should eventually report:

```text
Registered
```

---

# Gate 2.8 — Verify Onboarding Permission

The account performing the onboarding must be allowed to create Azure Arc-enabled server resources.

Suitable roles include:

```text
Azure Connected Machine Onboarding
```

or:

```text
Contributor
```

at the appropriate Azure scope.

Your instructor may already have configured this permission.

If you receive an Azure authorization error later, check your Azure role assignments before troubleshooting the GCP VM.

---

# Gate 2.9 — Install the Azure CLI Connected Machine Extension

Perform this step on your workstation.

Run:

```bash
az extension add \
    --name connectedmachine
```

If it is already installed:

```bash
az extension update \
    --name connectedmachine
```

Verify:

```bash
az extension show \
    --name connectedmachine \
    --output table
```

---

# Gate 2.10 — Verify No Arc Machine Exists Yet

Run:

```bash
az connectedmachine list \
    --resource-group SEIR-ARC-RG \
    --output table
```

Before onboarding, you should not see:

```text
seir-crosscloud-01
```

This establishes our before-state.

---

# Architecture Checkpoint

Azure currently contains:

```text
Subscription
     |
     v
SEIR-ARC-RG
```

but not yet:

```text
seir-crosscloud-01
```

Meanwhile:

```text
Google Cloud
     |
     v
seir-crosscloud-01
```

already exists and is running.

---

# Gate 2.11 — Connect to the GCP Windows Server

RDP into:

```text
seir-crosscloud-01
```

using the local bootstrap account created during Gate 1.

Example:

```text
seir-local-admin
```

Open **PowerShell as Administrator** inside the Windows Server.

---

# Gate 2.12 — Verify Azure Network Connectivity

Before installing the agent:

```powershell
Test-NetConnection management.azure.com -Port 443
```

Expected:

```text
TcpTestSucceeded : True
```

Also test Microsoft identity connectivity:

```powershell
Test-NetConnection login.microsoftonline.com -Port 443
```

Expected:

```text
TcpTestSucceeded : True
```

If HTTPS connectivity does not work, stop here.

Azure Arc requires outbound access to Azure services.

---

# Gate 2.13 — Download the Azure Connected Machine Agent

Inside the GCP Windows Server:

```powershell
$AgentUrl = "https://aka.ms/AzureConnectedMachineAgent"
```

Download:

```powershell
Invoke-WebRequest `
    -Uri $AgentUrl `
    -OutFile "$env:TEMP\AzureConnectedMachineAgent.msi"
```

Verify:

```powershell
Get-Item "$env:TEMP\AzureConnectedMachineAgent.msi"
```

---

# Gate 2.14 — Install the Agent

Run:

```powershell
Start-Process `
    msiexec.exe `
    -ArgumentList "/i `"$env:TEMP\AzureConnectedMachineAgent.msi`" /qn" `
    -Wait
```

After installation, close and reopen the elevated PowerShell session if necessary.

---

# Gate 2.15 — Verify azcmagent

Run:

```powershell
azcmagent version
```

You should receive Azure Connected Machine agent version information.

Then:

```powershell
Get-Command azcmagent
```

You should see the installed command.

---

# Gate 2.16 — Verify Azure Arc Services

Run:

```powershell
Get-Service himds
```

You should see:

```text
Status   Name
------   ----
Running  himds
```

You can also inspect other Azure Arc-related services:

```powershell
Get-Service |
    Where-Object {
        $_.Name -match "himds|gc"
    }
```

---

# Gate 2.17 — Run the Azure Arc Connectivity Check

Before registration:

```powershell
azcmagent check
```

This checks whether the machine can communicate with the Azure endpoints required by the Connected Machine agent.

Review any failures before continuing.

---

# Gate 2.18 — Connect the Machine to Azure Arc

Run this command **inside the GCP Windows Server**.

Replace the values with your actual Azure information:

```powershell
azcmagent connect `
    --subscription-id "YOUR_SUBSCRIPTION_ID" `
    --resource-group "SEIR-ARC-RG" `
    --location "eastus"
```

Because this is Windows Server with Desktop Experience, the normal interactive browser authentication flow should be used.

---

# Important — Do Not Use Device Code for This Lab

Do not add:

```text
--use-device-code
```

unless your instructor specifically tells you to.

Your Microsoft Entra tenant may have Security Defaults or Conditional Access policies that block device-code authentication.

Use the normal browser-based interactive login instead.

---

# Gate 2.19 — Authenticate to Azure

A Microsoft login window should open.

Authenticate using the Azure account authorized to onboard the machine.

After successful authentication, `azcmagent` will:

```text
Authenticate
     |
     v
Create Azure Arc Resource
     |
     v
Associate Local Agent
     |
     v
Create Machine Identity
```

Wait for the command to complete.

---

# Gate 2.20 — Verify the Local Agent Status

Run:

```powershell
azcmagent show
```

Look for:

```text
Agent Status
```

Expected:

```text
Connected
```

You should also see information such as:

```text
Azure Resource Name

Resource Group

Subscription ID

Tenant ID

Location
```

---

# Gate 2.21 — Display Only Important Agent Fields

Run:

```powershell
azcmagent show `
    "Agent Status" `
    "Agent Last Heartbeat"
```

Expected:

```text
Agent Status          Connected
Agent Last Heartbeat  <recent time>
```

---

# Gate 2.22 — Verify the Azure Resource From Your Workstation

Return to the workstation.

Run:

```bash
az connectedmachine list \
    --resource-group SEIR-ARC-RG \
    --output table
```

You should now see:

```text
seir-crosscloud-01
```

---

# Gate 2.23 — Inspect the Arc-Enabled Server

Run:

```bash
az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG
```

For cleaner output:

```bash
az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query "{Name:name,Location:location,Status:status}" \
    --output table
```

Expected:

```text
Name                  Location   Status
--------------------  ---------  ---------
seir-crosscloud-01    eastus     Connected
```

---

# Gate 2.24 — Verify the System-Assigned Managed Identity

Every Azure Arc-enabled server receives a system-assigned Microsoft Entra managed identity.

Run:

```bash
az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query identity
```

You should see identity information similar to:

```text
principalId
tenantId
type
```

The type should indicate a system-assigned identity.

---

# Gate 2.25 — Display the Machine Principal ID

Run:

```bash
az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query identity.principalId \
    --output tsv
```

Record the value.

It should be a GUID.

Example:

```text
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

This is the Microsoft Entra identity representing the **machine**.

---

# Important Concept — Machine Identity vs User Identity

The identity created in this gate represents:

```text
THE COMPUTER
```

It does not represent:

```text
Chewbacca
Mookie
Student01
```

The architecture is now:

```text
Microsoft Entra ID
       |
       +---- Machine Identity
                |
                v
        seir-crosscloud-01
```

Later we will add:

```text
Microsoft Entra ID
       |
       +---- Machine Identity
       |
       +---- User Identity
```

These are different security principals.

---

# Gate 2.26 — Verify Azure Arc From Both Clouds

## GCP

Run from the workstation:

```bash
gcloud compute instances describe seir-crosscloud-01 \
    --zone=us-central1-a \
    --format="table(name,status,zone)"
```

Expected:

```text
seir-crosscloud-01   RUNNING
```

## Azure

Run:

```bash
az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query "{Name:name,Status:status,Location:location}" \
    --output table
```

Expected:

```text
seir-crosscloud-01   Connected
```

---

# The Same Machine Now Exists in Two Control Planes

Conceptually:

```text
GOOGLE CLOUD
----------------------------

Compute Engine VM

seir-crosscloud-01

Status:
RUNNING


            SAME MACHINE


AZURE
----------------------------

Arc-enabled Server

seir-crosscloud-01

Status:
CONNECTED
```

This does **not** mean there are two VMs.

There is one VM.

There are two management-plane representations.

---

# Gate 2.27 — Verify Azure Has Not Enabled Entra Login Yet

Run from the workstation:

```bash
az connectedmachine extension list \
    --machine-name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --output table
```

At this point there should be no:

```text
AADLoginForWindows
```

extension.

That is intentional.

Gate 2 stops before user login integration.

---

# Gate 2 Final Architecture

```text
                    MICROSOFT ENTRA ID
                           |
                           |
                    Machine Identity
                           |
                           v
                       AZURE ARC
                           |
                  Arc Resource Object
                           |
                           |
              Azure Connected Machine Agent
                           |
                           v
                    GOOGLE CLOUD
                           |
                           v
                 Windows Server 2025
                 seir-crosscloud-01
```

The server:

```text
Physically runs in: GCP
```

but:

```text
Is represented in: Azure
```

and:

```text
Has an identity in: Microsoft Entra
```

---

# Final Verification Commands

## Workstation — Azure

```bash
az account show \
    --output table
```

```bash
az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG \
    --query "{Name:name,Status:status,Location:location,PrincipalId:identity.principalId}" \
    --output table
```

## Workstation — GCP

```bash
gcloud compute instances describe seir-crosscloud-01 \
    --zone=us-central1-a \
    --format="table(name,status,zone)"
```

## GCP Windows Server

```powershell
azcmagent show
```

---

# Success Criteria

Gate 2 is complete when:

- [ ] Azure CLI authentication works.
- [ ] The correct Azure subscription is selected.
- [ ] `SEIR-ARC-RG` exists.
- [ ] `Microsoft.HybridCompute` is registered.
- [ ] `Microsoft.GuestConfiguration` is registered.
- [ ] `Microsoft.HybridConnectivity` is registered.
- [ ] The Connected Machine agent is installed on the GCP VM.
- [ ] `himds` is running.
- [ ] `azcmagent check` completes successfully.
- [ ] `azcmagent connect` succeeds.
- [ ] `azcmagent show` reports `Connected`.
- [ ] Azure CLI shows `seir-crosscloud-01`.
- [ ] Azure reports the Arc machine as `Connected`.
- [ ] The Arc server has a system-assigned managed identity.
- [ ] GCP still reports the original VM as `RUNNING`.
- [ ] `AADLoginForWindows` has **not** yet been installed.

---

# Failure Rule

If:

```text
azcmagent show
```

does not report:

```text
Connected
```

stop here.

Do not install:

```text
AADLoginForWindows
```

Do not assign:

```text
Virtual Machine User Login
```

Do not troubleshoot Entra user login.

At this stage the problem is still one of:

```text
Azure authentication

Azure RBAC

Azure resource providers

Azure Arc network connectivity

Connected Machine agent

Azure Arc registration
```

Fix Gate 2 before proceeding.

---

# Next Gate

Gate 3 will add the Microsoft Entra authentication layer:

```text
Microsoft Entra ID
       |
       v
Azure Arc
       |
       v
AADLoginForWindows
       |
       v
Windows Server 2025
```

At that point:

```powershell
dsregcmd /status
```

should eventually report:

```text
AzureAdJoined : YES
```

That will be the point where the GCP-hosted Windows Server becomes capable of participating in Microsoft Entra interactive user authentication.
