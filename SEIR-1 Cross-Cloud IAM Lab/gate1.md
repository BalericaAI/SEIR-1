
# SEIR-1 Cross-Cloud IAM Lab

# Gate 1 — Deploy and Verify the GCP Windows VM

## Objective

In this gate, you will create a **Windows Server 2025 virtual machine in Google Cloud Platform** using the Google Cloud CLI.

At the end of this gate, you must prove that:

- The VM exists in GCP.
- The VM is running Windows Server 2025.
- The VM has network connectivity.
- RDP is reachable from your workstation.
- You can log into Windows using a temporary local administrator account.
- Azure has **not** been connected yet.

The goal is to establish a known-good GCP baseline.

---

# Architecture

At the end of Gate 1:

```text
Student Workstation
        |
        | gcloud CLI
        v
Google Cloud Platform
        |
        v
Compute Engine
        |
        v
Windows Server 2025
seir-crosscloud-01
```

Azure is not part of the architecture yet.

```text
Microsoft Entra ID

        X

Not connected yet
```

---

# Gate 1.1 — Verify GCP CLI Authentication

Run:

```bash
gcloud auth list
```

You should see an active account:

```text
ACTIVE  ACCOUNT
*       student@example.com
```

If no account is active:

```bash
gcloud auth login
```

Complete the authentication process.

---

# Gate 1.2 — Verify the GCP Project

Run:

```bash
gcloud config get-value project
```

Confirm that the correct SEIR project is selected.

If necessary, list available projects:

```bash
gcloud projects list
```

Then select the correct project:

```bash
gcloud config set project YOUR_PROJECT_ID
```

Verify:

```bash
gcloud config get-value project
```

---

# Gate 1.3 — Verify the Compute Engine API

Run:

```bash
gcloud services list --enabled \
    --filter="name:compute.googleapis.com"
```

You should see:

```text
compute.googleapis.com
```

If Compute Engine is not enabled:

```bash
gcloud services enable compute.googleapis.com
```

---

# Gate 1.4 — Select a Zone

View available zones:

```bash
gcloud compute zones list
```

For this lab, you may use:

```text
us-central1-a
```

Set the default zone:

```bash
gcloud config set compute/zone us-central1-a
```

Verify:

```bash
gcloud config get-value compute/zone
```

Expected:

```text
us-central1-a
```

---

# Gate 1.5 — Verify the Windows Server 2025 Image

Before creating the VM, prove that the image family exists.

Run:

```bash
gcloud compute images describe-from-family windows-2025 \
    --project=windows-cloud
```

Look for:

```text
family: windows-2025
```

The exact image name will change as Google publishes updated Windows images.

For this reason, use the **image family** rather than hard-coding a specific image release.

---

# Gate 1.6 — Inspect Available Networks

Do not assume that a network named `default` exists.

Run:

```bash
gcloud compute networks list
```

Then inspect the available subnets:

```bash
gcloud compute networks subnets list
```

Choose a network and subnet appropriate for your project.

Example:

```text
Network:
default

Subnet:
default
```

Your environment may use different values.

---

# Gate 1.7 — Define the Lab Values

For the examples below:

```text
VM Name:
seir-crosscloud-01

Zone:
us-central1-a

Machine Type:
e2-standard-2

Windows Image:
windows-2025

Image Project:
windows-cloud
```

The VM requires enough resources to operate Windows Server comfortably.

---

# Gate 1.8 — Create the VM

If using the default network:

```bash
gcloud compute instances create seir-crosscloud-01 \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --image-project=windows-cloud \
    --image-family=windows-2025 \
    --boot-disk-size=50GB \
    --boot-disk-type=pd-balanced \
    --tags=seir-rdp
```

If using a custom network and subnet:

```bash
gcloud compute instances create seir-crosscloud-01 \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --network=YOUR_NETWORK \
    --subnet=YOUR_SUBNET \
    --image-project=windows-cloud \
    --image-family=windows-2025 \
    --boot-disk-size=50GB \
    --boot-disk-type=pd-balanced \
    --tags=seir-rdp
```

---

# Gate 1.9 — Verify the VM Exists

Run:

```bash
gcloud compute instances list
```

You should see:

```text
NAME                  ZONE            MACHINE_TYPE     STATUS
seir-crosscloud-01    us-central1-a   e2-standard-2   RUNNING
```

---

# Gate 1.10 — Inspect the VM

Run:

```bash
gcloud compute instances describe seir-crosscloud-01 \
    --zone=us-central1-a
```

Verify:

```text
name

zone

machineType

networkInterfaces

disks

status
```

The important value is:

```text
status: RUNNING
```

---

# Gate 1.11 — Retrieve the External IP Address

Run:

```bash
gcloud compute instances describe seir-crosscloud-01 \
    --zone=us-central1-a \
    --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
```

Record this IP address.

Example:

```text
34.xxx.xxx.xxx
```

This will be used for RDP.

---

# Gate 1.12 — Restrict RDP to Your Workstation

Do **not** expose TCP 3389 to the entire Internet.

Do not use:

```text
0.0.0.0/0
```

for this lab.

Determine your workstation's public IP using an appropriate trusted method.

Suppose your public IP is:

```text
203.0.113.25
```

Your source CIDR becomes:

```text
203.0.113.25/32
```

Create the firewall rule:

```bash
gcloud compute firewall-rules create seir-allow-rdp \
    --network=YOUR_NETWORK \
    --allow=tcp:3389 \
    --source-ranges=203.0.113.25/32 \
    --target-tags=seir-rdp
```

If your network is named `default`:

```bash
gcloud compute firewall-rules create seir-allow-rdp \
    --network=default \
    --allow=tcp:3389 \
    --source-ranges=203.0.113.25/32 \
    --target-tags=seir-rdp
```

---

# Gate 1.13 — Verify the Firewall Rule

Run:

```bash
gcloud compute firewall-rules describe seir-allow-rdp
```

Verify:

```text
allowed:
tcp:3389

sourceRanges:
YOUR_PUBLIC_IP/32
```

The VM has the network tag:

```text
seir-rdp
```

and the firewall rule targets:

```text
seir-rdp
```

Therefore:

```text
Your Workstation
       |
       | TCP 3389
       v
seir-allow-rdp
       |
       v
seir-crosscloud-01
```

---

# Gate 1.14 — Create the Temporary Local Windows Administrator

At this point, Microsoft Entra is **not** involved.

We need a local Windows account so that we can verify that the VM works before connecting Azure.

Run:

```bash
gcloud compute reset-windows-password seir-crosscloud-01 \
    --zone=us-central1-a \
    --user=seir-local-admin
```

You will receive a warning similar to:

```text
Would you like to set or reset the password?
```

Answer:

```text
Y
```

Google will return:

```text
ip_address:

password:

username:
```

Save these credentials temporarily.

Do not paste the password into:

```text
GitHub

Class chat

README files

Screenshots

Source code
```

---

# Why Are We Creating a Local Account?

The account:

```text
seir-local-admin
```

is a **break-glass / bootstrap account**.

It proves that Windows works before Entra authentication is introduced.

Current architecture:

```text
GCP Windows VM
      |
      v
Local Windows Security Database
      |
      v
seir-local-admin
```

Later:

```text
Microsoft Entra
      |
      v
Azure Arc
      |
      v
GCP Windows VM
```

These are intentionally different authentication paths.

---

# Gate 1.15 — Test TCP 3389

## Windows PowerShell

Run:

```powershell
Test-NetConnection `
    -ComputerName YOUR_VM_EXTERNAL_IP `
    -Port 3389
```

Expected:

```text
TcpTestSucceeded : True
```

If:

```text
TcpTestSucceeded : False
```

do not continue.

Troubleshoot:

```text
VM status

External IP

VPC firewall

Network tag

Source IP

Windows boot state
```

---

# Gate 1.16 — RDP into the VM

On Windows:

```powershell
mstsc.exe
```

Enter the VM's external IP.

Use:

```text
Username:
seir-local-admin
```

and the password generated by:

```bash
gcloud compute reset-windows-password
```

Accept the RDP certificate warning for the lab VM if appropriate.

---

# Gate 1.17 — Verify Windows From Inside the VM

After connecting, open PowerShell inside the Windows Server.

Run:

```powershell
hostname
```

Expected:

```text
SEIR-CROSSCLOUD-01
```

Then:

```powershell
Get-ComputerInfo |
    Select-Object `
        WindowsProductName,
        WindowsVersion,
        OsName,
        OsArchitecture
```

Confirm that the machine is running Windows Server 2025.

---

# Gate 1.18 — Verify Network Connectivity From the VM

Inside the VM:

```powershell
Test-NetConnection www.microsoft.com -Port 443
```

Expected:

```text
TcpTestSucceeded : True
```

Then:

```powershell
Test-NetConnection management.azure.com -Port 443
```

Expected:

```text
TcpTestSucceeded : True
```

This is important because Azure Arc will later require outbound connectivity from the GCP VM to Azure services.

---

# Gate 1.19 — Verify Google Metadata Access

Inside the VM:

```powershell
Invoke-WebRequest `
    -Headers @{"Metadata-Flavor"="Google"} `
    -Uri "http://metadata.google.internal/computeMetadata/v1/instance/name"
```

The response should identify:

```text
seir-crosscloud-01
```

This proves that the machine still has access to the Google Compute Engine metadata service.

---

# Gate 1.20 — Verify Azure Has Not Been Added Yet

Inside Windows, check whether the Azure Connected Machine agent already exists:

```powershell
Get-Service himds -ErrorAction SilentlyContinue
```

For a new machine, there should normally be no result.

Also try:

```powershell
Get-Command azcmagent `
    -ErrorAction SilentlyContinue
```

Again, there should normally be no result.

At this point:

```text
Azure Arc Agent:       NOT INSTALLED

Entra Joined:          NO

Azure RBAC Login:      NO
```

That is expected.

---

# Final Gate 1 Architecture

You should now have:

```text
                   STUDENT WORKSTATION
                           |
                    gcloud CLI / RDP
                           |
                           v
                 GOOGLE CLOUD PLATFORM
                           |
                           v
                     Compute Engine
                           |
                           v
                  Windows Server 2025
                  seir-crosscloud-01
                           |
                           +---- Local account:
                           |     seir-local-admin
                           |
                           +---- Outbound HTTPS:
                                 WORKING
```

Microsoft is not yet controlling this machine.

---

# Gate 1 Verification Commands

Run from your workstation:

```bash
gcloud auth list
```

```bash
gcloud config get-value project
```

```bash
gcloud compute instances list
```

```bash
gcloud compute instances describe seir-crosscloud-01 \
    --zone=us-central1-a
```

Then from Windows PowerShell inside the VM:

```powershell
hostname
```

```powershell
Get-ComputerInfo |
    Select-Object `
        WindowsProductName,
        OsName,
        OsArchitecture
```

```powershell
Test-NetConnection management.azure.com -Port 443
```

---

# Success Criteria

Gate 1 is complete when:

- [ ] `gcloud` authentication works.
- [ ] The correct GCP project is selected.
- [ ] Compute Engine is enabled.
- [ ] The Windows Server 2025 image is available.
- [ ] The VM exists.
- [ ] The VM status is `RUNNING`.
- [ ] The VM has network connectivity.
- [ ] RDP is restricted to the student's source IP.
- [ ] TCP 3389 is reachable.
- [ ] `seir-local-admin` exists.
- [ ] The student can RDP into the machine.
- [ ] Windows Server 2025 is confirmed.
- [ ] Outbound HTTPS access to Azure works.
- [ ] Azure Arc is not yet installed.

---

# Failure Rule

If you cannot successfully RDP into the GCP VM using:

```text
seir-local-admin
```

**stop here.**

Do not install Azure Arc.

Do not troubleshoot Entra.

Do not create Azure role assignments.

At this stage, the problem is still:

```text
GCP

Networking

Windows

or

Local Authentication
```

Azure has not entered the architecture yet.

---

# Next Gate

Gate 2 will change the architecture from:

```text
GCP VM
```

to:

```text
GCP VM
   |
   | Azure Connected Machine Agent
   v
Azure Arc
```

The VM will remain physically hosted in Google Cloud.

Azure will gain a management-plane representation of that machine.
