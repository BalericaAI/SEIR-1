# SEIR Foundations — Module 1

# Balerica Bank Cross-Cloud IAM

# Gate 01 — Build AWS Managed Microsoft AD

## Objective

In this gate, students will create the Windows identity foundation for the Balerica Bank environment:

```text
AWS Managed Microsoft AD
```

The directory will eventually provide:

- Windows domain membership
- Kerberos authentication
- LDAP directory services
- Computer identities
- Domain users and groups
- Windows service identities
- Group Policy capabilities

The target directory will be:

```text
corp.balericabank.com
```

with the NetBIOS name:

```text
BALBANK
```

At the end of Gate 01:

```text
AWS
 |
 v
Balerica Bank VPC
 |
 +---------------------------+
 |                           |
 v                           v
Private Subnet A        Private Subnet B
AZ-A                    AZ-B
 |                           |
 v                           v
Managed AD DC-1         Managed AD DC-2
       \                   /
        \                 /
         +---------------+
                 |
                 v
       corp.balericabank.com
```

No EC2 machine will be joined yet.

That begins in Gate 02.

---

# Gate 01 Mental Model

Remember:

```text
Microsoft Entra
=
HUMAN WORKFORCE IDENTITY
```

Later:

```text
Entra
  |
  v
AWS IAM Identity Center
```

But this Gate creates:

```text
AWS Managed Microsoft AD
=
WINDOWS DOMAIN IDENTITY
```

These are different systems with different jobs.

---

# Gate 01.1 — Verify AWS Authentication

From the student workstation:

```bash
aws sts get-caller-identity
```

Expected conceptually:

```json
{
    "UserId": "...",
    "Account": "123456789012",
    "Arn": "..."
}
```

Record the AWS Account ID.

Optional:

```bash
AWS_ACCOUNT_ID=$(aws sts get-caller-identity \
    --query Account \
    --output text)
```

Verify:

```bash
echo "$AWS_ACCOUNT_ID"
```

---

# Gate 01.2 — Verify the AWS Region

Check:

```bash
aws configure get region
```

For the lab, define the region explicitly.

Example:

```bash
AWS_REGION="us-east-1"
```

Use the region selected for the existing Balerica Bank environment.

Do not accidentally deploy the directory into a different region from the lab workload.

---

# Gate 01.3 — Identify the Balerica Bank VPC

List VPCs:

```bash
aws ec2 describe-vpcs \
    --region "$AWS_REGION" \
    --query "Vpcs[].{
        VpcId:VpcId,
        CIDR:CidrBlock,
        Default:IsDefault
    }" \
    --output table
```

Identify the VPC that will contain:

```text
BALBANK-APP01
```

and the AWS Managed Microsoft AD.

For this class, keep the directory and application workload in the **same VPC**.

This simplifies:

```text
Routing

DNS

Domain Join

Kerberos

LDAP

Troubleshooting
```

---

# Gate 01.4 — Save the VPC ID

Example:

```bash
VPC_ID="vpc-xxxxxxxxxxxxxxxxx"
```

Verify:

```bash
echo "$VPC_ID"
```

---

# Gate 01.5 — Inspect VPC Tenancy

Run:

```bash
aws ec2 describe-vpcs \
    --vpc-ids "$VPC_ID" \
    --region "$AWS_REGION" \
    --query "Vpcs[0].InstanceTenancy" \
    --output text
```

Expected:

```text
default
```

AWS Managed Microsoft AD requires a VPC using default hardware tenancy.

If the result is not:

```text
default
```

stop here.

---

# Gate 01.6 — Inspect the VPC CIDR

Run:

```bash
aws ec2 describe-vpcs \
    --vpc-ids "$VPC_ID" \
    --region "$AWS_REGION" \
    --query "Vpcs[0].CidrBlock" \
    --output text
```

Example:

```text
10.20.0.0/16
```

Record the CIDR.

Do not use:

```text
198.18.0.0/15
```

for the directory VPC.

AWS reserves that range for internal Directory Service management networking.

---

# Gate 01.7 — List Candidate Subnets

Run:

```bash
aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --region "$AWS_REGION" \
    --query "Subnets[].{
        SubnetId:SubnetId,
        AZ:AvailabilityZone,
        CIDR:CidrBlock,
        PublicIP:MapPublicIpOnLaunch
    }" \
    --output table
```

Students should identify two subnets.

Recommended:

```text
Private Subnet A

Private Subnet B
```

The subnets must be in different Availability Zones.

Example:

```text
subnet-aaaa
us-east-1a
10.20.10.0/24


subnet-bbbb
us-east-1b
10.20.20.0/24
```

---

# Gate 01.8 — Define the Directory Subnets

Example:

```bash
SUBNET_A="subnet-aaaaaaaaaaaaaaaaa"
SUBNET_B="subnet-bbbbbbbbbbbbbbbbb"
```

---

# Gate 01.9 — Prove the Subnets Are in Different AZs

Run:

```bash
aws ec2 describe-subnets \
    --subnet-ids "$SUBNET_A" "$SUBNET_B" \
    --region "$AWS_REGION" \
    --query "Subnets[].{
        Subnet:SubnetId,
        AZ:AvailabilityZone,
        CIDR:CidrBlock
    }" \
    --output table
```

Expected:

```text
SUBNET                     AZ
-------------------------  ----------
subnet-aaaaaaaa            us-east-1a
subnet-bbbbbbbb            us-east-1b
```

The AZ values must differ.

---

# Why Two Availability Zones?

We are not manually creating the domain controllers.

AWS Directory Service will create the managed directory infrastructure.

Conceptually:

```text
Availability Zone A
        |
        v
Domain Controller 1


Availability Zone B
        |
        v
Domain Controller 2
```

This provides directory redundancy.

Students should understand that Active Directory is infrastructure.

If authentication is critical to an enterprise, one domain controller is not sufficient architecture.

---

# Gate 01.10 — Verify the Subnets Belong to the Same VPC

Run:

```bash
aws ec2 describe-subnets \
    --subnet-ids "$SUBNET_A" "$SUBNET_B" \
    --region "$AWS_REGION" \
    --query "Subnets[].VpcId" \
    --output text
```

Both values should equal:

```text
$VPC_ID
```

---

# Gate 01.11 — Inspect Route Tables

Determine which route table serves each subnet:

```bash
aws ec2 describe-route-tables \
    --filters "Name=association.subnet-id,Values=$SUBNET_A,$SUBNET_B" \
    --region "$AWS_REGION" \
    --output table
```

The directory itself does not require you to expose the domain controllers to the public Internet.

Do not create:

```text
Public Domain Controllers
```

for this lab.

---

# Gate 01.12 — Directory Naming

We will use:

```text
DNS Domain:

corp.balericabank.com
```

and:

```text
NetBIOS Name:

BALBANK
```

This gives future identities such as:

```text
BALBANK\Chewbacca
```

and computers such as:

```text
BALBANK-APP01$
```

The DNS name:

```text
corp.balericabank.com
```

does not need to be a publicly resolvable Internet DNS zone.

It represents the internal Active Directory namespace.

---

# Gate 01.13 — Important Route 53 Warning

Do not create a Route 53 Private Hosted Zone using exactly the same namespace:

```text
corp.balericabank.com
```

without intentionally designing DNS integration.

AWS Managed Microsoft AD owns DNS resolution for its AD namespace.

For the lab:

```text
corp.balericabank.com
```

is the Active Directory namespace.

---

# Gate 01.14 — Choose the Directory Edition

For this lab use:

```text
Standard Edition
```

We are teaching:

```text
Active Directory

Domain Join

Kerberos

LDAP

Windows Authentication

Enterprise IAM
```

not large-scale directory sizing.

---

# Gate 01.15 — Create the Directory

For the first manual round, the AWS Console is acceptable and provides a useful visualization.

Navigate:

```text
AWS Console
    |
    v
Directory Service
    |
    v
Directories
    |
    v
Set up directory
```

Choose:

```text
AWS Managed Microsoft AD
```

Then choose:

```text
Create new AWS managed AD domain
```

---

# Directory Information

Use:

```text
Edition:

Standard
```

```text
Directory DNS Name:

corp.balericabank.com
```

```text
NetBIOS Name:

BALBANK
```

Optional description:

```text
SEIR Foundations - Balerica Bank Managed AD
```

---

# Administrator Password

Create a strong directory administrator password.

Do not place the password in:

```text
GitHub

README files

Screenshots

Slack

Jira

Source code

Class chat
```

The initial managed directory administrator account is:

```text
Admin
```

The password is used later for directory administration.

---

# Gate 01.16 — Select the VPC

Choose:

```text
VPC:

Balerica Bank VPC
```

Then select:

```text
Subnet A
```

and:

```text
Subnet B
```

The two subnets must belong to different Availability Zones.

---

# Gate 01.17 — Review Before Creation

Before clicking:

```text
Create directory
```

verify:

```text
Directory Type
AWS Managed Microsoft AD

Edition
Standard

DNS Name
corp.balericabank.com

NetBIOS
BALBANK

VPC
Correct Balerica VPC

Subnet 1
Private subnet in AZ-A

Subnet 2
Private subnet in AZ-B
```

---

# Gate 01.18 — Create the Directory

Choose:

```text
Create directory
```

AWS will begin provisioning the managed directory.

The status will initially be similar to:

```text
Creating
```

Do not proceed to Gate 02 yet.

---

# OPTIONAL — CLI Creation

Students performing the second implementation may create the directory using the AWS CLI.

First collect the password without typing it directly into shell history.

## Bash

```bash
read -s -p "Directory Admin Password: " DS_PASSWORD
echo
```

Then:

```bash
aws ds create-microsoft-ad \
    --name "corp.balericabank.com" \
    --short-name "BALBANK" \
    --password "$DS_PASSWORD" \
    --description "SEIR Foundations Balerica Bank Managed AD" \
    --edition Standard \
    --vpc-settings \
        VpcId="$VPC_ID",SubnetIds="$SUBNET_A","$SUBNET_B" \
    --region "$AWS_REGION"
```

Immediately clear the shell variable:

```bash
unset DS_PASSWORD
```

The output should contain a Directory ID similar to:

```text
d-xxxxxxxxxx
```

Save it:

```bash
DIRECTORY_ID="d-xxxxxxxxxx"
```

---

# Gate 01.19 — List Directories

Run:

```bash
aws ds describe-directories \
    --region "$AWS_REGION" \
    --query "DirectoryDescriptions[].{
        ID:DirectoryId,
        Name:Name,
        ShortName:ShortName,
        Edition:Edition,
        Stage:Stage
    }" \
    --output table
```

Locate:

```text
corp.balericabank.com
```

---

# Gate 01.20 — Store the Directory ID

Automatically:

```bash
DIRECTORY_ID=$(aws ds describe-directories \
    --region "$AWS_REGION" \
    --query "DirectoryDescriptions[?Name=='corp.balericabank.com'].DirectoryId | [0]" \
    --output text)
```

Verify:

```bash
echo "$DIRECTORY_ID"
```

Expected:

```text
d-xxxxxxxxxx
```

---

# Gate 01.21 — Check Directory State

Run:

```bash
aws ds describe-directories \
    --directory-ids "$DIRECTORY_ID" \
    --region "$AWS_REGION" \
    --query "DirectoryDescriptions[0].{
        Name:Name,
        ShortName:ShortName,
        Edition:Edition,
        Stage:Stage
    }" \
    --output table
```

During provisioning:

```text
Stage
--------
Creating
```

Final expected result:

```text
Stage
--------
Active
```

Do not proceed until:

```text
Active
```

---

# Gate 01.22 — Record the DNS Server Addresses

Run:

```bash
aws ds describe-directories \
    --directory-ids "$DIRECTORY_ID" \
    --region "$AWS_REGION" \
    --query "DirectoryDescriptions[0].DnsIpAddrs" \
    --output table
```

You should receive two IP addresses.

Example:

```text
10.20.10.x

10.20.20.x
```

Record them.

These are extremely important.

Later:

```text
BALBANK-APP01
       |
       | DNS
       v
Managed AD DNS
       |
       v
corp.balericabank.com
```

Active Directory depends heavily on DNS.

---

# Gate 01.23 — Display the Full Directory Configuration

Run:

```bash
aws ds describe-directories \
    --directory-ids "$DIRECTORY_ID" \
    --region "$AWS_REGION" \
    --query "DirectoryDescriptions[0].{
        DirectoryId:DirectoryId,
        Name:Name,
        ShortName:ShortName,
        Edition:Edition,
        Stage:Stage,
        VpcId:VpcSettings.VpcId,
        SubnetIds:VpcSettings.SubnetIds,
        AvailabilityZones:VpcSettings.AvailabilityZones,
        DnsServers:DnsIpAddrs
    }" \
    --output json
```

Students should save this output as evidence.

---

# Gate 01.24 — Verify the Directory VPC

Run:

```bash
aws ds describe-directories \
    --directory-ids "$DIRECTORY_ID" \
    --region "$AWS_REGION" \
    --query "DirectoryDescriptions[0].VpcSettings.VpcId" \
    --output text
```

Expected:

```text
$VPC_ID
```

---

# Gate 01.25 — Verify Both Directory Subnets

Run:

```bash
aws ds describe-directories \
    --directory-ids "$DIRECTORY_ID" \
    --region "$AWS_REGION" \
    --query "DirectoryDescriptions[0].VpcSettings.SubnetIds" \
    --output table
```

Expected:

```text
SUBNET_A

SUBNET_B
```

---

# Gate 01.26 — Verify Availability Zones

Run:

```bash
aws ds describe-directories \
    --directory-ids "$DIRECTORY_ID" \
    --region "$AWS_REGION" \
    --query "DirectoryDescriptions[0].VpcSettings.AvailabilityZones" \
    --output table
```

You should see two different AZs.

Example:

```text
us-east-1a

us-east-1b
```

---

# Gate 01.27 — Inspect Directory Service Network Interfaces

AWS creates network interfaces that allow resources in your VPC to communicate with the managed directory.

Run:

```bash
aws ec2 describe-network-interfaces \
    --region "$AWS_REGION" \
    --filters \
        "Name=vpc-id,Values=$VPC_ID" \
        "Name=description,Values=*${DIRECTORY_ID}*" \
    --query "NetworkInterfaces[].{
        ENI:NetworkInterfaceId,
        PrivateIP:PrivateIpAddress,
        Subnet:SubnetId,
        AZ:AvailabilityZone,
        Description:Description
    }" \
    --output table
```

Do not delete Directory Service ENIs.

They are part of the managed service's connectivity architecture.

---

# Gate 01.28 — Understand What AWS Owns

Students are not creating normal EC2 domain controllers.

Conceptually:

```text
YOUR AWS ACCOUNT

Balerica VPC
     |
     +-- Directory Service ENI
     |
     +-- Directory Service ENI


AWS MANAGED DIRECTORY INFRASTRUCTURE

DC-1
DC-2
```

AWS manages the underlying domain-controller infrastructure.

Students manage the directory logically.

---

# Gate 01.29 — Understand the Three Identity Systems

This distinction is mandatory before Gate 02.

## AWS IAM Identity

Example:

```text
BalericaLegacyBankEC2Role
```

Purpose:

```text
AWS API authorization
```

---

## AWS Managed Microsoft AD Identity

Examples:

```text
BALBANK\Chewbacca

BALBANK-APP01$

BALBANK\svc-balerica
```

Purpose:

```text
Windows Authentication

Kerberos

LDAP

Computer Trust

Group Policy
```

---

## Microsoft Entra Identity

Example:

```text
chewbacca@balerica-ai.org
```

Purpose later in this lab:

```text
Human Workforce Identity

SAML Authentication

SCIM Provisioning

AWS IAM Identity Center Access
```

---

# The Separation Is Intentional

Eventually:

```text
Microsoft Entra
     |
     | SAML + SCIM
     v
AWS IAM Identity Center
     |
     v
AWS Permission Sets
```

while:

```text
AWS Managed Microsoft AD
     |
     | Kerberos / LDAP
     v
BALBANK-APP01
```

These systems solve different problems.

---

# Gate 01.30 — Final Verification Command

Run:

```bash
aws ds describe-directories \
    --directory-ids "$DIRECTORY_ID" \
    --region "$AWS_REGION" \
    --query "DirectoryDescriptions[0].{
        Directory:Name,
        NetBIOS:ShortName,
        Edition:Edition,
        Status:Stage,
        VPC:VpcSettings.VpcId,
        AZs:VpcSettings.AvailabilityZones,
        Subnets:VpcSettings.SubnetIds,
        DNS:DnsIpAddrs
    }" \
    --output json
```

Expected conceptually:

```json
{
    "Directory": "corp.balericabank.com",
    "NetBIOS": "BALBANK",
    "Edition": "Standard",
    "Status": "Active",
    "VPC": "vpc-...",
    "AZs": [
        "us-east-1a",
        "us-east-1b"
    ],
    "Subnets": [
        "subnet-...",
        "subnet-..."
    ],
    "DNS": [
        "10.x.x.x",
        "10.x.x.x"
    ]
}
```

---

# Gate 01 Screenshot Evidence

Students should capture evidence showing:

## Screenshot 1

AWS Directory Service console showing:

```text
corp.balericabank.com

AWS Managed Microsoft AD

Standard

Active
```

---

## Screenshot 2

Directory networking showing:

```text
VPC

Subnet A

Subnet B

Availability Zone A

Availability Zone B
```

---

## Screenshot 3

CLI output showing:

```text
Directory ID

DNS IP addresses

Stage = Active
```

---

# Gate 01 Deliverables

Students submit:

```text
Directory DNS Name

NetBIOS Name

Directory ID

Edition

AWS Region

VPC ID

Subnet A ID

Subnet A AZ

Subnet B ID

Subnet B AZ

DNS Server 1

DNS Server 2
```

Do not submit:

```text
Admin password
```

---

# Gate 01 Success Criteria

Gate 01 is complete when:

- [ ] AWS CLI authentication works.
- [ ] Correct AWS account is selected.
- [ ] Correct AWS region is selected.
- [ ] Correct Balerica Bank VPC is identified.
- [ ] VPC tenancy is `default`.
- [ ] VPC CIDR is valid for Directory Service.
- [ ] Two directory subnets exist.
- [ ] Both subnets belong to the same VPC.
- [ ] Subnets reside in different Availability Zones.
- [ ] AWS Managed Microsoft AD was selected.
- [ ] A new AWS managed AD domain was created.
- [ ] DNS domain is `corp.balericabank.com`.
- [ ] NetBIOS name is `BALBANK`.
- [ ] Edition is Standard.
- [ ] Directory status is `Active`.
- [ ] Directory ID was recorded.
- [ ] Two directory DNS addresses were recorded.
- [ ] VPC and subnet assignments were verified.
- [ ] Students understand that AWS Managed AD is not the Entra/IAM Identity Center workforce SSO system.

---

# Stop Condition

If:

```text
Stage != Active
```

stop.

Do not launch or domain-join:

```text
BALBANK-APP01
```

Do not troubleshoot:

```text
Kerberos

Windows login

Domain membership

SAML

SCIM

IAM Identity Center

Entra groups
```

Those layers do not exist yet.

At Gate 01, troubleshoot only:

```text
AWS Directory Service

VPC

Subnet selection

Availability Zones

Directory creation
```

---

# Gate 01 Final Architecture

```text
                 AWS
                  |
                  v
          BALERICA BANK VPC
                  |
       +----------+----------+
       |                     |
       v                     v
Private Subnet A       Private Subnet B
       |                     |
       v                     v
     DC-1                  DC-2
       |                     |
       +----------+----------+
                  |
                  v
        corp.balericabank.com
                  |
               BALBANK
```

The following does **not** exist yet:

```text
BALBANK-APP01
      |
      X
      |
corp.balericabank.com
```

That is Gate 02.

---

# Next Gate

Gate 02 will introduce the first actual domain member:

```text
BALBANK-APP01
      |
      | Secure Domain Join
      v
corp.balericabank.com
```

and students will finally get to distinguish:

```text
EC2 IAM ROLE
```

from:

```text
WINDOWS COMPUTER ACCOUNT
```

which are two completely different identities attached to the same workload.
