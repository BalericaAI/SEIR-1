#!/usr/bin/env python3

"""
SEIR-1 Cross-Cloud IAM
All Gates Verification - Gates 1 through 4

PURPOSE
-------
Run this script from the student's DESKTOP after completing Gate 4.

The script is READ-ONLY.

It verifies:

Gate 1
    GCP VM exists
    VM is RUNNING
    Windows Server 2025 is being used
    Desktop Experience image was used, not Server Core
    External IP exists
    RDP network tag exists
    RDP firewall rule exists
    TCP/3389 is not open to 0.0.0.0/0
    RDP is reachable from the current workstation

Gate 2
    Azure Arc resource providers are registered
    Arc machine exists
    Arc machine reports Connected
    System-assigned managed identity exists
    Arc tenant matches current Azure tenant

Gate 3
    AADLoginForWindows extension exists
    Extension provisioning state is Succeeded
    Entra device object exists

Gate 4
    Custom domain is verified
    Entra user exists
    User UPN is correct
    User is a Member
    User account is enabled
    User belongs to the same tenant
    NO Virtual Machine User Login role exists yet
    NO Virtual Machine Administrator Login role exists yet

The script DOES NOT:
    create resources
    modify resources
    request passwords
    print access tokens
    assign RBAC roles

Requirements:
    Python 3.10+
    gcloud CLI
    Azure CLI
    Azure CLI connectedmachine extension

Example:

python verify_all_gates.py \
    --user-upn chewbacca@balerica-ai.org

Optional:

python verify_all_gates.py \
    --project-id YOUR_GCP_PROJECT \
    --vm-name seir-crosscloud-01 \
    --zone us-central1-a \
    --resource-group SEIR-ARC-RG \
    --arc-name seir-crosscloud-01 \
    --user-upn chewbacca@balerica-ai.org \
    --firewall-rule seir-allow-rdp \
    --rdp-tag seir-rdp
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
from typing import Optional


# ---------------------------------------------------------------------
# RESULT MODEL
# ---------------------------------------------------------------------

@dataclass
class CheckResult:
    gate: str
    check: str
    status: str
    detail: str


RESULTS: list[CheckResult] = []


# ---------------------------------------------------------------------
# COLORS
# ---------------------------------------------------------------------

USE_COLOR = sys.stdout.isatty() and not os.getenv("NO_COLOR")

if USE_COLOR:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
else:
    GREEN = RED = YELLOW = CYAN = BOLD = RESET = ""


# ---------------------------------------------------------------------
# OUTPUT HELPERS
# ---------------------------------------------------------------------

def banner(text: str) -> None:
    print()
    print("=" * 78)
    print(f"{BOLD}{text}{RESET}")
    print("=" * 78)


def add_result(
    gate: str,
    check: str,
    status: str,
    detail: str = ""
) -> None:

    result = CheckResult(
        gate=gate,
        check=check,
        status=status,
        detail=detail
    )

    RESULTS.append(result)

    if status == "PASS":
        symbol = f"{GREEN}[PASS]{RESET}"
    elif status == "FAIL":
        symbol = f"{RED}[FAIL]{RESET}"
    elif status == "MANUAL":
        symbol = f"{YELLOW}[MANUAL]{RESET}"
    else:
        symbol = f"{YELLOW}[ERROR]{RESET}"

    print(f"{symbol:<15} {check}")

    if detail:
        print(f"                {detail}")


def passed(gate: str, check: str, detail: str = "") -> None:
    add_result(gate, check, "PASS", detail)


def failed(gate: str, check: str, detail: str = "") -> None:
    add_result(gate, check, "FAIL", detail)


def manual(gate: str, check: str, detail: str = "") -> None:
    add_result(gate, check, "MANUAL", detail)


def error(gate: str, check: str, detail: str = "") -> None:
    add_result(gate, check, "ERROR", detail)


# ---------------------------------------------------------------------
# COMMAND HELPERS
# ---------------------------------------------------------------------

class CommandFailure(Exception):
    pass


def run_command(
    command: list[str],
    timeout: int = 60
) -> str:

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


def run_json(
    command: list[str],
    timeout: int = 60
):
    output = run_command(command, timeout)

    if not output:
        return None

    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise CommandFailure(
            f"Expected JSON but received:\n{output}"
        ) from exc


def last_path_part(value: str) -> str:
    return value.rstrip("/").split("/")[-1]


# ---------------------------------------------------------------------
# PORT HELPER
# ---------------------------------------------------------------------

def rule_contains_port(rule: dict, port: int) -> bool:

    for allowed in rule.get("allowed", []):

        if allowed.get("IPProtocol", "").lower() != "tcp":
            continue

        ports = allowed.get("ports", [])

        # No ports specified means all TCP ports.
        if not ports:
            return True

        for item in ports:

            if "-" in item:
                start, end = item.split("-", 1)

                try:
                    if int(start) <= port <= int(end):
                        return True
                except ValueError:
                    continue

            else:
                try:
                    if int(item) == port:
                        return True
                except ValueError:
                    continue

    return False


# ---------------------------------------------------------------------
# ARGUMENTS
# ---------------------------------------------------------------------

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Verify SEIR-1 Cross-Cloud IAM Gates 1 through 4."
        )
    )

    parser.add_argument(
        "--project-id",
        help="Expected GCP project ID. If omitted, active gcloud project is used."
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
        default=None,
        help="Azure Arc machine name. Defaults to --vm-name."
    )

    parser.add_argument(
        "--user-upn",
        required=True,
        help="Entra user UPN, e.g. chewbacca@balerica-ai.org"
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
        default="all_gates_verification.json"
    )

    return parser.parse_args()


# ---------------------------------------------------------------------
# PRE-FLIGHT
# ---------------------------------------------------------------------

def preflight(args):

    banner("PRE-FLIGHT - DESKTOP CLI ENVIRONMENT")

    gcloud = shutil.which("gcloud")
    az = shutil.which("az")

    if gcloud:
        passed("PRE", "gcloud CLI installed", gcloud)
    else:
        failed("PRE", "gcloud CLI installed", "gcloud was not found.")

    if az:
        passed("PRE", "Azure CLI installed", az)
    else:
        failed("PRE", "Azure CLI installed", "az was not found.")

    if not gcloud or not az:
        return None, None

    # GCP authentication
    try:
        accounts = run_json([
            "gcloud",
            "auth",
            "list",
            "--filter=status:ACTIVE",
            "--format=json"
        ])

        if accounts:
            account = accounts[0].get("account", "Unknown")
            passed(
                "PRE",
                "GCP CLI authentication",
                f"Active account: {account}"
            )
        else:
            failed(
                "PRE",
                "GCP CLI authentication",
                "No active gcloud account."
            )

    except CommandFailure as exc:
        error("PRE", "GCP CLI authentication", str(exc))

    # GCP project
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

            if args.project_id:

                if active_project == args.project_id:
                    passed(
                        "PRE",
                        "Expected GCP project",
                        active_project
                    )
                else:
                    failed(
                        "PRE",
                        "Expected GCP project",
                        (
                            f"Expected {args.project_id}, "
                            f"active project is {active_project}"
                        )
                    )

            project_id = args.project_id or active_project

        else:
            failed(
                "PRE",
                "GCP project selected",
                "No active GCP project."
            )

            project_id = args.project_id

    except CommandFailure as exc:
        error("PRE", "GCP project selected", str(exc))
        project_id = args.project_id

    # Azure authentication
    try:
        account = run_json([
            "az",
            "account",
            "show",
            "--output",
            "json"
        ])

        subscription_id = account.get("id")
        tenant_id = account.get("tenantId")
        subscription_name = account.get("name")

        passed(
            "PRE",
            "Azure CLI authentication",
            f"Subscription: {subscription_name}"
        )

        passed(
            "PRE",
            "Azure tenant detected",
            tenant_id
        )

    except CommandFailure as exc:

        error(
            "PRE",
            "Azure CLI authentication",
            (
                f"{exc}\n"
                "Run: az login"
            )
        )

        tenant_id = None

    return project_id, tenant_id


# ---------------------------------------------------------------------
# GATE 1
# ---------------------------------------------------------------------

def gate1(args, project_id):

    banner("GATE 1 - GCP WINDOWS VM")

    if not project_id:
        failed(
            "GATE 1",
            "GCP project available",
            "Cannot run Gate 1 checks without a project."
        )
        return None

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
        return None

    # Status
    status = instance.get("status")

    if status == "RUNNING":
        passed(
            "GATE 1",
            "VM status",
            "RUNNING"
        )
    else:
        failed(
            "GATE 1",
            "VM status",
            str(status)
        )

    # External IP
    external_ip = None

    try:
        interfaces = instance.get("networkInterfaces", [])
        configs = interfaces[0].get("accessConfigs", [])
        external_ip = configs[0].get("natIP")
    except (IndexError, AttributeError):
        pass

    if external_ip:
        passed(
            "GATE 1",
            "External IP exists",
            external_ip
        )
    else:
        failed(
            "GATE 1",
            "External IP exists",
            "No public NAT IP found."
        )

    # Network tag
    tags = instance.get("tags", {}).get("items", [])

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
            f"Expected tag: {args.rdp_tag}"
        )

    # Windows version based on boot disk metadata.
    try:
        boot_disks = [
            disk
            for disk in instance.get("disks", [])
            if disk.get("boot")
        ]

        if not boot_disks:
            raise CommandFailure("No boot disk found.")

        disk_name = last_path_part(
            boot_disks[0]["source"]
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
            disk.get("licenses", [])
        ).lower()

        source_image = (
            disk.get("sourceImage", "")
            or ""
        ).lower()

        if "windows-server-2025" in licenses:
            passed(
                "GATE 1",
                "Windows Server 2025 license",
                "Windows Server 2025 detected."
            )
        else:
            failed(
                "GATE 1",
                "Windows Server 2025 license",
                f"Licenses: {licenses or 'Unknown'}"
            )

        if source_image:

            if "core" in source_image:
                failed(
                    "GATE 1",
                    "Windows Desktop Experience image",
                    (
                        "Source image appears to be "
                        "Windows Server Core."
                    )
                )

            elif (
                "windows-2025" in source_image
                or "windows-server-2025" in source_image
            ):
                passed(
                    "GATE 1",
                    "Windows Desktop Experience image",
                    last_path_part(source_image)
                )

            else:
                error(
                    "GATE 1",
                    "Windows Desktop Experience image",
                    f"Unable to identify image: {source_image}"
                )

        else:
            manual(
                "GATE 1",
                "Windows Desktop Experience image",
                (
                    "sourceImage metadata unavailable. "
                    "Confirm using Get-ComputerInfo inside Windows."
                )
            )

    except CommandFailure as exc:
        error(
            "GATE 1",
            "Windows boot disk verification",
            str(exc)
        )

    # Firewall
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

        if rule_contains_port(firewall, 3389):
            passed(
                "GATE 1",
                "Firewall permits TCP/3389"
            )
        else:
            failed(
                "GATE 1",
                "Firewall permits TCP/3389"
            )

        ranges = firewall.get("sourceRanges", [])

        if "0.0.0.0/0" in ranges:
            failed(
                "GATE 1",
                "RDP is not world-open",
                "0.0.0.0/0 is configured."
            )
        elif ranges:
            passed(
                "GATE 1",
                "RDP is not world-open",
                ", ".join(ranges)
            )
        else:
            failed(
                "GATE 1",
                "RDP source range",
                "No source ranges found."
            )

        target_tags = firewall.get("targetTags", [])

        if args.rdp_tag in target_tags:
            passed(
                "GATE 1",
                "Firewall targets VM tag",
                args.rdp_tag
            )
        else:
            failed(
                "GATE 1",
                "Firewall targets VM tag",
                f"Expected: {args.rdp_tag}"
            )

    except CommandFailure as exc:
        failed(
            "GATE 1",
            "RDP firewall rule exists",
            str(exc)
        )

    # Actual TCP test from workstation.
    if external_ip:

        try:
            with socket.create_connection(
                (external_ip, 3389),
                timeout=args.rdp_timeout
            ):
                passed(
                    "GATE 1",
                    "RDP reachable from this workstation",
                    f"{external_ip}:3389"
                )

        except OSError as exc:
            failed(
                "GATE 1",
                "RDP reachable from this workstation",
                f"{external_ip}:3389 - {exc}"
            )

    manual(
        "GATE 1",
        "Local bootstrap login",
        (
            "Confirm you successfully logged in using "
            "seir-local-admin."
        )
    )

    return instance


# ---------------------------------------------------------------------
# GATE 2
# ---------------------------------------------------------------------

def gate2(args, tenant_id):

    banner("GATE 2 - AZURE ARC")

    providers = [
        "Microsoft.HybridCompute",
        "Microsoft.GuestConfiguration",
        "Microsoft.HybridConnectivity",
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
                    f"{provider} registered"
                )
            else:
                failed(
                    "GATE 2",
                    f"{provider} registered",
                    state
                )

        except CommandFailure as exc:
            error(
                "GATE 2",
                f"{provider} registered",
                str(exc)
            )

    try:
        arc = run_json([
            "az",
            "connectedmachine",
            "show",
            "--name",
            args.arc_name,
            "--resource-group",
            args.resource_group,
            "--expand",
            "instanceView",
            "--output",
            "json"
        ])

        passed(
            "GATE 2",
            "Azure Arc machine exists",
            args.arc_name
        )

    except CommandFailure as exc:
        failed(
            "GATE 2",
            "Azure Arc machine exists",
            str(exc)
        )
        return None

    status = (
        arc.get("status")
        or arc.get("instanceView", {}).get("status")
    )

    if str(status).lower() == "connected":
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

    identity = arc.get("identity") or {}

    identity_type = identity.get("type")

    if identity_type and "systemassigned" in identity_type.lower():
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

    principal_id = identity.get("principalId")

    if principal_id:
        passed(
            "GATE 2",
            "Machine principal ID exists",
            principal_id
        )
    else:
        failed(
            "GATE 2",
            "Machine principal ID exists"
        )

    arc_tenant = identity.get("tenantId")

    if tenant_id and arc_tenant == tenant_id:
        passed(
            "GATE 2",
            "Arc tenant matches Azure CLI tenant",
            tenant_id
        )
    elif tenant_id and arc_tenant:
        failed(
            "GATE 2",
            "Arc tenant matches Azure CLI tenant",
            f"Arc={arc_tenant} CLI={tenant_id}"
        )
    else:
        error(
            "GATE 2",
            "Arc tenant matches Azure CLI tenant",
            "Tenant information unavailable."
        )

    return arc


# ---------------------------------------------------------------------
# GATE 3
# ---------------------------------------------------------------------

def gate3(args):

    banner("GATE 3 - MICROSOFT ENTRA DEVICE IDENTITY")

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
            "AADLoginForWindows extension exists"
        )

        state = (
            extension.get("provisioningState")
            or extension.get(
                "properties",
                {}
            ).get("provisioningState")
        )

        if state == "Succeeded":
            passed(
                "GATE 3",
                "AADLoginForWindows provisioning",
                state
            )
        else:
            failed(
                "GATE 3",
                "AADLoginForWindows provisioning",
                str(state)
            )

    except CommandFailure as exc:
        failed(
            "GATE 3",
            "AADLoginForWindows extension exists",
            str(exc)
        )

    # Device object
    try:
        devices = run_json([
            "az",
            "ad",
            "device",
            "list",
            "--filter",
            f"displayName eq '{args.arc_name}'",
            "--output",
            "json"
        ])

        if devices:

            passed(
                "GATE 3",
                "Entra device object exists",
                f"{len(devices)} matching device(s)"
            )

            for device in devices:

                device_id = (
                    device.get("deviceId")
                    or device.get("id")
                )

                if device_id:
                    passed(
                        "GATE 3",
                        "Entra Device ID",
                        device_id
                    )
                    break

        else:
            failed(
                "GATE 3",
                "Entra device object exists",
                (
                    f"No device named "
                    f"{args.arc_name} was found."
                )
            )

    except CommandFailure as exc:
        error(
            "GATE 3",
            "Entra device object exists",
            str(exc)
        )

    manual(
        "GATE 3",
        "Local dsregcmd confirmation",
        (
            "Inside the Windows VM run: dsregcmd /status "
            "and verify AzureAdJoined : YES"
        )
    )


# ---------------------------------------------------------------------
# GATE 4
# ---------------------------------------------------------------------

def gate4(args, arc, tenant_id):

    banner("GATE 4 - MICROSOFT ENTRA USER")

    domain = args.user_upn.split("@", 1)[-1]

    # Domain
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

        if domain_info.get("isVerified") is True:

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

    # User
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
        return

    upn = user.get("userPrincipalName")

    if upn and upn.lower() == args.user_upn.lower():
        passed(
            "GATE 4",
            "User UPN is correct",
            upn
        )
    else:
        failed(
            "GATE 4",
            "User UPN is correct",
            str(upn)
        )

    user_type = user.get("userType")

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
            (
                f"{user_type}. "
                "Arc login requires a same-tenant Member."
            )
        )

    account_enabled = user.get("accountEnabled")

    if account_enabled is True:
        passed(
            "GATE 4",
            "User account enabled"
        )
    elif account_enabled is False:
        failed(
            "GATE 4",
            "User account enabled",
            "Account is disabled."
        )
    else:
        error(
            "GATE 4",
            "User account enabled",
            "accountEnabled was not returned by Azure CLI."
        )

    user_object_id = user.get("id")

    if user_object_id:
        passed(
            "GATE 4",
            "User Object ID exists",
            user_object_id
        )
    else:
        failed(
            "GATE 4",
            "User Object ID exists"
        )
        return

    # Tenant consistency
    if arc:

        arc_identity = arc.get("identity") or {}
        arc_tenant = arc_identity.get("tenantId")

        if tenant_id and arc_tenant == tenant_id:
            passed(
                "GATE 4",
                "User/Arc tenant alignment",
                tenant_id
            )
        else:
            failed(
                "GATE 4",
                "User/Arc tenant alignment",
                (
                    f"CLI tenant={tenant_id}, "
                    f"Arc tenant={arc_tenant}"
                )
            )

        arc_resource_id = arc.get("id")

    else:
        arc_resource_id = None

    # Gate 4 should NOT yet have VM login authorization.
    if arc_resource_id:

        try:
            assignments = run_json([
                "az",
                "role",
                "assignment",
                "list",
                "--all",
                "--assignee-object-id",
                user_object_id,
                "--include-groups",
                "--include-inherited",
                "--scope",
                arc_resource_id,
                "--output",
                "json"
            ])

            login_roles = {
                "Virtual Machine User Login",
                "Virtual Machine Administrator Login"
            }

            found_login_roles = []

            for assignment in assignments or []:

                role_name = assignment.get(
                    "roleDefinitionName"
                )

                if role_name in login_roles:
                    found_login_roles.append(role_name)

            if not found_login_roles:

                passed(
                    "GATE 4",
                    "No VM login role assigned yet",
                    (
                        "Correct Gate 4 state: "
                        "identity exists, authorization does not."
                    )
                )

            else:
                failed(
                    "GATE 4",
                    "No VM login role assigned yet",
                    (
                        "Unexpected role(s): "
                        + ", ".join(found_login_roles)
                    )
                )

        except CommandFailure as exc:
            error(
                "GATE 4",
                "VM login role verification",
                str(exc)
            )

    else:
        error(
            "GATE 4",
            "VM login role verification",
            "Arc resource ID unavailable."
        )

    manual(
        "GATE 4",
        "Temporary password changed",
        (
            "Confirm the user completed first sign-in "
            "and changed the temporary password."
        )
    )

    manual(
        "GATE 4",
        "Normal Entra sign-in works",
        (
            "Confirm the user can authenticate normally "
            "to Microsoft Entra."
        )
    )


# ---------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------

def print_summary():

    banner("ALL GATES VERIFICATION SUMMARY")

    gates = [
        "PRE",
        "GATE 1",
        "GATE 2",
        "GATE 3",
        "GATE 4"
    ]

    for gate in gates:

        gate_results = [
            result
            for result in RESULTS
            if result.gate == gate
        ]

        if not gate_results:
            continue

        failures = [
            result
            for result in gate_results
            if result.status in ("FAIL", "ERROR")
        ]

        manual_items = [
            result
            for result in gate_results
            if result.status == "MANUAL"
        ]

        if failures:
            status = f"{RED}FAIL{RESET}"

        else:
            status = f"{GREEN}PASS{RESET}"

        print(
            f"{gate:<10} {status:<15} "
            f"{len(gate_results) - len(failures) - len(manual_items)} "
            f"automated checks passed"
        )

    print()

    passes = sum(
        1
        for result in RESULTS
        if result.status == "PASS"
    )

    failures = sum(
        1
        for result in RESULTS
        if result.status == "FAIL"
    )

    errors = sum(
        1
        for result in RESULTS
        if result.status == "ERROR"
    )

    manuals = sum(
        1
        for result in RESULTS
        if result.status == "MANUAL"
    )

    print(f"PASS:   {passes}")
    print(f"FAIL:   {failures}")
    print(f"ERROR:  {errors}")
    print(f"MANUAL: {manuals}")

    print()

    if failures == 0 and errors == 0:

        print(
            f"{GREEN}{BOLD}"
            "AUTOMATED GATES 1-4 VERIFICATION PASSED."
            f"{RESET}"
        )

        if manuals:
            print()
            print(
                "Complete the MANUAL confirmations above "
                "before proceeding to Gate 5."
            )

    else:

        print(
            f"{RED}{BOLD}"
            "DO NOT PROCEED TO GATE 5."
            f"{RESET}"
        )

        print()
        print(
            "Fix the failed gate before adding "
            "Virtual Machine User Login."
        )


# ---------------------------------------------------------------------
# JSON REPORT
# ---------------------------------------------------------------------

def save_report(filename: str):

    report = {
        "generated": datetime.now(
            timezone.utc
        ).isoformat(),
        "results": [
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
    print(f"Report written to: {filename}")


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():

    args = parse_args()

    if args.arc_name is None:
        args.arc_name = args.vm_name

    banner(
        "SEIR-1 CROSS-CLOUD IAM - ALL GATES VERIFICATION"
    )

    print(f"GCP VM:              {args.vm_name}")
    print(f"GCP Zone:            {args.zone}")
    print(f"Azure Arc Machine:   {args.arc_name}")
    print(f"Azure Resource Group:{args.resource_group}")
    print(f"Entra User:          {args.user_upn}")

    project_id, tenant_id = preflight(args)

    gate1(
        args,
        project_id
    )

    arc = gate2(
        args,
        tenant_id
    )

    gate3(args)

    gate4(
        args,
        arc,
        tenant_id
    )

    print_summary()

    save_report(args.report)

    failures = any(
        result.status in ("FAIL", "ERROR")
        for result in RESULTS
    )

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
