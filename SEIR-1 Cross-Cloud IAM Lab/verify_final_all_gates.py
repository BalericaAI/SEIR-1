#!/usr/bin/env python3

"""
SEIR-1 Cross-Cloud IAM
FINAL ALL-GATES VERIFICATION
Gates 1 through 7

Run this script from the student's DESKTOP after completing Gate 7.

FINAL EXPECTED STATE
--------------------

GCP VM                         RUNNING
Windows Server 2025           YES
RDP TCP/3389                  REACHABLE
Azure Arc                     CONNECTED
Managed Identity              PRESENT
AADLoginForWindows            SUCCEEDED
Entra Device                  PRESENT
Entra User                    PRESENT / ENABLED / MEMBER
Security Group                PRESENT
User in Security Group        YES

Direct VM Login Role          NONE
Group VM Login Role           NONE
Inherited VM Login Role       NONE
Effective VM Login Role       NONE

Therefore:

NETWORK                       WORKING
COMPUTE                       WORKING
IDENTITY                      WORKING
AUTHORIZATION                 REVOKED

This script is READ-ONLY.

It does not:
    create resources
    delete resources
    modify RBAC
    modify groups
    change passwords
    connect/disconnect Azure Arc
    modify GCP firewall rules


Requirements
------------

Python 3.10+
gcloud CLI
Azure CLI
Azure CLI connectedmachine extension

Example:

python verify_final_all_gates.py \
    --user-upn chewbacca@balerica-ai.org

Full example:

python verify_final_all_gates.py \
    --project-id seir-1-490120 \
    --vm-name seir-crosscloud-01 \
    --zone us-central1-a \
    --resource-group SEIR-ARC-RG \
    --arc-name seir-crosscloud-01 \
    --entra-device-name seir-crosscloud-01 \
    --user-upn chewbacca@balerica-ai.org \
    --group-name SEIR_ARC_Users
"""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys

from dataclasses import dataclass, asdict
from datetime import datetime, timezone


# =====================================================================
# RESULT MODEL
# =====================================================================

@dataclass
class CheckResult:
    gate: str
    check: str
    status: str
    detail: str = ""


RESULTS = []


# =====================================================================
# COLORS
# =====================================================================

USE_COLOR = sys.stdout.isatty() and not os.getenv("NO_COLOR")

if USE_COLOR:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
else:
    GREEN = ""
    RED = ""
    YELLOW = ""
    CYAN = ""
    BOLD = ""
    RESET = ""


# =====================================================================
# OUTPUT HELPERS
# =====================================================================

def banner(text):
    print()
    print("=" * 80)
    print(f"{BOLD}{text}{RESET}")
    print("=" * 80)


def record(gate, check, status, detail=""):

    result = CheckResult(
        gate=gate,
        check=check,
        status=status,
        detail=detail
    )

    RESULTS.append(result)

    if status == "PASS":
        marker = f"{GREEN}[PASS]{RESET}"

    elif status == "FAIL":
        marker = f"{RED}[FAIL]{RESET}"

    elif status == "MANUAL":
        marker = f"{YELLOW}[MANUAL]{RESET}"

    else:
        marker = f"{YELLOW}[ERROR]{RESET}"

    print(f"{marker:<16}{check}")

    if detail:
        print(f"                {detail}")


def passed(gate, check, detail=""):
    record(gate, check, "PASS", detail)


def failed(gate, check, detail=""):
    record(gate, check, "FAIL", detail)


def manual(gate, check, detail=""):
    record(gate, check, "MANUAL", detail)


def error(gate, check, detail=""):
    record(gate, check, "ERROR", detail)


# =====================================================================
# COMMAND HELPERS
# =====================================================================

class CommandFailure(Exception):
    pass


def run_command(command, timeout=60):

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

    except FileNotFoundError:

        raise CommandFailure(
            f"Command not found: {command[0]}"
        )

    except subprocess.TimeoutExpired:

        raise CommandFailure(
            f"Command timed out: {' '.join(command)}"
        )

    if result.returncode != 0:

        message = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Unknown command failure"
        )

        raise CommandFailure(message)

    return result.stdout.strip()


def run_json(command, timeout=60):

    output = run_command(
        command,
        timeout
    )

    if not output:
        return None

    try:
        return json.loads(output)

    except json.JSONDecodeError as exc:

        raise CommandFailure(
            f"Expected JSON but received:\n{output}"
        ) from exc


def path_name(value):

    if not value:
        return ""

    return value.rstrip("/").split("/")[-1]


# =====================================================================
# ARGUMENTS
# =====================================================================

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Verify the final state of the SEIR-1 "
            "Cross-Cloud IAM Gates 1-7 lab."
        )
    )

    parser.add_argument(
        "--project-id",
        help=(
            "GCP project. If omitted, the active "
            "gcloud project is used."
        )
    )

    parser.add_argument(
        "--vm-name",
        default="seir-crosscloud-01"
    )

    parser.add_argument(
        "--zone",
        default="us-central1-a"
    )

    parser.add_argument(
        "--resource-group",
        default="SEIR-ARC-RG"
    )

    parser.add_argument(
        "--arc-name",
        default=None
    )

    parser.add_argument(
        "--entra-device-name",
        default=None
    )

    parser.add_argument(
        "--user-upn",
        required=True
    )

    parser.add_argument(
        "--group-name",
        default="SEIR_ARC_Users"
    )

    parser.add_argument(
        "--firewall-rule",
        default="seir-allow-rdp"
    )

    parser.add_argument(
        "--rdp-tag",
        default="seir-rdp"
    )

    parser.add_argument(
        "--rdp-timeout",
        type=int,
        default=5
    )

    parser.add_argument(
        "--report",
        default="final_all_gates_report.json"
    )

    return parser.parse_args()


# =====================================================================
# PRE-FLIGHT
# =====================================================================

def preflight(args):

    banner("PRE-FLIGHT - STUDENT DESKTOP")

    # ---------------------------------------------------------------
    # CLI presence
    # ---------------------------------------------------------------

    gcloud_path = shutil.which("gcloud")
    az_path = shutil.which("az")

    if gcloud_path:
        passed(
            "PRE",
            "gcloud CLI installed",
            gcloud_path
        )
    else:
        failed(
            "PRE",
            "gcloud CLI installed",
            "gcloud not found in PATH."
        )

    if az_path:
        passed(
            "PRE",
            "Azure CLI installed",
            az_path
        )
    else:
        failed(
            "PRE",
            "Azure CLI installed",
            "az not found in PATH."
        )

    if not gcloud_path or not az_path:
        return None, None

    # ---------------------------------------------------------------
    # GCP authentication
    # ---------------------------------------------------------------

    try:

        accounts = run_json([
            "gcloud",
            "auth",
            "list",
            "--filter=status:ACTIVE",
            "--format=json"
        ])

        if accounts:

            account = accounts[0].get(
                "account",
                "Unknown"
            )

            passed(
                "PRE",
                "GCP authentication",
                account
            )

        else:

            failed(
                "PRE",
                "GCP authentication",
                "No active gcloud account."
            )

    except CommandFailure as exc:

        error(
            "PRE",
            "GCP authentication",
            str(exc)
        )

    # ---------------------------------------------------------------
    # GCP project
    # ---------------------------------------------------------------

    project_id = args.project_id

    try:

        active_project = run_command([
            "gcloud",
            "config",
            "get-value",
            "project"
        ])

        if active_project and active_project != "(unset)":

            passed(
                "PRE",
                "GCP project selected",
                active_project
            )

            if project_id:

                if project_id == active_project:

                    passed(
                        "PRE",
                        "Expected GCP project matches",
                        project_id
                    )

                else:

                    failed(
                        "PRE",
                        "Expected GCP project matches",
                        (
                            f"Expected={project_id} "
                            f"Active={active_project}"
                        )
                    )

            else:
                project_id = active_project

        else:

            failed(
                "PRE",
                "GCP project selected",
                "No active project."
            )

    except CommandFailure as exc:

        error(
            "PRE",
            "GCP project selected",
            str(exc)
        )

    # ---------------------------------------------------------------
    # Azure authentication
    # ---------------------------------------------------------------

    tenant_id = None

    try:

        account = run_json([
            "az",
            "account",
            "show",
            "--output",
            "json"
        ])

        tenant_id = account.get("tenantId")

        passed(
            "PRE",
            "Azure CLI authenticated",
            account.get("user", {}).get(
                "name",
                "Authenticated"
            )
        )

        passed(
            "PRE",
            "Azure subscription selected",
            (
                f"{account.get('name')} "
                f"({account.get('id')})"
            )
        )

        passed(
            "PRE",
            "Azure tenant detected",
            tenant_id
        )

    except CommandFailure as exc:

        failed(
            "PRE",
            "Azure CLI authenticated",
            f"{exc} -- run: az login"
        )

    # ---------------------------------------------------------------
    # connectedmachine extension
    # ---------------------------------------------------------------

    try:

        extension = run_json([
            "az",
            "extension",
            "show",
            "--name",
            "connectedmachine",
            "--output",
            "json"
        ])

        passed(
            "PRE",
            "Azure connectedmachine CLI extension",
            extension.get("version", "installed")
        )

    except CommandFailure:

        failed(
            "PRE",
            "Azure connectedmachine CLI extension",
            (
                "Install with: "
                "az extension add --name connectedmachine"
            )
        )

    return project_id, tenant_id


# =====================================================================
# FIREWALL HELPER
# =====================================================================

def rule_allows_tcp_port(rule, port):

    for allowed in rule.get("allowed", []):

        protocol = allowed.get(
            "IPProtocol",
            ""
        ).lower()

        if protocol != "tcp":
            continue

        ports = allowed.get(
            "ports",
            []
        )

        # TCP allowed without a port list means all TCP ports.
        if not ports:
            return True

        for value in ports:

            if "-" in value:

                try:

                    start, end = value.split(
                        "-",
                        1
                    )

                    if int(start) <= port <= int(end):
                        return True

                except ValueError:
                    pass

            else:

                try:

                    if int(value) == port:
                        return True

                except ValueError:
                    pass

    return False


# =====================================================================
# GATE 1
# =====================================================================

def gate1(args, project_id):

    banner("GATE 1 - GCP WINDOWS SERVER")

    if not project_id:

        failed(
            "GATE 1",
            "GCP project available"
        )

        return None, None

    # ---------------------------------------------------------------
    # VM
    # ---------------------------------------------------------------

    try:

        instance = run_json([
            "gcloud",
            "compute",
            "instances",
            "describe",
            args.vm_name,
            "--zone",
            args.zone,
            "--project",
            project_id,
            "--format=json"
        ])

        passed(
            "GATE 1",
            "GCP VM exists",
            args.vm_name
        )

    except CommandFailure as exc:

        failed(
            "GATE 1",
            "GCP VM exists",
            str(exc)
        )

        return None, None

    # ---------------------------------------------------------------
    # RUNNING
    # ---------------------------------------------------------------

    status = instance.get("status")

    if status == "RUNNING":

        passed(
            "GATE 1",
            "GCP VM status",
            "RUNNING"
        )

    else:

        failed(
            "GATE 1",
            "GCP VM status",
            str(status)
        )

    # ---------------------------------------------------------------
    # External IP
    # ---------------------------------------------------------------

    external_ip = None

    try:

        external_ip = (
            instance["networkInterfaces"][0]
            ["accessConfigs"][0]
            ["natIP"]
        )

    except (
        KeyError,
        IndexError,
        TypeError
    ):
        pass

    if external_ip:

        passed(
            "GATE 1",
            "GCP external IP",
            external_ip
        )

    else:

        failed(
            "GATE 1",
            "GCP external IP",
            "No external NAT address found."
        )

    # ---------------------------------------------------------------
    # RDP tag
    # ---------------------------------------------------------------

    tags = (
        instance.get(
            "tags",
            {}
        ).get(
            "items",
            []
        )
    )

    if args.rdp_tag in tags:

        passed(
            "GATE 1",
            "RDP network tag",
            args.rdp_tag
        )

    else:

        failed(
            "GATE 1",
            "RDP network tag",
            f"Missing: {args.rdp_tag}"
        )

    # ---------------------------------------------------------------
    # Windows Server 2025
    # ---------------------------------------------------------------

    try:

        boot_disks = [
            disk
            for disk in instance.get(
                "disks",
                []
            )
            if disk.get("boot")
        ]

        if not boot_disks:
            raise CommandFailure(
                "No boot disk found."
            )

        disk_name = path_name(
            boot_disks[0].get("source")
        )

        disk = run_json([
            "gcloud",
            "compute",
            "disks",
            "describe",
            disk_name,
            "--zone",
            args.zone,
            "--project",
            project_id,
            "--format=json"
        ])

        licenses = " ".join(
            disk.get(
                "licenses",
                []
            )
        ).lower()

        source_image = (
            disk.get(
                "sourceImage",
                ""
            )
            or ""
        ).lower()

        if (
            "windows-server-2025"
            in licenses
            or "windows-2025"
            in source_image
        ):

            passed(
                "GATE 1",
                "Windows Server 2025 detected"
            )

        else:

            failed(
                "GATE 1",
                "Windows Server 2025 detected",
                (
                    f"Image={source_image or 'unknown'} "
                    f"Licenses={licenses or 'unknown'}"
                )
            )

        if "core" in source_image:

            failed(
                "GATE 1",
                "Desktop Experience image",
                "Server Core appears to be installed."
            )

        elif source_image:

            passed(
                "GATE 1",
                "Desktop Experience image",
                path_name(source_image)
            )

        else:

            manual(
                "GATE 1",
                "Desktop Experience image",
                (
                    "Confirm Windows Server 2025 "
                    "Desktop Experience locally."
                )
            )

    except CommandFailure as exc:

        error(
            "GATE 1",
            "Windows image verification",
            str(exc)
        )

    # ---------------------------------------------------------------
    # Firewall
    # ---------------------------------------------------------------

    try:

        firewall = run_json([
            "gcloud",
            "compute",
            "firewall-rules",
            "describe",
            args.firewall_rule,
            "--project",
            project_id,
            "--format=json"
        ])

        passed(
            "GATE 1",
            "RDP firewall rule exists",
            args.firewall_rule
        )

        if rule_allows_tcp_port(
            firewall,
            3389
        ):

            passed(
                "GATE 1",
                "Firewall permits TCP/3389"
            )

        else:

            failed(
                "GATE 1",
                "Firewall permits TCP/3389"
            )

        source_ranges = firewall.get(
            "sourceRanges",
            []
        )

        if "0.0.0.0/0" in source_ranges:

            failed(
                "GATE 1",
                "RDP is not open to the Internet",
                "0.0.0.0/0 detected."
            )

        else:

            passed(
                "GATE 1",
                "RDP is not open to the Internet",
                ", ".join(source_ranges)
            )

        target_tags = firewall.get(
            "targetTags",
            []
        )

        if args.rdp_tag in target_tags:

            passed(
                "GATE 1",
                "Firewall targets RDP VM tag",
                args.rdp_tag
            )

        else:

            failed(
                "GATE 1",
                "Firewall targets RDP VM tag",
                str(target_tags)
            )

    except CommandFailure as exc:

        failed(
            "GATE 1",
            "RDP firewall rule exists",
            str(exc)
        )

    # ---------------------------------------------------------------
    # This is important at the FINAL state.
    #
    # Network must still work even though IAM authorization is gone.
    # ---------------------------------------------------------------

    if external_ip:

        try:

            connection = socket.create_connection(
                (
                    external_ip,
                    3389
                ),
                timeout=args.rdp_timeout
            )

            connection.close()

            passed(
                "GATE 1",
                "TCP/3389 reachable from this desktop",
                (
                    f"{external_ip}:3389 -- "
                    "network path is healthy"
                )
            )

        except OSError as exc:

            failed(
                "GATE 1",
                "TCP/3389 reachable from this desktop",
                str(exc)
            )

    return instance, external_ip


# =====================================================================
# GATE 2
# =====================================================================

def gate2(args, tenant_id):

    banner("GATE 2 - AZURE ARC BRIDGE")

    # ---------------------------------------------------------------
    # Resource Providers
    # ---------------------------------------------------------------

    providers = [
        "Microsoft.HybridCompute",
        "Microsoft.GuestConfiguration",
        "Microsoft.HybridConnectivity"
    ]

    for provider in providers:

        try:

            state = run_command([
                "az",
                "provider",
                "show",
                "--namespace",
                provider,
                "--query",
                "registrationState",
                "--output",
                "tsv"
            ])

            if state == "Registered":

                passed(
                    "GATE 2",
                    f"{provider}",
                    "Registered"
                )

            else:

                failed(
                    "GATE 2",
                    f"{provider}",
                    state
                )

        except CommandFailure as exc:

            error(
                "GATE 2",
                provider,
                str(exc)
            )

    # ---------------------------------------------------------------
    # Arc Resource
    # ---------------------------------------------------------------

    try:

        arc = run_json([
            "az",
            "connectedmachine",
            "show",
            "--name",
            args.arc_name,
            "--resource-group",
            args.resource_group,
            "--output",
            "json"
        ])

        passed(
            "GATE 2",
            "Azure Arc resource exists",
            args.arc_name
        )

    except CommandFailure as exc:

        failed(
            "GATE 2",
            "Azure Arc resource exists",
            str(exc)
        )

        return None

    # ---------------------------------------------------------------
    # Connected
    # ---------------------------------------------------------------

    status = arc.get("status")

    if (
        status
        and status.lower() == "connected"
    ):

        passed(
            "GATE 2",
            "Azure Arc status",
            "Connected"
        )

    else:

        failed(
            "GATE 2",
            "Azure Arc status",
            str(status)
        )

    # ---------------------------------------------------------------
    # Managed Identity
    # ---------------------------------------------------------------

    identity = arc.get(
        "identity",
        {}
    ) or {}

    identity_type = (
        identity.get(
            "type",
            ""
        )
    )

    if (
        identity_type
        and "systemassigned"
        in identity_type.lower()
    ):

        passed(
            "GATE 2",
            "System-assigned managed identity",
            identity_type
        )

    else:

        failed(
            "GATE 2",
            "System-assigned managed identity",
            str(identity_type)
        )

    principal_id = identity.get(
        "principalId"
    )

    if principal_id:

        passed(
            "GATE 2",
            "Machine principal ID",
            principal_id
        )

    else:

        failed(
            "GATE 2",
            "Machine principal ID"
        )

    # ---------------------------------------------------------------
    # Tenant
    # ---------------------------------------------------------------

    arc_tenant = identity.get(
        "tenantId"
    )

    if (
        tenant_id
        and arc_tenant
        and tenant_id == arc_tenant
    ):

        passed(
            "GATE 2",
            "Arc tenant matches CLI tenant",
            tenant_id
        )

    else:

        failed(
            "GATE 2",
            "Arc tenant matches CLI tenant",
            (
                f"CLI={tenant_id} "
                f"Arc={arc_tenant}"
            )
        )

    return arc


# =====================================================================
# GATE 3
# =====================================================================

def gate3(args):

    banner("GATE 3 - ENTRA DEVICE IDENTITY")

    # ---------------------------------------------------------------
    # AADLoginForWindows
    # ---------------------------------------------------------------

    try:

        extension = run_json([
            "az",
            "connectedmachine",
            "extension",
            "show",
            "--resource-group",
            args.resource_group,
            "--machine-name",
            args.arc_name,
            "--name",
            "AADLoginForWindows",
            "--output",
            "json"
        ])

        passed(
            "GATE 3",
            "AADLoginForWindows installed"
        )

        state = (
            extension.get(
                "provisioningState"
            )
            or extension.get(
                "properties",
                {}
            ).get(
                "provisioningState"
            )
        )

        if state == "Succeeded":

            passed(
                "GATE 3",
                "AADLoginForWindows state",
                "Succeeded"
            )

        else:

            failed(
                "GATE 3",
                "AADLoginForWindows state",
                str(state)
            )

    except CommandFailure as exc:

        failed(
            "GATE 3",
            "AADLoginForWindows installed",
            str(exc)
        )

    # ---------------------------------------------------------------
    # Entra device
    # ---------------------------------------------------------------

    try:

        devices = run_json([
            "az",
            "ad",
            "device",
            "list",
            "--filter",
            (
                "displayName eq "
                f"'{args.entra_device_name}'"
            ),
            "--output",
            "json"
        ])

        if devices:

            passed(
                "GATE 3",
                "Entra device exists",
                args.entra_device_name
            )

            device = devices[0]

            passed(
                "GATE 3",
                "Entra Device ID",
                (
                    device.get("deviceId")
                    or device.get("id")
                    or "present"
                )
            )

        else:

            failed(
                "GATE 3",
                "Entra device exists",
                (
                    f"No device named "
                    f"{args.entra_device_name}"
                )
            )

    except CommandFailure as exc:

        error(
            "GATE 3",
            "Entra device lookup",
            str(exc)
        )

    # ---------------------------------------------------------------
    # Local proof cannot be safely inferred from desktop APIs.
    # ---------------------------------------------------------------

    manual(
        "GATE 3",
        "Local Entra join confirmation",
        (
            "On the VM run: dsregcmd /status "
            "and confirm AzureAdJoined : YES"
        )
    )


# =====================================================================
# GATE 4
# =====================================================================

def gate4(args, arc, tenant_id):

    banner("GATE 4 - ENTRA HUMAN IDENTITY")

    domain = args.user_upn.split(
        "@",
        1
    )[-1]

    # ---------------------------------------------------------------
    # Domain
    # ---------------------------------------------------------------

    try:

        domain_info = run_json([
            "az",
            "rest",
            "--method",
            "GET",
            "--url",
            (
                "https://graph.microsoft.com/"
                f"v1.0/domains/{domain}"
            ),
            "--output",
            "json"
        ])

        if domain_info.get(
            "isVerified"
        ) is True:

            passed(
                "GATE 4",
                "Custom domain verified",
                domain
            )

        else:

            failed(
                "GATE 4",
                "Custom domain verified",
                domain
            )

    except CommandFailure as exc:

        failed(
            "GATE 4",
            "Custom domain verified",
            str(exc)
        )

    # ---------------------------------------------------------------
    # User
    # ---------------------------------------------------------------

    try:

        user = run_json([
            "az",
            "ad",
            "user",
            "show",
            "--id",
            args.user_upn,
            "--output",
            "json"
        ])

        passed(
            "GATE 4",
            "Entra user exists",
            args.user_upn
        )

    except CommandFailure as exc:

        failed(
            "GATE 4",
            "Entra user exists",
            str(exc)
        )

        return None

    # ---------------------------------------------------------------
    # UPN
    # ---------------------------------------------------------------

    upn = user.get(
        "userPrincipalName"
    )

    if (
        upn
        and upn.lower()
        == args.user_upn.lower()
    ):

        passed(
            "GATE 4",
            "User UPN",
            upn
        )

    else:

        failed(
            "GATE 4",
            "User UPN",
            str(upn)
        )

    # ---------------------------------------------------------------
    # Member, not Guest
    # ---------------------------------------------------------------

    user_type = user.get(
        "userType"
    )

    if user_type == "Member":

        passed(
            "GATE 4",
            "User type",
            "Member"
        )

    else:

        failed(
            "GATE 4",
            "User type",
            str(user_type)
        )

    # ---------------------------------------------------------------
    # Enabled
    # ---------------------------------------------------------------

    enabled = user.get(
        "accountEnabled"
    )

    if enabled is True:

        passed(
            "GATE 4",
            "User account enabled"
        )

    elif enabled is False:

        failed(
            "GATE 4",
            "User account enabled",
            "Account is disabled."
        )

    else:

        error(
            "GATE 4",
            "User account enabled",
            "accountEnabled not returned."
        )

    object_id = user.get(
        "id"
    )

    if object_id:

        passed(
            "GATE 4",
            "User Object ID",
            object_id
        )

    else:

        failed(
            "GATE 4",
            "User Object ID"
        )

    # ---------------------------------------------------------------
    # Same tenant
    # ---------------------------------------------------------------

    if arc:

        arc_tenant = (
            arc.get(
                "identity",
                {}
            )
            or {}
        ).get(
            "tenantId"
        )

        if (
            tenant_id
            and arc_tenant == tenant_id
        ):

            passed(
                "GATE 4",
                "User and Arc tenant alignment",
                tenant_id
            )

        else:

            failed(
                "GATE 4",
                "User and Arc tenant alignment",
                (
                    f"CLI={tenant_id} "
                    f"Arc={arc_tenant}"
                )
            )

    manual(
        "GATE 4",
        "User normal Entra authentication",
        (
            "Confirm the temporary password was changed "
            "and the user can sign into Entra normally."
        )
    )

    return user


# =====================================================================
# GATE 5
# =====================================================================

def gate5(args):

    banner("GATE 5 - VM LOGIN ROLE MODEL")

    # ---------------------------------------------------------------
    # The final state cannot prove that Gate 5 historically succeeded.
    # It CAN prove that the required built-in roles exist and that no
    # direct assignment survived Gate 7.
    # ---------------------------------------------------------------

    for role_name in [
        "Virtual Machine User Login",
        "Virtual Machine Administrator Login"
    ]:

        try:

            roles = run_json([
                "az",
                "role",
                "definition",
                "list",
                "--name",
                role_name,
                "--output",
                "json"
            ])

            if roles:

                passed(
                    "GATE 5",
                    f"Built-in role exists: {role_name}"
                )

            else:

                failed(
                    "GATE 5",
                    f"Built-in role exists: {role_name}"
                )

        except CommandFailure as exc:

            error(
                "GATE 5",
                f"Role lookup: {role_name}",
                str(exc)
            )

    manual(
        "GATE 5",
        "Historical authorization test",
        (
            "Confirm that Gate 5 was manually demonstrated: "
            "direct VM User Login assignment caused a "
            "successful fresh Entra RDP session."
        )
    )


# =====================================================================
# GATE 6
# =====================================================================

def gate6(args, user):

    banner("GATE 6 - ENTERPRISE GROUP AUTHORIZATION MODEL")

    if not user:
        failed(
            "GATE 6",
            "User available for membership checks"
        )
        return None

    user_object_id = user.get(
        "id"
    )

    # ---------------------------------------------------------------
    # Group
    # ---------------------------------------------------------------

    try:

        group = run_json([
            "az",
            "ad",
            "group",
            "show",
            "--group",
            args.group_name,
            "--output",
            "json"
        ])

        passed(
            "GATE 6",
            "Security group exists",
            args.group_name
        )

    except CommandFailure as exc:

        failed(
            "GATE 6",
            "Security group exists",
            str(exc)
        )

        return None

    # ---------------------------------------------------------------
    # Security enabled
    # ---------------------------------------------------------------

    if group.get(
        "securityEnabled"
    ) is True:

        passed(
            "GATE 6",
            "Group is security-enabled"
        )

    else:

        failed(
            "GATE 6",
            "Group is security-enabled"
        )

    group_object_id = group.get(
        "id"
    )

    if group_object_id:

        passed(
            "GATE 6",
            "Group Object ID",
            group_object_id
        )

    # ---------------------------------------------------------------
    # Membership
    #
    # Final Gate 7 state intentionally keeps Chewbacca in the group.
    # ---------------------------------------------------------------

    try:

        membership = run_json([
            "az",
            "ad",
            "group",
            "member",
            "check",
            "--group",
            group_object_id,
            "--member-id",
            user_object_id,
            "--output",
            "json"
        ])

        if membership.get(
            "value"
        ) is True:

            passed(
                "GATE 6",
                "User remains a group member",
                args.group_name
            )

        else:

            failed(
                "GATE 6",
                "User remains a group member",
                (
                    "Gate 7 final state expects the user "
                    "to remain in the group."
                )
            )

    except CommandFailure as exc:

        error(
            "GATE 6",
            "Group membership",
            str(exc)
        )

    manual(
        "GATE 6",
        "Historical group authorization test",
        (
            "Confirm Gate 6 was demonstrated manually: "
            "group IN -> allowed, OUT -> denied, "
            "IN -> allowed."
        )
    )

    return group


# =====================================================================
# ROLE HELPERS
# =====================================================================

LOGIN_ROLES = {
    "Virtual Machine User Login",
    "Virtual Machine Administrator Login"
}


def find_login_roles(assignments):

    found = []

    for assignment in assignments or []:

        role_name = assignment.get(
            "roleDefinitionName"
        )

        if role_name in LOGIN_ROLES:

            found.append({
                "role": role_name,
                "scope": assignment.get(
                    "scope"
                ),
                "principal": (
                    assignment.get(
                        "principalName"
                    )
                    or assignment.get(
                        "principalId"
                    )
                )
            })

    return found


# =====================================================================
# GATE 7
# =====================================================================

def gate7(args, arc, user, group, external_ip):

    banner("GATE 7 - FINAL REVOCATION STATE")

    if not arc or not user or not group:

        failed(
            "GATE 7",
            "Required objects available",
            "Arc, User, or Group object missing."
        )

        return

    arc_resource_id = arc.get(
        "id"
    )

    user_object_id = user.get(
        "id"
    )

    group_object_id = group.get(
        "id"
    )

    # ---------------------------------------------------------------
    # Verify user has NO direct/inherited login role.
    # ---------------------------------------------------------------

    try:

        direct_assignments = run_json([
            "az",
            "role",
            "assignment",
            "list",
            "--all",
            "--assignee-object-id",
            user_object_id,
            "--scope",
            arc_resource_id,
            "--include-inherited",
            "--output",
            "json"
        ])

        direct_login_roles = find_login_roles(
            direct_assignments
        )

        if not direct_login_roles:

            passed(
                "GATE 7",
                "No direct/inherited user VM login role"
            )

        else:

            failed(
                "GATE 7",
                "No direct/inherited user VM login role",
                json.dumps(
                    direct_login_roles
                )
            )

    except CommandFailure as exc:

        error(
            "GATE 7",
            "Direct user role verification",
            str(exc)
        )

    # ---------------------------------------------------------------
    # Verify group has NO login assignment.
    # ---------------------------------------------------------------

    try:

        group_assignments = run_json([
            "az",
            "role",
            "assignment",
            "list",
            "--all",
            "--assignee-object-id",
            group_object_id,
            "--scope",
            arc_resource_id,
            "--include-inherited",
            "--output",
            "json"
        ])

        group_login_roles = find_login_roles(
            group_assignments
        )

        if not group_login_roles:

            passed(
                "GATE 7",
                "Group has no VM login role"
            )

        else:

            failed(
                "GATE 7",
                "Group has no VM login role",
                json.dumps(
                    group_login_roles
                )
            )

    except CommandFailure as exc:

        error(
            "GATE 7",
            "Group role verification",
            str(exc)
        )

    # ---------------------------------------------------------------
    # This is the strongest cloud-side check.
    #
    # Include:
    #   direct roles
    #   inherited roles
    #   group-derived roles
    #
    # If ANY VM login role remains, final revocation is incomplete.
    # ---------------------------------------------------------------

    try:

        effective_assignments = run_json([
            "az",
            "role",
            "assignment",
            "list",
            "--all",
            "--assignee-object-id",
            user_object_id,
            "--scope",
            arc_resource_id,
            "--include-inherited",
            "--include-groups",
            "--output",
            "json"
        ])

        effective_login_roles = find_login_roles(
            effective_assignments
        )

        if not effective_login_roles:

            passed(
                "GATE 7",
                "NO effective VM login authorization",
                (
                    "Direct + inherited + group-derived "
                    "login roles are absent."
                )
            )

        else:

            failed(
                "GATE 7",
                "NO effective VM login authorization",
                (
                    "Residual authorization found: "
                    + json.dumps(
                        effective_login_roles
                    )
                )
            )

    except CommandFailure as exc:

        error(
            "GATE 7",
            "Effective authorization verification",
            str(exc)
        )

    # ---------------------------------------------------------------
    # Infrastructure must remain healthy.
    # ---------------------------------------------------------------

    if (
        arc.get(
            "status",
            ""
        ).lower()
        == "connected"
    ):

        passed(
            "GATE 7",
            "Arc remains healthy after revocation",
            "Connected"
        )

    else:

        failed(
            "GATE 7",
            "Arc remains healthy after revocation",
            str(
                arc.get("status")
            )
        )

    # ---------------------------------------------------------------
    # Network should STILL be reachable.
    #
    # This is pedagogically important:
    #
    # Network = PASS
    # IAM     = DENIED
    # ---------------------------------------------------------------

    if external_ip:

        try:

            connection = socket.create_connection(
                (
                    external_ip,
                    3389
                ),
                timeout=args.rdp_timeout
            )

            connection.close()

            passed(
                "GATE 7",
                "RDP network path still works",
                (
                    f"{external_ip}:3389 reachable. "
                    "Any new login denial should be IAM, "
                    "not network failure."
                )
            )

        except OSError as exc:

            failed(
                "GATE 7",
                "RDP network path still works",
                str(exc)
            )

    manual(
        "GATE 7",
        "Fresh RDP attempt is denied",
        (
            "Start a NEW Entra-authenticated RDP attempt. "
            "Expected result: authorization denied."
        )
    )


# =====================================================================
# FINAL SECURITY INVARIANTS
# =====================================================================

def final_invariants():

    banner("FINAL SECURITY INVARIANTS")

    expected = [
        (
            "GCP compute remains operational",
            "The VM should not have been damaged by IAM revocation."
        ),
        (
            "Azure Arc remains connected",
            "The cross-cloud management bridge remains healthy."
        ),
        (
            "Entra device remains present",
            "The server identity remains intact."
        ),
        (
            "Entra user remains enabled",
            "Identity was not destroyed to remove access."
        ),
        (
            "Security group remains present",
            "The group itself was not deleted."
        ),
        (
            "User remains a group member",
            "Gate 7 removed GROUP PERMISSION, not membership."
        ),
        (
            "No VM login role remains",
            "Authorization was removed cleanly."
        ),
        (
            "RDP TCP path remains reachable",
            "Denial should come from IAM, not networking."
        )
    ]

    for name, detail in expected:
        print(f"  - {name}")
        print(f"      {detail}")


# =====================================================================
# SUMMARY
# =====================================================================

def summary():

    banner("FINAL ALL-GATES SCOREBOARD")

    gates = [
        "PRE",
        "GATE 1",
        "GATE 2",
        "GATE 3",
        "GATE 4",
        "GATE 5",
        "GATE 6",
        "GATE 7"
    ]

    for gate in gates:

        results = [
            result
            for result in RESULTS
            if result.gate == gate
        ]

        if not results:
            continue

        failures = [
            result
            for result in results
            if result.status
            in (
                "FAIL",
                "ERROR"
            )
        ]

        passes = [
            result
            for result in results
            if result.status == "PASS"
        ]

        manuals = [
            result
            for result in results
            if result.status == "MANUAL"
        ]

        if failures:
            state = f"{RED}FAIL{RESET}"
        else:
            state = f"{GREEN}PASS{RESET}"

        print(
            f"{gate:<10}"
            f"{state:<15}"
            f"AUTO PASS={len(passes):<3}"
            f"MANUAL={len(manuals):<3}"
            f"FAIL/ERROR={len(failures)}"
        )

    total_pass = sum(
        result.status == "PASS"
        for result in RESULTS
    )

    total_fail = sum(
        result.status == "FAIL"
        for result in RESULTS
    )

    total_error = sum(
        result.status == "ERROR"
        for result in RESULTS
    )

    total_manual = sum(
        result.status == "MANUAL"
        for result in RESULTS
    )

    print()
    print(f"PASS:    {total_pass}")
    print(f"FAIL:    {total_fail}")
    print(f"ERROR:   {total_error}")
    print(f"MANUAL:  {total_manual}")
    print()

    if (
        total_fail == 0
        and total_error == 0
    ):

        print(
            f"{GREEN}{BOLD}"
            "AUTOMATED FINAL-STATE VERIFICATION PASSED"
            f"{RESET}"
        )

        print()

        print(
            "The environment is consistent with the "
            "expected post-Gate-7 state."
        )

        print()

        print(
            f"{GREEN}"
            "COMPUTE        PASS"
            f"{RESET}"
        )

        print(
            f"{GREEN}"
            "NETWORK        PASS"
            f"{RESET}"
        )

        print(
            f"{GREEN}"
            "AZURE ARC      PASS"
            f"{RESET}"
        )

        print(
            f"{GREEN}"
            "DEVICE ID      PASS"
            f"{RESET}"
        )

        print(
            f"{GREEN}"
            "USER ID        PASS"
            f"{RESET}"
        )

        print(
            f"{GREEN}"
            "GROUP          PASS"
            f"{RESET}"
        )

        print(
            f"{GREEN}"
            "REVOCATION     PASS"
            f"{RESET}"
        )

        print()

        print(
            f"{CYAN}{BOLD}"
            "FINAL EXPECTED RESULT:"
            f"{RESET}"
        )

        print(
            "Infrastructure is healthy."
        )

        print(
            "Identity is healthy."
        )

        print(
            "Network connectivity is healthy."
        )

        print(
            "VM login authorization has been removed."
        )

        if total_manual:

            print()
            print(
                f"{YELLOW}"
                "Complete the MANUAL checks before "
                "declaring the entire lab complete."
                f"{RESET}"
            )

    else:

        print(
            f"{RED}{BOLD}"
            "FINAL VERIFICATION FAILED"
            f"{RESET}"
        )

        print()

        print(
            "Do not tear down the lab yet."
        )

        print(
            "Use the first failing gate to determine "
            "where troubleshooting should begin."
        )


# =====================================================================
# REPORT
# =====================================================================

def save_report(filename):

    report = {
        "generated_utc": datetime.now(
            timezone.utc
        ).isoformat(),

        "expected_final_state": {
            "compute": "healthy",
            "network": "healthy",
            "azure_arc": "connected",
            "entra_device": "present",
            "entra_user": "enabled",
            "security_group": "present",
            "group_membership": "present",
            "vm_login_authorization": "absent"
        },

        "checks": [
            asdict(result)
            for result in RESULTS
        ]
    }

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=2
        )

    print()
    print(
        f"Verification report: {filename}"
    )


# =====================================================================
# MAIN
# =====================================================================

def main():

    args = parse_args()

    if args.arc_name is None:
        args.arc_name = args.vm_name

    if args.entra_device_name is None:
        args.entra_device_name = args.arc_name

    banner(
        "SEIR-1 CROSS-CLOUD IAM "
        "- FINAL ALL-GATES VERIFICATION"
    )

    print(
        f"GCP VM:              {args.vm_name}"
    )

    print(
        f"GCP Zone:            {args.zone}"
    )

    print(
        f"Azure Arc Resource:  {args.arc_name}"
    )

    print(
        f"Azure Resource Group:{args.resource_group}"
    )

    print(
        f"Entra Device:        {args.entra_device_name}"
    )

    print(
        f"Entra User:          {args.user_upn}"
    )

    print(
        f"Entra Security Group:{args.group_name}"
    )

    project_id, tenant_id = preflight(
        args
    )

    instance, external_ip = gate1(
        args,
        project_id
    )

    arc = gate2(
        args,
        tenant_id
    )

    gate3(
        args
    )

    user = gate4(
        args,
        arc,
        tenant_id
    )

    gate5(
        args
    )

    group = gate6(
        args,
        user
    )

    gate7(
        args,
        arc,
        user,
        group,
        external_ip
    )

    final_invariants()

    summary()

    save_report(
        args.report
    )

    failure_exists = any(
        result.status
        in (
            "FAIL",
            "ERROR"
        )
        for result in RESULTS
    )

    sys.exit(
        1
        if failure_exists
        else 0
    )


if __name__ == "__main__":
    main()
