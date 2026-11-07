# SEIR-1 — Azure Arc Cross-Cloud IAM

# PowerShell Troubleshooting Commands

## Purpose

These commands are intended to build the troubleshooting habits used by Windows, cloud, IAM, and infrastructure engineers.

Do not begin troubleshooting with:

```text
Delete it and recreate it.
```

Do not begin troubleshooting with:

```text
Restart everything.
```

Do not begin troubleshooting with:

```text
Ask Claude Code to fix it.
```

First determine:

> **Which layer is actually failing?**

Use this order:

```text
1. Operating System
2. Network
3. DNS
4. RDP
5. Azure Arc Agent
6. Azure Arc Identity
7. AADLoginForWindows
8. Microsoft Entra Device Join
9. Microsoft Entra User / Group
10. Azure RBAC
11. Authentication
12. Authorization
```

---

# 1. Who Am I and Where Am I?

Always establish your environment first.

```powershell
hostname
```

```powershell
whoami
```

```powershell
whoami /user
```

```powershell
whoami /groups
```

Useful PowerShell equivalent:

```powershell
$env:COMPUTERNAME
```

```powershell
$env:USERNAME
```

Check whether the current PowerShell session is elevated:

```powershell
([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
```

Expected when running elevated:

```text
True
```

---

# 2. Check the Operating System

```powershell
Get-ComputerInfo |
    Select-Object `
        WindowsProductName,
        WindowsVersion,
        OsBuildNumber,
        OsArchitecture
```

Alternative:

```powershell
Get-CimInstance Win32_OperatingSystem |
    Select-Object `
        Caption,
        Version,
        BuildNumber,
        OSArchitecture
```

For this lab you should be using:

```text
Windows Server 2025
Desktop Experience
```

---

# 3. Check Time

Authentication systems care about time.

```powershell
Get-Date
```

```powershell
Get-TimeZone
```

Check Windows Time:

```powershell
w32tm /query /status
```

Check configured time source:

```powershell
w32tm /query /source
```

Check Windows Time service:

```powershell
Get-Service W32Time
```

---

# 4. Inspect Network Configuration

Start with:

```powershell
Get-NetIPConfiguration
```

Then:

```powershell
Get-NetIPAddress -AddressFamily IPv4
```

Look at:

```text
IP Address
Prefix Length
Default Gateway
DNS Servers
```

---

# 5. Inspect DNS Configuration

```powershell
Get-DnsClientServerAddress -AddressFamily IPv4
```

More readable:

```powershell
Get-DnsClientServerAddress -AddressFamily IPv4 |
    Format-Table `
        InterfaceAlias,
        ServerAddresses
```

---

# 6. Inspect Routing

```powershell
Get-NetRoute -AddressFamily IPv4 |
    Sort-Object RouteMetric
```

Look specifically for the default route:

```powershell
Get-NetRoute `
    -DestinationPrefix "0.0.0.0/0"
```

Traditional Windows command:

```powershell
route print
```

Students should be comfortable with both.

---

# 7. Test General Internet Connectivity

Test HTTPS connectivity:

```powershell
Test-NetConnection www.microsoft.com -Port 443
```

Expected:

```text
TcpTestSucceeded : True
```

---

# 8. Test Microsoft Entra Connectivity

```powershell
Test-NetConnection `
    login.microsoftonline.com `
    -Port 443
```

Expected:

```text
TcpTestSucceeded : True
```

---

# 9. Test Entra Device Registration

```powershell
Test-NetConnection `
    enterpriseregistration.windows.net `
    -Port 443
```

Expected:

```text
TcpTestSucceeded : True
```

---

# 10. Test Azure Authorization Service

```powershell
Test-NetConnection `
    pas.windows.net `
    -Port 443
```

Expected:

```text
TcpTestSucceeded : True
```

These endpoints participate in Entra authentication, device registration, and the Arc Windows login authorization path.

---

# 11. Test the Endpoints Using HTTP

Sometimes TCP works but HTTP/TLS still fails.

Test:

```powershell
curl.exe `
    https://login.microsoftonline.com/ `
    -D -
```

Then:

```powershell
curl.exe `
    https://enterpriseregistration.windows.net/ `
    -D -
```

Then:

```powershell
curl.exe `
    https://pas.windows.net/ `
    -D -
```

A response such as:

```text
404 Not Found
```

can actually be a successful connectivity test.

It proves that:

```text
DNS worked
TCP worked
TLS worked
HTTP reached the service
```

The URL simply did not request a valid application resource.

---

# 12. Test DNS Resolution Directly

```powershell
Resolve-DnsName login.microsoftonline.com
```

```powershell
Resolve-DnsName enterpriseregistration.windows.net
```

```powershell
Resolve-DnsName pas.windows.net
```

Traditional Windows command:

```powershell
nslookup login.microsoftonline.com
```

If HTTPS fails, always determine whether DNS is the actual problem first.

---

# 13. Clear the DNS Resolver Cache

Only after determining cached DNS may be involved:

```powershell
Clear-DnsClientCache
```

Traditional version:

```powershell
ipconfig /flushdns
```

Do not make clearing caches your first troubleshooting technique.

---

# 14. Verify Google Cloud Metadata

Remember:

> This machine is still physically running in GCP.

Test the Google metadata service:

```powershell
Invoke-RestMethod `
    -Headers @{"Metadata-Flavor"="Google"} `
    -Uri "http://metadata.google.internal/computeMetadata/v1/instance/name"
```

Expected:

```text
seir-crosscloud-01
```

This proves the Windows Server still recognizes its GCP environment.

---

# 15. Verify RDP Service

Check Remote Desktop Services:

```powershell
Get-Service TermService
```

Expected:

```text
Running
```

---

# 16. Verify Port 3389 Is Listening

Inside the Windows VM:

```powershell
Get-NetTCPConnection `
    -LocalPort 3389 `
    -State Listen
```

Alternative:

```powershell
netstat -ano |
    Select-String ":3389"
```

---

# 17. Verify RDP Is Enabled

```powershell
Get-ItemProperty `
    "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" `
    -Name fDenyTSConnections
```

Expected:

```text
fDenyTSConnections : 0
```

`0` means RDP connections are permitted by that configuration setting.

---

# 18. Inspect Windows Firewall RDP Rules

```powershell
Get-NetFirewallRule `
    -DisplayGroup "Remote Desktop" |
    Format-Table `
        DisplayName,
        Enabled,
        Direction,
        Action
```

Inspect port filters:

```powershell
Get-NetFirewallPortFilter |
    Where-Object {
        $_.LocalPort -eq "3389"
    }
```

---

# 19. Test RDP From the Student Workstation

Run from the desktop:

```powershell
Test-NetConnection `
    YOUR_VM_IP `
    -Port 3389
```

Expected:

```text
TcpTestSucceeded : True
```

This is extremely important.

If:

```text
TCP 3389 = FALSE
```

do not troubleshoot Entra authentication yet.

You have a networking problem.

---

# 20. See Current RDP Sessions

Inside Windows:

```powershell
quser.exe
```

or:

```powershell
qwinsta.exe
```

This tells you whether a session already exists.

Remember:

```text
Disconnected session
!=
New authentication attempt
```

---

# 21. Check Whether the Azure Arc Agent Is Installed

```powershell
Get-Command azcmagent `
    -ErrorAction SilentlyContinue
```

Check installation directory:

```powershell
Get-ChildItem `
    "$env:ProgramFiles\AzureConnectedMachineAgent"
```

---

# 22. Check Azure Arc Version

```powershell
azcmagent version
```

---

# 23. Check Azure Arc Status

One of the most important commands in this entire lab:

```powershell
azcmagent show
```

Look for:

```text
Agent Status
Resource Name
Resource Group
Subscription ID
Tenant ID
Location
Last Heartbeat
```

You want:

```text
Agent Status : Connected
```

---

# 24. Show Only Important Arc Status

```powershell
azcmagent show `
    "Agent Status" `
    "Agent Last Heartbeat"
```

This is useful when you do not need the entire output.

---

# 25. Save Arc Status as JSON

```powershell
azcmagent show -j |
    Out-File `
        "$env:USERPROFILE\Desktop\arc-status.json"
```

This is useful for:

```text
Trouble tickets
Escalations
Documentation
Automation
```

---

# 26. Run the Azure Arc Network Diagnostic

```powershell
azcmagent check
```

This should become one of the first commands students remember for Arc troubleshooting.

It checks connectivity to required Azure Arc endpoints.

---

# 27. Run Arc Diagnostics Verbosely

Most `azcmagent` commands support:

```text
--verbose
```

Example:

```powershell
azcmagent check --verbose
```

The verbose output is useful when normal output does not reveal enough information.

---

# 28. Check Azure Arc Services

The Windows Connected Machine agent installs three particularly important services:

```powershell
Get-Service `
    himds,
    GCArcService,
    ExtensionService
```

Expected:

```text
Running
Running
Running
```

For cleaner output:

```powershell
Get-Service `
    himds,
    GCArcService,
    ExtensionService |
    Format-Table `
        Name,
        Status,
        StartType
```

---

# 29. Check HIMDS Specifically

```powershell
Get-Service himds
```

HIMDS is the:

```text
Hybrid Instance Metadata Service
```

It is central to:

```text
Azure Arc registration
Heartbeats
Machine metadata
Managed identity
```

---

# 30. Check the Extension Service

```powershell
Get-Service ExtensionService
```

If this service is not functioning, Azure Arc extensions may fail to install or update.

---

# 31. Check Machine Configuration Service

```powershell
Get-Service GCArcService
```

---

# 32. Check Arc Processes

```powershell
Get-Process |
    Where-Object {
        $_.ProcessName -match "himds|gc"
    }
```

---

# 33. Test the Arc Metadata Endpoint

Azure Arc provides a local metadata service on:

```text
localhost:40342
```

Test it:

```powershell
Invoke-RestMethod `
    -Headers @{Metadata="true"} `
    -Uri "http://localhost:40342/metadata/instance?api-version=2017-08-01"
```

If this fails, investigate:

```text
HIMDS
Arc Agent
Local firewall
Agent health
```

before troubleshooting the user's Entra identity.

---

# 34. Check Arc Identity Information

```powershell
Invoke-RestMethod `
    -Headers @{Metadata="true"} `
    -Uri "http://localhost:40342/metadata/identity/info?api-version=2018-02-01"
```

Look for tenant information.

This helps prove that the machine's Azure identity is functioning.

---

# 35. Check Arc Environment Variables

```powershell
$env:IMDS_ENDPOINT
```

```powershell
$env:IDENTITY_ENDPOINT
```

Typical Arc IMDS endpoint:

```text
http://localhost:40342
```

---

# 36. Check HIMDS Logs

```powershell
Get-Content `
    "$env:ProgramData\AzureConnectedMachineAgent\Log\himds.log" `
    -Tail 100
```

Search for errors:

```powershell
Select-String `
    -Path "$env:ProgramData\AzureConnectedMachineAgent\Log\himds.log" `
    -Pattern "error|fail|timeout|denied" `
    -CaseSensitive:$false
```

---

# 37. Check azcmagent Logs

```powershell
Get-Content `
    "$env:ProgramData\AzureConnectedMachineAgent\Log\azcmagent.log" `
    -Tail 100
```

Search:

```powershell
Select-String `
    -Path "$env:ProgramData\AzureConnectedMachineAgent\Log\azcmagent.log" `
    -Pattern "error|fail|timeout|denied" `
    -CaseSensitive:$false
```

---

# 38. Check Extension Manager Logs

```powershell
Get-Content `
    "$env:ProgramData\GuestConfig\ext_mgr_logs\gc_ext.log" `
    -Tail 100
```

Search for failures:

```powershell
Select-String `
    -Path "$env:ProgramData\GuestConfig\ext_mgr_logs\gc_ext.log" `
    -Pattern "error|fail|exception|timeout" `
    -CaseSensitive:$false
```

---

# 39. Find Extension Logs

```powershell
Get-ChildItem `
    "$env:ProgramData\GuestConfig\extension_logs" `
    -Recurse `
    -ErrorAction SilentlyContinue
```

Search specifically for AAD login related files:

```powershell
Get-ChildItem `
    "$env:ProgramData\GuestConfig" `
    -Recurse `
    -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -match "AADLogin"
    }
```

---

# 40. Collect the Entire Azure Arc Log Bundle

This is a very useful real-world escalation command:

```powershell
azcmagent logs
```

For a complete bundle:

```powershell
azcmagent logs `
    --full `
    --output "$env:USERPROFILE\Desktop\azcmagent-full-logs.zip"
```

Now the engineer has one ZIP file containing the Arc diagnostic data.

---

# 41. Check Microsoft Entra Join State

One of the most important identity commands:

```powershell
dsregcmd /status
```

Look for:

```text
AzureAdJoined : YES
```

For this lab that is the key device state.

---

# 42. Filter dsregcmd Output

Instead of reading everything:

```powershell
dsregcmd /status |
    Select-String `
        "AzureAdJoined|DeviceId|TenantId|AzureAdPrt"
```

This quickly exposes the most useful values.

---

# 43. Check the Entra Device ID

```powershell
dsregcmd /status |
    Select-String "DeviceId"
```

---

# 44. Check the Entra Tenant ID

```powershell
dsregcmd /status |
    Select-String "TenantId"
```

---

# 45. Check the Entra Primary Refresh Token

For user-session authentication troubleshooting:

```powershell
dsregcmd /status |
    Select-String "AzureAdPrt"
```

Depending on the authentication path, this can help diagnose SSO state.

---

# 46. Check Device Registration Events

```powershell
Get-WinEvent `
    -LogName "Microsoft-Windows-User Device Registration/Admin" `
    -MaxEvents 50
```

Show only useful fields:

```powershell
Get-WinEvent `
    -LogName "Microsoft-Windows-User Device Registration/Admin" `
    -MaxEvents 50 |
    Select-Object `
        TimeCreated,
        Id,
        LevelDisplayName,
        Message
```

---

# 47. Show Only Device Registration Errors

```powershell
Get-WinEvent `
    -LogName "Microsoft-Windows-User Device Registration/Admin" `
    -MaxEvents 100 |
    Where-Object {
        $_.LevelDisplayName -eq "Error"
    } |
    Select-Object `
        TimeCreated,
        Id,
        Message
```

---

# 48. Check Entra Authentication Events

```powershell
Get-WinEvent `
    -LogName "Microsoft-Windows-AAD/Operational" `
    -MaxEvents 50
```

Cleaner:

```powershell
Get-WinEvent `
    -LogName "Microsoft-Windows-AAD/Operational" `
    -MaxEvents 50 |
    Select-Object `
        TimeCreated,
        Id,
        LevelDisplayName,
        Message
```

This log is particularly useful when:

```text
Password works elsewhere
but
Entra RDP fails
```

---

# 49. Check Windows System Errors

```powershell
Get-WinEvent `
    -LogName System `
    -MaxEvents 100 |
    Where-Object {
        $_.LevelDisplayName -in @(
            "Error",
            "Critical"
        )
    } |
    Select-Object `
        TimeCreated,
        ProviderName,
        Id,
        Message
```

---

# 50. Check Windows Application Errors

```powershell
Get-WinEvent `
    -LogName Application `
    -MaxEvents 100 |
    Where-Object {
        $_.LevelDisplayName -eq "Error"
    } |
    Select-Object `
        TimeCreated,
        ProviderName,
        Id,
        Message
```

---

# DESKTOP-SIDE POWERSHELL

The following commands should normally be run from the student's workstation.

---

# 51. Verify Azure PowerShell Modules

```powershell
Get-Module -ListAvailable `
    Az.Accounts,
    Az.Resources,
    Az.ConnectedMachine
```

If necessary:

```powershell
Install-Module `
    Az.ConnectedMachine `
    -Scope CurrentUser
```

---

# 52. Authenticate to Azure

```powershell
Connect-AzAccount
```

Then:

```powershell
Get-AzContext
```

---

# 53. Check Available Azure Subscriptions

```powershell
Get-AzSubscription
```

Select one:

```powershell
Set-AzContext `
    -Subscription "YOUR_SUBSCRIPTION_ID"
```

Verify:

```powershell
Get-AzContext
```

---

# 54. Inspect the Arc Machine from Azure

```powershell
Get-AzConnectedMachine `
    -ResourceGroupName "SEIR-ARC-RG" `
    -Name "seir-crosscloud-01"
```

Useful fields:

```powershell
Get-AzConnectedMachine `
    -ResourceGroupName "SEIR-ARC-RG" `
    -Name "seir-crosscloud-01" |
    Format-List `
        Name,
        Location,
        Status,
        ProvisioningState
```

Expected:

```text
Status            : Connected
ProvisioningState : Succeeded
```

---

# 55. List Arc Extensions

```powershell
Get-AzConnectedMachineExtension `
    -ResourceGroupName "SEIR-ARC-RG" `
    -MachineName "seir-crosscloud-01"
```

---

# 56. Inspect AADLoginForWindows

```powershell
Get-AzConnectedMachineExtension `
    -ResourceGroupName "SEIR-ARC-RG" `
    -MachineName "seir-crosscloud-01" `
    -Name "AADLoginForWindows" |
    Format-List
```

Look for:

```text
ProvisioningState : Succeeded
```

---

# 57. Retrieve the Arc Resource ID

```powershell
$Arc = Get-AzConnectedMachine `
    -ResourceGroupName "SEIR-ARC-RG" `
    -Name "seir-crosscloud-01"
```

Then:

```powershell
$Arc.Id
```

Save it:

```powershell
$ArcResourceId = $Arc.Id
```

---

# 58. Check Azure RBAC for the User

```powershell
$UserUPN = "chewbacca@balerica-ai.org"
```

Then:

```powershell
Get-AzRoleAssignment `
    -SignInName $UserUPN |
    Format-Table `
        DisplayName,
        RoleDefinitionName,
        Scope
```

---

# 59. Check Effective Roles Including Groups

This is especially important:

```powershell
Get-AzRoleAssignment `
    -SignInName $UserUPN `
    -ExpandPrincipalGroups |
    Format-Table `
        DisplayName,
        RoleDefinitionName,
        Scope
```

This can reveal permissions inherited through Entra security-group membership.

---

# 60. Search Only for VM Login Roles

```powershell
Get-AzRoleAssignment `
    -SignInName $UserUPN `
    -ExpandPrincipalGroups |
    Where-Object {
        $_.RoleDefinitionName -in @(
            "Virtual Machine User Login",
            "Virtual Machine Administrator Login"
        )
    } |
    Format-Table `
        DisplayName,
        RoleDefinitionName,
        Scope
```

After Gate 7, this should return nothing relevant to the Arc machine.

---

# 61. Check RBAC at the Exact Arc Scope

```powershell
Get-AzRoleAssignment `
    -Scope $ArcResourceId |
    Format-Table `
        DisplayName,
        ObjectType,
        RoleDefinitionName,
        Scope
```

This answers:

> Who has permission on this specific Arc machine?

---

# MICROSOFT GRAPH POWERSHELL

Use these commands to inspect the Entra identity layer.

---

# 62. Connect to Microsoft Graph

```powershell
Connect-MgGraph `
    -Scopes `
        "User.Read.All",
        "Group.Read.All",
        "Device.Read.All"
```

Verify:

```powershell
Get-MgContext
```

---

# 63. Inspect the User

```powershell
Get-MgUser `
    -UserId "chewbacca@balerica-ai.org" `
    -Property `
        Id,
        DisplayName,
        UserPrincipalName,
        UserType,
        AccountEnabled |
    Select-Object `
        Id,
        DisplayName,
        UserPrincipalName,
        UserType,
        AccountEnabled
```

You want:

```text
UserType       : Member
AccountEnabled : True
```

---

# 64. Find the Security Group

```powershell
$Group = Get-MgGroup `
    -Filter "displayName eq 'SEIR_ARC_Users'"
```

Inspect:

```powershell
$Group |
    Select-Object `
        Id,
        DisplayName,
        SecurityEnabled
```

---

# 65. List Group Members

```powershell
Get-MgGroupMember `
    -GroupId $Group.Id `
    -All
```

To inspect the actual users:

```powershell
Get-MgGroupMember `
    -GroupId $Group.Id `
    -All |
    ForEach-Object {
        Get-MgUser `
            -UserId $_.Id `
            -ErrorAction SilentlyContinue
    } |
    Select-Object `
        DisplayName,
        UserPrincipalName,
        Id
```

---

# 66. Check the Entra Device

```powershell
Get-MgDevice `
    -Filter "displayName eq 'seir-crosscloud-01'"
```

Cleaner:

```powershell
Get-MgDevice `
    -Filter "displayName eq 'seir-crosscloud-01'" |
    Select-Object `
        DisplayName,
        DeviceId,
        Id,
        AccountEnabled
```

Compare the Entra:

```text
DeviceId
```

against:

```powershell
dsregcmd /status
```

on the Windows server.

---

# GCP FROM POWERSHELL

PowerShell can also invoke the Google Cloud CLI.

---

# 67. Check GCP Authentication

```powershell
gcloud auth list
```

---

# 68. Check GCP Project

```powershell
gcloud config get-value project
```

---

# 69. Verify the VM

```powershell
gcloud compute instances describe `
    seir-crosscloud-01 `
    --zone us-central1-a
```

---

# 70. Verify GCP Firewall

```powershell
gcloud compute firewall-rules describe `
    seir-allow-rdp
```

---

# 71. Retrieve the VM External IP

```powershell
$VMIP = gcloud compute instances describe `
    seir-crosscloud-01 `
    --zone us-central1-a `
    --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
```

Then:

```powershell
$VMIP
```

Test it:

```powershell
Test-NetConnection `
    $VMIP `
    -Port 3389
```

---

# THE TROUBLESHOOTING LADDER

Students should memorize this sequence.

## Problem: "I cannot log in."

Do not immediately investigate passwords.

Start here:

```powershell
Test-NetConnection $VMIP -Port 3389
```

If:

```text
False
```

investigate:

```text
GCP firewall
Network
External IP
Windows firewall
RDP service
```

If:

```text
True
```

continue.

---

## Next

```powershell
azcmagent show
```

If:

```text
Disconnected
```

investigate Arc.

If:

```text
Connected
```

continue.

---

## Next

```powershell
Get-Service `
    himds,
    GCArcService,
    ExtensionService
```

If services are stopped, investigate the agent.

If running, continue.

---

## Next

```powershell
azcmagent check
```

If Azure endpoints fail, investigate:

```text
DNS
Firewall
Proxy
Internet routing
```

---

## Next

```powershell
dsregcmd /status
```

If:

```text
AzureAdJoined : NO
```

investigate:

```text
AADLoginForWindows
Device registration
Entra connectivity
```

If:

```text
AzureAdJoined : YES
```

continue.

---

## Next

```powershell
Get-AzConnectedMachineExtension `
    -ResourceGroupName "SEIR-ARC-RG" `
    -MachineName "seir-crosscloud-01" `
    -Name "AADLoginForWindows"
```

You want:

```text
Succeeded
```

---

## Next

Check the user:

```powershell
Get-MgUser `
    -UserId "chewbacca@balerica-ai.org"
```

Then group membership.

Then RBAC.

---

# Authentication vs Authorization

If the user successfully authenticates to Microsoft but receives:

```text
Your account is configured to prevent you
from using this device
```

do not immediately reset the password.

Check:

```powershell
Get-AzRoleAssignment `
    -SignInName $UserUPN `
    -ExpandPrincipalGroups |
    Where-Object {
        $_.RoleDefinitionName -match "Virtual Machine"
    }
```

You are probably dealing with:

```text
AUTHORIZATION
```

not:

```text
AUTHENTICATION
```

---

# Commands Students Should NOT Blindly Run

Do not use this as a general troubleshooting technique:

```powershell
azcmagent disconnect
```

Do not blindly run:

```powershell
dsregcmd /leave
```

Do not immediately uninstall:

```text
AADLoginForWindows
```

Do not immediately delete:

```text
Arc Resource
```

Do not immediately delete:

```text
Entra Device
```

Do not immediately delete:

```text
Entra User
```

Those destroy evidence.

Troubleshooting should first answer:

> **What is broken?**

---

# Repair Commands — Only After Diagnosis

If HIMDS is confirmed unhealthy:

```powershell
Restart-Service himds
```

If the Arc extension subsystem is confirmed unhealthy:

```powershell
Restart-Service ExtensionService
```

If machine configuration is confirmed unhealthy:

```powershell
Restart-Service GCArcService
```

All three:

```powershell
Restart-Service `
    himds,
    ExtensionService,
    GCArcService
```

Then:

```powershell
azcmagent show
```

and:

```powershell
azcmagent check
```

again.

---

# Homework Requirement

For each troubleshooting scenario, students must submit:

```text
1. Symptom
2. Layer suspected
3. Commands executed
4. Relevant output
5. Diagnosis
6. Proposed remediation
7. Verification command
```

Example:

```text
SYMPTOM

Unable to RDP.


FIRST TEST

Test-NetConnection 34.x.x.x -Port 3389


RESULT

TcpTestSucceeded : False


DIAGNOSIS

Failure occurs before Entra authentication.


NEXT LAYER

GCP / Windows networking.


DO NOT TROUBLESHOOT

Azure RBAC
Entra password
Group membership
AADLoginForWindows
```

---

# Required Homework Command Set

Every student should become comfortable with at least these commands:

```powershell
hostname
```

```powershell
whoami /all
```

```powershell
Get-ComputerInfo
```

```powershell
Get-NetIPConfiguration
```

```powershell
Get-DnsClientServerAddress
```

```powershell
Resolve-DnsName login.microsoftonline.com
```

```powershell
Test-NetConnection login.microsoftonline.com -Port 443
```

```powershell
Test-NetConnection YOUR_VM_IP -Port 3389
```

```powershell
Get-Service himds,GCArcService,ExtensionService
```

```powershell
azcmagent show
```

```powershell
azcmagent check
```

```powershell
dsregcmd /status
```

```powershell
Get-WinEvent `
    -LogName "Microsoft-Windows-User Device Registration/Admin" `
    -MaxEvents 20
```

```powershell
Get-WinEvent `
    -LogName "Microsoft-Windows-AAD/Operational" `
    -MaxEvents 20
```

```powershell
Get-AzConnectedMachine `
    -ResourceGroupName "SEIR-ARC-RG" `
    -Name "seir-crosscloud-01"
```

```powershell
Get-AzConnectedMachineExtension `
    -ResourceGroupName "SEIR-ARC-RG" `
    -MachineName "seir-crosscloud-01"
```

```powershell
Get-MgUser `
    -UserId "chewbacca@balerica-ai.org"
```

```powershell
Get-AzRoleAssignment `
    -SignInName "chewbacca@balerica-ai.org" `
    -ExpandPrincipalGroups
```

```powershell
azcmagent logs `
    --full `
    --output "$env:USERPROFILE\Desktop\arc-diagnostics.zip"
```

---

# The Job Skill

Do not think:

```text
"I know the command."
```

Think:

```text
"I know which command answers which question."
```

For example:

```text
Is Windows alive?
    |
    v
Get-ComputerInfo
```

```text
Does the server have an IP?
    |
    v
Get-NetIPConfiguration
```

```text
Does DNS work?
    |
    v
Resolve-DnsName
```

```text
Can I reach Microsoft?
    |
    v
Test-NetConnection
```

```text
Is Arc healthy?
    |
    v
azcmagent show
```

```text
Can Arc reach Azure?
    |
    v
azcmagent check
```

```text
Are the Arc services healthy?
    |
    v
Get-Service
```

```text
Is the machine Entra joined?
    |
    v
dsregcmd /status
```

```text
Is AADLoginForWindows healthy?
    |
    v
Get-AzConnectedMachineExtension
```

```text
Does the user exist?
    |
    v
Get-MgUser
```

```text
Is the user authorized?
    |
    v
Get-AzRoleAssignment
```

That is troubleshooting.

Not:

```text
CLICK RANDOM THINGS UNTIL IT WORKS
```
