# Azure Arc — What Is This Thing?

## Why Are We Talking About Azure Arc?

Until now, most of our cloud work has followed a simple model:

```text
AWS resource
    |
    v
Managed by AWS
```

```text
Azure resource
    |
    v
Managed by Azure
```

```text
GCP resource
    |
    v
Managed by GCP
```

Azure Arc changes that model.

Azure Arc allows Microsoft Azure to **manage and govern machines that are not running inside Azure**.

For example:

```text
Google Cloud
     |
     v
Windows Server VM
```

can also appear inside:

```text
Microsoft Azure
     |
     v
Azure Arc
     |
     v
Arc-enabled Server
```

There is still only **one computer**.

The computer remains physically hosted by Google Cloud.

Azure gains a **management-plane representation** of that computer.

---

# The Simplest Definition

> Azure Arc extends parts of the Azure management plane to infrastructure that exists outside Azure.

That infrastructure may include:

- Google Cloud virtual machines
- AWS virtual machines
- VMware virtual machines
- Physical servers
- Servers in a corporate datacenter
- Edge servers
- Linux servers
- Windows servers

The machine does **not** have to be an Azure VM.

---

# The Mental Model

Think about a traditional server:

```text
Physical or Virtual Server
          |
          v
Operating System
```

Normally, the platform hosting that machine controls it.

For example:

```text
GCP
 |
 v
Compute Engine
 |
 v
Windows Server
```

Azure Arc adds another management relationship:

```text
                 Microsoft Azure
                       |
                       v
                   Azure Arc
                       |
                       |
                       v
Google Cloud ---> Windows Server
```

Google still owns the **compute infrastructure**.

Azure now participates in the **management of the operating system and server resource**.

---

# Azure Arc Does NOT Move the VM

This is extremely important.

When we connect our GCP VM to Azure Arc:

```text
GCP VM
   |
   v
Azure Arc
```

Azure does **not** copy the VM into Azure.

Azure does **not** convert it into an Azure VM.

Azure does **not** take ownership of its virtual disk.

Azure does **not** move its network interface.

Azure does **not** replace the GCP VPC.

The VM remains:

```text
Compute Provider: GCP
```

The architecture becomes:

```text
                    MICROSOFT AZURE
                    ---------------
                          |
                          v
                       Azure Arc
                          |
                          |
                          v

GOOGLE CLOUD       Windows Server
------------       --------------
Compute Engine ---> VM
VPC
Disk
IP Address
Firewall
```

---

# One Machine — Two Control Planes

This is the most important idea in the lab.

After Azure Arc onboarding:

```text
Google Cloud
     |
     v
seir-crosscloud-01
Status: RUNNING
```

and:

```text
Microsoft Azure
     |
     v
Azure Arc
     |
     v
seir-crosscloud-01
Status: CONNECTED
```

These are **not two virtual machines**.

They are two representations of the same machine.

---

# What Does GCP Still Control?

Google Cloud continues to control the infrastructure underneath the VM.

Examples:

```text
CPU

Memory

VM Size

Boot Disk

Additional Disks

VPC

Subnet

External IP Address

GCP Firewall Rules

VM Start / Stop

VM Deletion
```

Conceptually:

```text
GCP
 |
 +-- Compute
 |
 +-- Storage
 |
 +-- Networking
 |
 +-- VM lifecycle
```

---

# What Does Azure Arc Add?

Azure Arc adds Azure management capabilities to the machine.

Examples include:

```text
Azure Resource Manager representation

Azure RBAC

Microsoft Entra managed identity

Azure Policy

Extensions

Monitoring

Security integrations

Configuration management

Update management

Remote management capabilities
```

Not every feature available to a native Azure VM automatically becomes available to an Arc-enabled server.

Think:

> Azure management capabilities are being extended to the external machine.

---

# How Does Azure Communicate With the Machine?

We install software on the external server called the:

```text
Azure Connected Machine Agent
```

The architecture becomes:

```text
Azure
 |
 v
Azure Arc
 |
 | HTTPS
 |
 v
Azure Connected Machine Agent
 |
 v
Windows Server
 |
 v
GCP VM
```

The agent creates and maintains the relationship between the server and Azure.

---

# The Azure Connected Machine Agent

The agent contains several important components.

You do not need to memorize every internal service immediately.

For SEIR-1, understand these three.

---

## 1. HIMDS

HIMDS means:

```text
Hybrid Instance Metadata Service
```

HIMDS is one of the core components of Azure Arc.

It handles things such as:

```text
Machine registration

Azure identity

Metadata

Connection status

Heartbeats
```

On Windows you can inspect it with:

```powershell
Get-Service himds
```

A connected machine should normally show:

```text
Status: Running
```

---

# 2. Extension Manager

Azure Arc can install extensions on the external machine.

Conceptually:

```text
Azure
 |
 v
Azure Arc
 |
 v
Extension Manager
 |
 v
Install additional functionality
```

Examples include extensions for:

```text
Monitoring

Security

Scripts

Identity

Configuration
```

Later in this lab we will install:

```text
AADLoginForWindows
```

That extension will help connect our Windows Server to Microsoft Entra authentication.

---

# 3. Machine Configuration

Azure can also evaluate configuration and policy against an Arc-enabled machine.

Conceptually:

```text
Azure Policy
      |
      v
Azure Arc
      |
      v
Windows Server
```

This makes it possible for organizations to apply centralized governance to machines running in different environments.

---

# What Happens When We Run azcmagent connect?

After installing the Connected Machine agent, we run:

```powershell
azcmagent connect
```

Conceptually, this performs:

```text
GCP Windows Server
        |
        v
Authenticate to Azure
        |
        v
Register machine
        |
        v
Create Azure resource
        |
        v
Create machine identity
        |
        v
Start sending health information
```

Azure then creates a resource representing the server.

---

# The Azure Resource

The external server becomes an Azure Resource Manager resource.

The resource type is:

```text
Microsoft.HybridCompute/machines
```

That means Azure can give the machine:

```text
Resource Group

Resource ID

Tags

RBAC

Policy

Extensions
```

just like many other Azure resources.

---

# Before Azure Arc

Our VM might look like this:

```text
GCP Project
     |
     v
Compute Engine
     |
     v
seir-crosscloud-01
```

Azure knows nothing about it.

---

# After Azure Arc

The architecture becomes:

```text
                     AZURE SUBSCRIPTION
                            |
                            v
                       Resource Group
                            |
                            v
                        Azure Arc
                            |
                            v
                  seir-crosscloud-01
                  Arc Resource Object
                            |
                            |
                            v
                     HTTPS Connection
                            |
                            |
                            v
                        GCP VM
                  seir-crosscloud-01
```

---

# Azure Resource ID

Once connected, the server receives an Azure Resource ID.

Conceptually:

```text
/subscriptions/...
    /resourceGroups/SEIR-ARC-RG
        /providers/Microsoft.HybridCompute
            /machines/seir-crosscloud-01
```

Now Azure can target that Resource ID with things such as:

```text
RBAC

Policy

Extensions

Tags
```

This is why bringing a machine into Azure Arc is important.

Azure now has an object against which Azure management controls can operate.

---

# The Machine Gets an Identity

This is especially important for our IAM course.

Every Arc-enabled server receives a:

```text
System-Assigned Managed Identity
```

That identity represents:

```text
THE MACHINE
```

not the person using it.

For example:

```text
Microsoft Entra ID
       |
       v
Machine Identity
       |
       v
seir-crosscloud-01
```

This allows the Connected Machine agent and authorized applications on the server to authenticate to Azure without storing a normal username and password.

---

# Machine Identity Is NOT User Identity

Do not confuse these.

We will eventually have:

```text
Microsoft Entra ID
       |
       +-------------------------+
       |                         |
       v                         v

Machine Identity            User Identity

seir-crosscloud-01          Chewbacca
                            Mookie
                            Student01
```

These identities serve different purposes.

---

# Machine Identity

Answers:

> Which computer is talking to Azure?

Example:

```text
seir-crosscloud-01
```

---

# User Identity

Answers:

> Which human is trying to access the computer?

Example:

```text
chewbacca@balerica-ai.org
```

---

# Why Does the Machine Need an Identity?

Imagine the server needs to communicate with Azure services.

Without managed identity we might need:

```text
Username
+
Password
```

or:

```text
Client ID
+
Client Secret
```

stored somewhere on the server.

That creates credential-management problems.

Managed identity allows:

```text
Machine
   |
   v
Microsoft Entra
   |
   v
OAuth Token
   |
   v
Azure Resource
```

without storing a traditional password for the machine identity.

---

# Azure Arc and RBAC

Azure Arc also allows us to apply Azure Role-Based Access Control.

Remember our earlier model:

```text
PRINCIPAL
    +
ROLE
    +
SCOPE
    =
ACCESS
```

The Arc server can become the **scope**.

Example:

```text
Chewbacca
    +
Virtual Machine User Login
    +
seir-crosscloud-01
    =
Authorized Login
```

This is what makes our upcoming lab interesting.

The computer exists in:

```text
Google Cloud
```

but authorization can be controlled using:

```text
Microsoft Entra
+
Azure RBAC
```

---

# Why Not Just Create a Local Windows User?

We could.

For example:

```text
Windows Server
      |
      v
Local User Database
      |
      v
Chewbacca
```

But now imagine:

```text
100 servers

500 servers

5,000 servers
```

Creating and removing local accounts individually becomes difficult.

Instead:

```text
Microsoft Entra
       |
       v
Central User Identity
       |
       v
Azure RBAC
       |
       +---- Server A
       |
       +---- Server B
       |
       +---- Server C
```

This gives us centralized identity and authorization.

---

# Why Is This Useful for Multi-Cloud?

Imagine an organization has:

```text
200 Azure VMs

100 AWS VMs

75 GCP VMs

50 physical servers
```

Without a common management layer:

```text
Azure Admin Tools

AWS Admin Tools

GCP Admin Tools

Datacenter Tools
```

may all operate separately.

Azure Arc attempts to create a common Azure management layer:

```text
                    AZURE MANAGEMENT
                           |
              +------------+------------+
              |            |            |
              v            v            v

            Azure         AWS          GCP

              \            |            /
               \           |           /
                +----------+----------+
                           |
                           v
                    Physical Servers
```

The infrastructure remains distributed.

The **management plane becomes more centralized**.

---

# Azure Arc Is Not a VPN

Azure Arc does not mean:

```text
GCP Network
     |
     v
Automatically connected to Azure VNet
```

It is not automatically creating a site-to-site VPN.

Networking between clouds is a separate subject.

Arc primarily establishes a **management relationship**.

---

# Azure Arc Is Not Active Directory Domain Services

Azure Arc also does not mean the machine has joined a traditional:

```text
Windows Active Directory Domain
```

We are working with:

```text
Microsoft Entra ID
```

and Azure management services.

Traditional AD DS and Entra ID are different identity systems.

---

# Azure Arc Is Not Azure Stack

These technologies have different purposes.

Very simplified:

```text
Azure Arc
=
Extend Azure management to external resources
```

```text
Azure Stack
=
Run certain Azure technologies in environments outside Microsoft's public Azure regions
```

Do not treat the terms as interchangeable.

---

# Azure Arc Is Not VM Migration

This:

```text
GCP VM
   |
   v
Azure Arc
```

does not mean:

```text
GCP VM
   |
   v
Azure VM
```

Nothing has migrated.

The VM is still running on Google infrastructure.

---

# Why Would Microsoft Want This?

Because real enterprises are rarely:

```text
100% Azure
```

A company may have:

```text
Azure

AWS

GCP

VMware

Bare Metal

Datacenters

Edge Locations
```

Azure Arc allows Azure management services to participate across those environments.

---

# Why Would an Organization Use It?

Possible reasons include:

```text
Centralized inventory

Centralized IAM

Azure Policy

Monitoring

Security

Server management

Compliance

Patch management

Extension deployment

Consistent tagging

Cross-cloud governance
```

The important word is:

```text
CONSISTENCY
```

---

# Connection Status

Arc-enabled servers report status back to Azure.

A healthy server normally appears as:

```text
Connected
```

The Connected Machine agent sends regular heartbeat information to Azure.

If Azure stops receiving those heartbeats, the server can appear as:

```text
Disconnected
```

Notice what this means.

The GCP VM could still be:

```text
RUNNING
```

while Azure reports:

```text
DISCONNECTED
```

because these are reporting different things.

---

# Example

GCP might say:

```text
VM Status:

RUNNING
```

while Azure says:

```text
Arc Status:

DISCONNECTED
```

That means:

```text
The computer is running
```

but:

```text
The Azure management relationship is not currently healthy
```

This is another example of the two-control-plane model.

---

# Useful Commands

## From the GCP Windows Server

Check the agent:

```powershell
azcmagent show
```

Check connectivity:

```powershell
azcmagent check
```

Check version:

```powershell
azcmagent version
```

Check HIMDS:

```powershell
Get-Service himds
```

---

# From Your Desktop Using Azure CLI

List Arc machines:

```bash
az connectedmachine list \
    --output table
```

Inspect one server:

```bash
az connectedmachine show \
    --name seir-crosscloud-01 \
    --resource-group SEIR-ARC-RG
```

---

# From Your Desktop Using GCP CLI

Meanwhile, the exact same computer can still be queried from GCP:

```bash
gcloud compute instances describe seir-crosscloud-01 \
    --zone=us-central1-a
```

This is the important comparison:

```text
gcloud
   |
   v
GCP infrastructure information
```

versus:

```text
az connectedmachine
   |
   v
Azure Arc management information
```

---

# Our SEIR-1 Architecture

For this course, the architecture will eventually become:

```text
                       MICROSOFT ENTRA
                             |
                             |
                      User Identity
                             |
                             v
                         Azure RBAC
                             |
                             v
                         Azure Arc
                             |
                             |
                  Azure Connected Machine
                         Agent
                             |
                             v
                      WINDOWS SERVER
                             |
                             v
                       GOOGLE CLOUD
```

This is a true cross-cloud IAM example.

---

# What Will Gate 2 Do?

Gate 2 performs only this transition:

```text
BEFORE

GCP
 |
 v
Windows Server
```

to:

```text
AFTER

       Azure
         |
         v
     Azure Arc
         |
         v
Connected Machine Agent
         |
         v
     Windows Server
         |
         v
        GCP
```

No user login integration yet.

---

# What Will Gate 3 Do?

Gate 3 adds:

```text
Microsoft Entra
       |
       v
AADLoginForWindows
       |
       v
Arc-enabled Server
```

The machine can then participate in Microsoft Entra authentication.

---

# What Will the Later Gates Do?

Eventually:

```text
Chewbacca
    |
    | Entra Identity
    v
Microsoft Entra
    |
    | Authentication
    v
Azure RBAC
    |
    | Authorization
    v
Azure Arc
    |
    v
Windows Server
    |
    v
GCP
```

The interesting result is:

> The computer runs in Google Cloud, but Microsoft Entra and Azure RBAC control who may log into it.

---

# Final Mental Model

If you remember nothing else, remember this:

```text
GCP PROVIDES THE COMPUTER
```

```text
AZURE ARC PROVIDES THE BRIDGE
```

```text
MICROSOFT ENTRA PROVIDES IDENTITY
```

```text
AZURE RBAC PROVIDES AUTHORIZATION
```

Together:

```text
GCP
 |
 | Compute
 v
Windows Server
 |
 | Azure Connected Machine Agent
 v
Azure Arc
 |
 | Identity + RBAC
 v
Microsoft Entra
```

---

# One Sentence Definition

> **Azure Arc allows Azure to represent, govern, and manage servers that physically or virtually run outside Azure.**

For our lab:

> **Azure Arc is the bridge that lets Microsoft Entra and Azure management controls reach a Windows Server VM running in Google Cloud.**
