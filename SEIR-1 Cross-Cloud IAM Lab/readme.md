# SEIR-1 Cross-Cloud IAM Lab

## GCP + Azure Arc + Microsoft Entra ID + Azure RBAC

---

# Overview

This lab demonstrates a real cross-cloud identity and access-management architecture.

You will deploy a Windows Server virtual machine in:

```text
Google Cloud Platform
```

and then extend Microsoft Azure management and Microsoft Entra identity controls to that machine using:

```text
Azure Arc
```

The final architecture combines:

```text
GCP Compute
+
Azure Arc
+
Microsoft Entra ID
+
Azure RBAC
+
Windows Server
```

The primary goal is to understand how:

```text
IDENTITY

AUTHENTICATION

AUTHORIZATION

GROUP MEMBERSHIP

DEVICE IDENTITY

CROSS-CLOUD MANAGEMENT
```

work together.

---

# Final Architecture

```text
                         MICROSOFT ENTRA ID
                                |
                    +-----------+-----------+
                    |                       |
                    v                       v

               User Identity          Device Identity
                    |                       |
                    v                       |
              Security Group                |
                    |                       |
                    v                       |
                 Azure RBAC                 |
                    |                       |
                    +-----------+-----------+
                                |
                                v
                           AZURE ARC
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

The Windows Server remains physically hosted by Google Cloud.

Azure Arc provides the management bridge.

Microsoft Entra provides identity.

Azure RBAC provides authorization.

---

# Mental Model

Remember these four lines:

```text
GCP   = COMPUTER

ARC   = BRIDGE

ENTRA = IDENTITY

RBAC  = PERMISSION
```

Everything in the lab builds upon those concepts.

---

# Lab Philosophy

This course follows a:

```text
MANUAL FIRST
```

approach.

You are expected to build and troubleshoot each portion of the lab manually before relying upon AI-assisted development tools.

The recommended progression is:

```text
1. Instructor performs the lab live.

2. Students follow along manually.

3. Students verify their environment.

4. Students troubleshoot their own implementation.

5. Students submit evidence.

6. Students may then reproduce or automate the implementation
   using tools such as Claude Code.
```

The objective is not simply:

```text
make it work
```

The objective is:

```text
understand why it works
```

---

# AI-Assisted Engineering

After completing the implementation manually, students are encouraged to reproduce parts of the environment using an AI coding assistant such as:

```text
Claude Code
```

This provides experience with both:

```text
Traditional Cloud Engineering

and

AI-Assisted Cloud Engineering
```

However:

> AI assistance does not replace understanding of the architecture.

Students should be capable of explaining:

```text
What was created?

Where was it created?

Which cloud owns it?

Which identity is being used?

Which role grants access?

Which scope applies?

Why did authentication succeed or fail?

Why did authorization succeed or fail?
```

before using AI to automate the same implementation.

---

# Prerequisites

Students should already have working CLI access to:

```text
Google Cloud Platform
```

and:

```text
Microsoft Azure
```

from their local workstation.

Verify GCP:

```bash
gcloud auth list
```

```bash
gcloud config get-value project
```

Verify Azure:

```bash
az account show
```

Students should also have:

```text
Python 3.10+

PowerShell 7+

Google Cloud CLI

Azure CLI

Microsoft Graph PowerShell

Az PowerShell modules

RDP client
```

available.

---

# Existing Environment

This lab assumes that:

```text
A custom domain already exists.

The custom domain is managed in GCP DNS.

The custom domain has already been verified in Microsoft Entra ID.

Students have access to an Azure subscription.

Students have access to a GCP project.
```

Domain migration is not part of this lab.

---

# Lab Structure

The project is divided into seven gates.

Each gate must work before proceeding to the next.

```text
Gate 1
   |
   v
Gate 2
   |
   v
Gate 3
   |
   v
Gate 4
   |
   v
Gate 5
   |
   v
Gate 6
   |
   v
Gate 7
```

Do not skip gates.

A failure in an earlier gate should be corrected before troubleshooting a later gate.

---

# Gate 1 — Create the GCP Windows Server

## Goal

Deploy:

```text
Windows Server 2025
```

in Google Compute Engine.

Verify:

```text
VM exists

VM is RUNNING

Windows Server 2025 is installed

RDP is available

RDP firewall access is restricted

Local bootstrap administrator works

Outbound HTTPS works
```

Architecture:

```text
Student Workstation
       |
       v
      GCP
       |
       v
Compute Engine
       |
       v
Windows Server 2025
```

Azure is not involved yet.

---

# Gate 2 — Connect the Server to Azure Arc

## Goal

Install the:

```text
Azure Connected Machine Agent
```

and register the GCP server with Azure Arc.

Final state:

```text
GCP VM
   |
   v
Azure Connected Machine Agent
   |
   v
Azure Arc
```

Verify:

```text
azcmagent show
```

reports:

```text
Connected
```

The Arc server should also receive a:

```text
System-Assigned Managed Identity
```

---

# Gate 3 — Add Microsoft Entra Device Identity

## Goal

Install:

```text
AADLoginForWindows
```

through Azure Arc.

Verify:

```powershell
dsregcmd /status
```

reports:

```text
AzureAdJoined : YES
```

The server should appear as a device in Microsoft Entra.

Architecture:

```text
Microsoft Entra
       |
       v
Device Identity
       |
       v
AADLoginForWindows
       |
       v
Azure Arc
       |
       v
Windows Server
       |
       v
GCP
```

---

# Gate 4 — Create the Microsoft Entra User

## Goal

Create a normal same-tenant:

```text
Member
```

user using the custom domain.

Example:

```text
chewbacca@balerica-ai.org
```

Verify:

```text
User exists

UserType = Member

AccountEnabled = True

Custom domain is verified

User belongs to same tenant as Arc machine
```

At the end of Gate 4:

```text
DEVICE EXISTS

USER EXISTS

LOGIN AUTHORIZATION DOES NOT EXIST
```

This is intentional.

---

# Gate 5 — Direct User Authorization

## Goal

Assign:

```text
Virtual Machine User Login
```

directly to the Entra user.

Scope:

```text
seir-crosscloud-01
```

The authorization formula becomes:

```text
USER
+
ROLE
+
SCOPE
=
ACCESS
```

Students must prove:

```text
Role absent   -> Login denied

Role present  -> Login allowed

Role removed  -> Login denied

Role restored -> Login allowed
```

This proves causality.

---

# Gate 6 — Group-Based Enterprise Authorization

## Goal

Replace the direct user role assignment with a security-group model.

Create:

```text
SEIR_ARC_Users
```

Then:

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
seir-crosscloud-01
```

Verify:

```text
User has no direct VM login assignment.

Group has the VM login assignment.

User can log in through group membership.
```

Then test:

```text
User IN group
     |
     v
ACCESS


User OUT of group
     |
     v
DENIED


User IN group
     |
     v
ACCESS
```

This demonstrates enterprise access management.

---

# Gate 7 — Revoke Authorization

## Goal

Remove the group's:

```text
Virtual Machine User Login
```

role assignment.

Do not delete:

```text
The user

The security group

The Arc resource

The VM

The Entra device
```

Final state:

```text
GCP VM                         RUNNING

Azure Arc                     CONNECTED

AADLoginForWindows            SUCCEEDED

Entra Device                  PRESENT

Entra User                    PRESENT

Entra Group                   PRESENT

Group Membership              PRESENT

VM Login Authorization        ABSENT
```

A new Entra-authenticated RDP attempt should be denied.

This proves:

> A correctly revoked environment is not a broken environment.

---

# Verification Scripts

Two verification tools are included or may be provided during the lab.

---

## Gates 1–4 Verification

Run after completing Gate 4:

```bash
python 1-4-verify_all_gates.py \
  --user-upn chewbacca@balerica-ai.org
```

The script verifies the infrastructure and identity state before authorization is introduced.

---

## Final Gates 1–7 Verification

Run after completing Gate 7:

```bash
python verify_final_all_gates.py \
  --user-upn chewbacca@balerica-ai.org
```

The final verifier should confirm:

```text
COMPUTE       PASS

NETWORK       PASS

AZURE ARC     PASS

DEVICE ID     PASS

USER ID       PASS

GROUP         PASS

REVOCATION    PASS
```

The final expected state is:

```text
Infrastructure healthy.

Identity healthy.

Network healthy.

Authorization intentionally removed.
```

---

# Required Student Deliverables

Students must complete **all seven gates**.

Completion is not based only on:

```text
"It worked."
```

Students must provide evidence.

---

# Deliverable 1 — Completed Lab

Students must perform:

```text
Gate 1

Gate 2

Gate 3

Gate 4

Gate 5

Gate 6

Gate 7
```

Students are responsible for maintaining the environment through the complete sequence.

---

# Deliverable 2 — Screenshot Evidence

Students must provide screenshots proving successful implementation.

Screenshots should show enough context to prove what occurred.

Do not submit screenshots containing:

```text
Passwords

Access tokens

Client secrets

Private keys

Recovery codes

Authentication cookies
```

---

# Required Screenshot Evidence

## Gate 1

Screenshot showing the GCP VM:

```text
seir-crosscloud-01
```

with:

```text
RUNNING
```

Also provide evidence of successful Windows login or Windows Server information.

Recommended:

```powershell
Get-ComputerInfo
```

---

## Gate 2

Screenshot of:

```powershell
azcmagent show
```

showing:

```text
Agent Status : Connected
```

Also include Azure-side evidence showing the Arc resource.

---

## Gate 3

Screenshot of:

```powershell
dsregcmd /status
```

showing:

```text
AzureAdJoined : YES
```

Also provide evidence of:

```text
AADLoginForWindows
```

with provisioning state:

```text
Succeeded
```

---

## Gate 4

Screenshot showing the Microsoft Entra user.

The screenshot should demonstrate:

```text
UserPrincipalName

UserType = Member

AccountEnabled = True
```

The custom domain should be visible.

---

## Gate 5

Provide evidence of:

```text
Virtual Machine User Login
```

assigned directly to the user.

Also provide evidence of a successful Entra-authenticated Windows login.

---

## Gate 6

Provide evidence showing:

```text
SEIR_ARC_Users
```

exists.

Show:

```text
Chewbacca is a member
```

and:

```text
Virtual Machine User Login
```

is assigned to the group.

Also provide evidence that the user successfully logged in through the group authorization path.

---

## Gate 7

Provide evidence that:

```text
Virtual Machine User Login
```

has been removed.

Show that:

```text
GCP VM remains RUNNING

Azure Arc remains Connected

AADLoginForWindows remains Succeeded

User remains enabled
```

Then provide evidence that a fresh login attempt is denied.

---

# Deliverable 3 — Final Verification Output

Students must run:

```bash
python verify_final_all_gates.py \
  --user-upn YOUR_USER@YOUR_DOMAIN
```

Submit:

```text
final_all_gates_report.json
```

along with a screenshot of the final verification scoreboard.

The expected automated result is:

```text
AUTOMATED FINAL-STATE VERIFICATION PASSED
```

---

# Deliverable 4 — Troubleshooting Evidence

Every student must demonstrate at least one troubleshooting workflow.

The report should contain:

```text
Symptom

Suspected Layer

Commands Used

Relevant Output

Diagnosis

Remediation

Verification
```

Example:

```text
SYMPTOM

RDP connection fails.


TEST

Test-NetConnection $VMIP -Port 3389


RESULT

TcpTestSucceeded : False


DIAGNOSIS

The failure is occurring before Entra authentication.


INVESTIGATION AREA

GCP networking
Windows firewall
RDP service


DO NOT INVESTIGATE YET

Azure RBAC
Entra passwords
Group membership
AADLoginForWindows
```

---

# Suggested Screenshot Naming Convention

Use a consistent naming convention.

Example:

```text
gate01-gcp-vm-running.png

gate01-windows-login.png

gate02-arc-connected.png

gate03-aad-extension.png

gate03-entra-joined.png

gate04-entra-user.png

gate05-direct-rbac.png

gate05-login-success.png

gate06-security-group.png

gate06-group-rbac.png

gate06-group-login-success.png

gate07-rbac-removed.png

gate07-login-denied.png

final-verification.png
```

Good evidence should allow another engineer to reconstruct what happened.

---

# Recommended Repository Structure

```text
seir-crosscloud-iam/
|
├── README.md
|
├── gates/
│   |
│   ├── gate01-gcp-windows.md
│   ├── gate02-azure-arc.md
│   ├── gate03-entra-device.md
│   ├── gate04-entra-user.md
│   ├── gate05-direct-rbac.md
│   ├── gate06-group-rbac.md
│   └── gate07-revocation.md
|
├── docs/
│   |
│   ├── azure_arc_explanation.md
│   └── powershell_troubleshooting.md
|
├── verification/
│   |
│   ├── 1-4-verify_all_gates.py
│   └── verify_final_all_gates.py
|
├── evidence/
│   |
│   ├── gate01/
│   ├── gate02/
│   ├── gate03/
│   ├── gate04/
│   ├── gate05/
│   ├── gate06/
│   └── gate07/
|
└── reports/
    |
    └── final_all_gates_report.json
```

---

# Troubleshooting Philosophy

When something fails:

```text
DO NOT CHANGE EVERYTHING.
```

Determine the failed layer.

Use:

```text
OS
 |
 v
NETWORK
 |
 v
DNS
 |
 v
RDP
 |
 v
AZURE ARC
 |
 v
ARC IDENTITY
 |
 v
AADLoginForWindows
 |
 v
ENTRA DEVICE
 |
 v
ENTRA USER
 |
 v
GROUP
 |
 v
RBAC
 |
 v
AUTHENTICATION
 |
 v
AUTHORIZATION
```

Move downward only after the previous layer has been proven healthy.

---

# First-Line Troubleshooting Commands

Students should become comfortable with these commands.

## Windows

```powershell
hostname
```

```powershell
whoami /all
```

```powershell
Get-ComputerInfo
```

---

## Network

```powershell
Get-NetIPConfiguration
```

```powershell
Get-NetRoute -DestinationPrefix "0.0.0.0/0"
```

```powershell
Get-DnsClientServerAddress
```

---

## DNS

```powershell
Resolve-DnsName login.microsoftonline.com
```

```powershell
Resolve-DnsName enterpriseregistration.windows.net
```

---

## Microsoft Connectivity

```powershell
Test-NetConnection login.microsoftonline.com -Port 443
```

```powershell
Test-NetConnection enterpriseregistration.windows.net -Port 443
```

```powershell
Test-NetConnection pas.windows.net -Port 443
```

---

## RDP

From the desktop:

```powershell
Test-NetConnection $VMIP -Port 3389
```

Inside the VM:

```powershell
Get-Service TermService
```

```powershell
Get-NetTCPConnection -LocalPort 3389 -State Listen
```

---

## Azure Arc

```powershell
azcmagent show
```

```powershell
azcmagent check
```

```powershell
azcmagent version
```

```powershell
Get-Service himds,GCArcService,ExtensionService
```

---

## Entra Device

```powershell
dsregcmd /status
```

Useful filter:

```powershell
dsregcmd /status |
    Select-String "AzureAdJoined|DeviceId|TenantId|AzureAdPrt"
```

---

## Arc Extension

```powershell
Get-AzConnectedMachineExtension `
    -ResourceGroupName "SEIR-ARC-RG" `
    -MachineName "seir-crosscloud-01"
```

---

## Entra User

```powershell
Get-MgUser `
    -UserId "chewbacca@balerica-ai.org"
```

---

## Effective RBAC

```powershell
Get-AzRoleAssignment `
    -SignInName "chewbacca@balerica-ai.org" `
    -ExpandPrincipalGroups
```

---

# Claude Troubleshooting Guide

Students are expected to use AI tools.

Therefore, this repository provides a troubleshooting model specifically intended for tools such as:

```text
Claude

Claude Code

ChatGPT

other coding assistants
```

The AI should be used as a:

```text
DIAGNOSTIC ASSISTANT
```

not as a:

```text
RESOURCE DESTRUCTION ASSISTANT
```

---

# Instructions for Claude

If you are Claude or another AI assistant helping a student with this lab, follow these rules.

## Rule 1 — Determine the Current Gate

Ask or determine:

```text
Which Gate is the student currently attempting?
```

Do not troubleshoot Gate 6 if Gate 2 is broken.

---

## Rule 2 — Do Not Rebuild Resources Immediately

Do not begin by recommending:

```text
Delete the VM

Delete the Arc resource

Delete the Entra device

Delete the Entra user

Disconnect Azure Arc

Reinstall everything
```

These actions destroy troubleshooting evidence.

---

## Rule 3 — Diagnose Bottom-Up

Use this sequence:

```text
Windows
   |
   v
Network
   |
   v
DNS
   |
   v
RDP
   |
   v
Azure Arc Agent
   |
   v
Arc Managed Identity
   |
   v
AADLoginForWindows
   |
   v
Entra Device Join
   |
   v
Entra User
   |
   v
Security Group
   |
   v
Azure RBAC
   |
   v
Authentication
   |
   v
Authorization
```

---

# Claude Diagnostic Decision Tree

## Student says:

```text
"I cannot connect to the server."
```

First ask for or run:

```powershell
Test-NetConnection $VMIP -Port 3389
```

If:

```text
False
```

do not troubleshoot Entra yet.

Investigate:

```text
GCP firewall

Windows Firewall

External IP

RDP service

Routing
```

---

## Student says:

```text
"The server is reachable but Entra login fails."
```

Check:

```powershell
azcmagent show
```

Expected:

```text
Connected
```

Then:

```powershell
azcmagent check
```

Then:

```powershell
Get-Service himds,GCArcService,ExtensionService
```

---

## Arc Is Healthy

Next check:

```powershell
dsregcmd /status
```

Expected:

```text
AzureAdJoined : YES
```

If:

```text
AzureAdJoined : NO
```

investigate:

```text
AADLoginForWindows

Device registration

Microsoft endpoints

Arc managed identity
```

Do not troubleshoot the user's RBAC assignment yet.

---

## Device Join Is Healthy

Check:

```powershell
Get-AzConnectedMachineExtension `
    -ResourceGroupName "SEIR-ARC-RG" `
    -MachineName "seir-crosscloud-01" `
    -Name "AADLoginForWindows"
```

Expected:

```text
ProvisioningState : Succeeded
```

---

## Extension Is Healthy

Check the user:

```powershell
Get-MgUser `
    -UserId "USER@DOMAIN"
```

Verify:

```text
UserType       = Member

AccountEnabled = True
```

---

## User Is Healthy

Check group membership.

Then check RBAC:

```powershell
Get-AzRoleAssignment `
    -SignInName "USER@DOMAIN" `
    -ExpandPrincipalGroups
```

Look specifically for:

```text
Virtual Machine User Login
```

or:

```text
Virtual Machine Administrator Login
```

---

# Authentication vs Authorization

Claude should explicitly determine whether the failure is:

```text
AUTHENTICATION
```

or:

```text
AUTHORIZATION
```

Authentication asks:

```text
WHO ARE YOU?
```

Authorization asks:

```text
WHAT ARE YOU ALLOWED TO DO?
```

Example:

```text
Microsoft accepts username/password
but
Windows says account cannot use device
```

This strongly suggests:

```text
AUTHORIZATION
```

Check RBAC.

Do not immediately reset the password.

---

# Claude Must Ask for Evidence

Claude should request actual command output.

For example:

```text
Please run:

azcmagent show

and paste the output.
```

Then:

```text
Please run:

dsregcmd /status

and paste the Device State section.
```

Then:

```text
Please run:

Get-AzRoleAssignment ...
```

Do not assume a command succeeded because the student says:

```text
"I think I did it."
```

Use evidence.

---

# Claude Should Work One Layer at a Time

Bad troubleshooting:

```text
Try reinstalling Arc.

Reset the password.

Recreate the firewall.

Delete the Entra object.

Restart Windows.
```

All at once.

Good troubleshooting:

```text
Step 1:

Test-NetConnection VM-IP -Port 3389
```

Evaluate result.

Then continue.

---

# Claude Should Not Invent Environment Values

Do not invent:

```text
Subscription IDs

Tenant IDs

Resource IDs

Object IDs

Group IDs

Project IDs

IP addresses
```

Retrieve them.

Examples:

```powershell
Get-AzContext
```

```powershell
Get-AzConnectedMachine
```

```powershell
Get-MgUser
```

```powershell
Get-MgGroup
```

```powershell
gcloud config get-value project
```

---

# Claude Should Preserve Evidence

Before changing something, inspect it.

For example:

```powershell
Get-Service himds
```

before:

```powershell
Restart-Service himds
```

and:

```powershell
Get-AzRoleAssignment
```

before:

```powershell
Remove-AzRoleAssignment
```

Troubleshooting should create:

```text
EVIDENCE
```

before:

```text
CHANGE
```

---

# Suggested Claude Prompt for Students

Students may copy the following when they need assistance.

```text
I am completing the SEIR-1 Cross-Cloud IAM lab.

Architecture:

GCP Windows Server 2025
-> Azure Connected Machine Agent
-> Azure Arc
-> AADLoginForWindows
-> Microsoft Entra Device
-> Microsoft Entra User
-> Entra Security Group
-> Azure RBAC

I am currently on Gate: [NUMBER]

Expected result:
[DESCRIBE EXPECTED RESULT]

Actual result:
[DESCRIBE FAILURE]

Help me troubleshoot this one layer at a time.

Rules:

1. Do not immediately recommend deleting or recreating resources.

2. Diagnose bottom-up:
   Windows
   Network
   DNS
   RDP
   Azure Arc
   Managed Identity
   AADLoginForWindows
   Entra Device
   Entra User
   Group Membership
   Azure RBAC
   Authentication
   Authorization

3. Give me one or a small group of diagnostic commands at a time.

4. Ask me to provide the command output before deciding what to change.

5. Explain what each command is proving.

6. Separate authentication problems from authorization problems.

7. Prefer read-only diagnostic commands before repair commands.

8. Do not invent IDs, resource names, subscription IDs, tenant IDs,
   Object IDs, or IP addresses.

9. Preserve evidence before making changes.

10. Once the cause is identified, provide the smallest possible remediation
    and then give me a command to verify the repair.

Start by helping me identify which layer is failing.
```

---

# Suggested Claude Code Prompt

After manually completing the lab, students may ask Claude Code to reproduce or automate portions of the implementation.

Example:

```text
Review this SEIR-1 Cross-Cloud IAM repository.

Do not change anything yet.

First identify:

1. GCP resources
2. Azure Arc resources
3. Microsoft Entra dependencies
4. Azure RBAC assignments
5. Security group dependencies
6. Verification scripts

Then explain the desired state.

After I approve the plan, create automation that reproduces the existing
manual implementation.

Do not weaken firewall rules.

Do not expose RDP to 0.0.0.0/0.

Do not store passwords, tokens, or secrets in source code.

Do not create duplicate Entra users or groups.

Do not replace group-based RBAC with direct user assignments.

Make all operations idempotent where practical.

After implementation, run or provide verification commands proving each
layer is correct.
```

---

# What Claude Should Never Do Automatically

Claude should not automatically:

```text
Disable security controls

Open TCP 3389 to 0.0.0.0/0

Delete Entra users

Delete Entra devices

Delete Arc resources

Disconnect azcmagent

Run dsregcmd /leave

Remove security groups

Reset passwords

Create new subscriptions

Change tenant configuration

Disable Conditional Access

Disable Security Defaults
```

unless the student clearly understands the consequence and the action is explicitly required by the instructor.

---

# Evidence Before Repair

Students should develop this engineering habit:

```text
SYMPTOM
    |
    v
EVIDENCE
    |
    v
HYPOTHESIS
    |
    v
TEST
    |
    v
DIAGNOSIS
    |
    v
SMALLEST REPAIR
    |
    v
VERIFICATION
```

Not:

```text
SYMPTOM
    |
    v
PANIC
    |
    v
DELETE EVERYTHING
```

---

# Final Student Submission

Submit the following:

```text
README.md

Completed Gate documentation

Screenshot evidence

PowerShell troubleshooting evidence

1-4-verify_all_gates.py output

verify_final_all_gates.py output

final_all_gates_report.json
```

Screenshots should be stored in:

```text
evidence/
```

Reports should be stored in:

```text
reports/
```

---

# Submission Checklist

Before submitting:

```text
[ ] Gate 1 completed

[ ] Gate 2 completed

[ ] Gate 3 completed

[ ] Gate 4 completed

[ ] Gate 5 completed

[ ] Gate 6 completed

[ ] Gate 7 completed

[ ] Required screenshots captured

[ ] No secrets visible in screenshots

[ ] Troubleshooting exercise completed

[ ] Final verification script executed

[ ] JSON verification report included

[ ] Final RDP authorization denial confirmed

[ ] GCP VM still RUNNING

[ ] Azure Arc still Connected

[ ] Entra user still enabled

[ ] Security group still exists

[ ] Final VM login authorization removed
```

---

# What You Should Be Able to Explain After This Lab

You should be able to answer:

```text
What is Azure Arc?

Why does the VM remain a GCP VM?

What does the Azure Connected Machine Agent do?

What is HIMDS?

What is a system-assigned managed identity?

What is AADLoginForWindows?

What does AzureAdJoined mean?

What is the difference between a user identity and device identity?

What is the difference between authentication and authorization?

Why does Contributor not automatically grant Windows login?

What does Virtual Machine User Login grant?

Why are security groups preferable to individual role assignments?

How can removing group membership revoke access?

How can removing the group's RBAC role revoke access for the entire team?

Why can TCP/3389 remain reachable while login is denied?

How do you identify whether the problem is GCP, Windows, Arc, Entra, or RBAC?

How would you use Claude Code without allowing it to hide your lack of understanding?
```

If you can explain those concepts and successfully demonstrate the lab, you have done much more than:

```text
follow a tutorial
```

You have implemented and troubleshot a:

```text
CROSS-CLOUD
IDENTITY
AUTHENTICATION
AUTHORIZATION
AND ACCESS-LIFECYCLE
ARCHITECTURE
```

---

# Final Architecture Summary

```text
                      MICROSOFT ENTRA ID
                             |
                  +----------+----------+
                  |                     |
                  v                     v

             Human Identity        Device Identity
                  |
                  v
           Security Groups
                  |
                  v
              Azure RBAC
                  |
                  v
              Azure Arc
                  |
                  v
         AADLoginForWindows
                  |
                  v
          Windows Server 2025
                  |
                  v
                  GCP
```

---

# Final Lesson

The most important result of this lab is not:

```text
"I successfully RDP'd into a server."
```

The important result is understanding:

```text
WHO
was authenticated

WHAT
authorized them

WHERE
that authorization applied

HOW
the external machine became manageable from Azure

WHY
access succeeded

and

WHY
access disappeared when authorization was removed
```

That is the skill you take into the office.
