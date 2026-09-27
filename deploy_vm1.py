#!/usr/bin/env python3

"""
VMware vCenter Windows VM Bulk Deployment
=========================================

Python:
    3.12+

Dependency:
    pyVmomi

Install:
    pip install pyvmomi

Features:
    - Displays configured vCenter servers in a numbered menu
    - User selects vCenter instead of typing the IP every time
    - Connects using SmartConnect
    - SSL certificate verification disabled
    - Discovers datacenters
    - Discovers ESXi hosts
    - Discovers datastores
    - Discovers networks / port groups
    - Discovers Windows VM templates
    - Template selection by numbered menu
    - Network selection by numbered menu
    - Automatically selects the best ESXi host
    - Automatically selects the best datastore accessible by that host
    - Validates CPU and memory
    - Validates datastore capacity
    - Validates IP range
    - Generates VM names automatically
    - Clones Windows VMs
    - Configures CPU
    - Configures memory
    - Expands the first virtual disk if required
    - Configures Windows Sysprep customization
    - Configures static IP
    - Configures subnet mask
    - Configures gateway
    - Configures DNS
    - Configures Windows computer name
    - Configures local Administrator password
    - Connects VM NIC to selected network
    - Powers on VM
    - Deploys multiple VMs sequentially
    - Displays deployment progress
    - Displays final deployment summary

IMPORTANT:
    The Windows template must:
        1. Have VMware Tools installed.
        2. Be Sysprep/customization ready.
        3. Have a supported Windows guest OS.
        4. Have at least one virtual NIC.
        5. Have at least one virtual disk.

    Cluster selection is NOT used.
"""


import atexit
import getpass
import ipaddress
import ssl
import sys
import time

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim


# ============================================================
# CONFIGURATION
# ============================================================

# ------------------------------------------------------------
# Add your vCenter IP addresses / FQDNs here.
#
# These are the vCenters that will appear in the menu.
#
# Example:
#
#     "10.130.80.10"
#     "10.130.80.11"
#     "vcenter-prod.company.local"
#
# ------------------------------------------------------------

VCENTER_SERVERS = [
    "10.130.80.10",
    "10.130.80.11",
    "10.130.80.12",
]


# Extra datastore space reserved for VMware overhead.
DATASTORE_OVERHEAD_GB = 1.0


# Minimum CPU that should remain available on the host.
CPU_SAFETY_MARGIN_PERCENT = 5.0


# Minimum memory that should remain available on the host.
MEMORY_SAFETY_MARGIN_PERCENT = 5.0


# ============================================================
# Utility Functions
# ============================================================

def format_gb(bytes_value):
    """Convert bytes to GB."""

    return bytes_value / (1024 ** 3)


def format_cpu_mhz(mhz):
    """Format CPU MHz in a human-readable format."""

    if mhz >= 1000:
        return f"{mhz / 1000:.2f} GHz"

    return f"{mhz:.0f} MHz"


def get_obj(content, vimtype, name):
    """
    Find a vSphere inventory object by exact name.
    """

    container = content.viewManager.CreateContainerView(
        content.rootFolder,
        vimtype,
        True
    )

    try:

        for obj in container.view:

            if obj.name == name:
                return obj

    finally:

        container.Destroy()

    return None


def get_all_objects(content, vimtype):
    """
    Return all vSphere objects of the requested type.
    """

    container = content.viewManager.CreateContainerView(
        content.rootFolder,
        vimtype,
        True
    )

    try:

        return list(container.view)

    finally:

        container.Destroy()


def print_exception(prefix, exc):
    """
    Display an exception in a consistent format.
    """

    print()
    print("=" * 70)
    print(prefix)
    print("=" * 70)
    print(f"Error: {exc}")
    print("=" * 70)


# ============================================================
# vCenter Selection
# ============================================================

def choose_vcenter():
    """
    Display configured vCenter servers and allow the user
    to select one by number.
    """

    if not VCENTER_SERVERS:

        raise RuntimeError(
            "No vCenter servers are configured."
        )

    print()
    print("=" * 70)
    print("AVAILABLE VCENTER SERVERS")
    print("=" * 70)

    for index, vcenter in enumerate(
        VCENTER_SERVERS,
        start=1
    ):

        print(
            f"{index:3}. {vcenter}"
        )

    print("=" * 70)

    while True:

        try:

            selection = int(
                input(
                    "Select vCenter number: "
                ).strip()
            )

            if 1 <= selection <= len(
                VCENTER_SERVERS
            ):

                selected_vcenter = (
                    VCENTER_SERVERS[
                        selection - 1
                    ]
                )

                print()
                print(
                    f"[OK] Selected vCenter: "
                    f"{selected_vcenter}"
                )

                return selected_vcenter

            print(
                f"Please select a number from "
                f"1 to {len(VCENTER_SERVERS)}."
            )

        except ValueError:

            print(
                "Please enter a valid number."
            )


# ============================================================
# vCenter Connection
# ============================================================

def connect_vcenter(
    host,
    user,
    password
):
    """
    Connect to VMware vCenter using SmartConnect.

    SSL certificate verification is disabled intentionally.
    """

    try:

        print()
        print("=" * 70)
        print("CONNECTING TO VCENTER")
        print("=" * 70)

        print(
            f"vCenter : {host}"
        )

        print(
            f"User    : {user}"
        )

        context = ssl._create_unverified_context()

        si = SmartConnect(
            host=host,
            user=user,
            pwd=password,
            sslContext=context
        )

        if si is None:

            raise RuntimeError(
                "SmartConnect returned no service instance."
            )

        atexit.register(
            Disconnect,
            si
        )

        print(
            "[OK] Connected to vCenter."
        )

        return si

    except vim.fault.InvalidLogin as exc:

        raise RuntimeError(
            "Authentication failed. "
            "Please verify the username and password."
        ) from exc

    except Exception as exc:

        raise RuntimeError(
            f"Unable to connect to vCenter "
            f"'{host}': {exc}"
        ) from exc


# ============================================================
# VMware Task Handling
# ============================================================

def wait_for_task(
    task,
    task_name="VMware Task"
):
    """
    Wait for VMware asynchronous task completion.
    """

    last_progress = -1

    while True:

        state = task.info.state

        if state == vim.TaskInfo.State.success:

            print(
                f"[OK] {task_name} completed."
            )

            return task.info.result

        if state == vim.TaskInfo.State.error:

            error = task.info.error

            if error is not None:

                message = getattr(
                    error,
                    "msg",
                    str(error)
                )

            else:

                message = (
                    "Unknown VMware task error."
                )

            raise RuntimeError(
                f"{task_name} failed: "
                f"{message}"
            )

        progress = task.info.progress

        if (
            progress is not None
            and progress != last_progress
        ):

            print(
                f"    {task_name} progress: "
                f"{progress}%"
            )

            last_progress = progress

        time.sleep(1)


# ============================================================
# Input Helpers
# ============================================================

def prompt_positive_int(prompt):
    """
    Prompt for a positive integer.
    """

    while True:

        value = input(
            prompt
        ).strip()

        try:

            number = int(value)

            if number <= 0:
                raise ValueError

            return number

        except ValueError:

            print(
                "Please enter a positive integer."
            )


def prompt_ipv4(prompt):
    """
    Prompt for a valid IPv4 address.
    """

    while True:

        value = input(
            prompt
        ).strip()

        try:

            return ipaddress.IPv4Address(
                value
            )

        except ValueError:

            print(
                f"Invalid IPv4 address: {value}"
            )


def prompt_subnet_mask(prompt):
    """
    Prompt for a valid IPv4 subnet mask.
    """

    while True:

        value = input(
            prompt
        ).strip()

        try:

            mask = ipaddress.IPv4Address(
                value
            )

            # Validate contiguous subnet mask.
            ipaddress.IPv4Network(
                f"0.0.0.0/{mask}"
            )

            return mask

        except ValueError:

            print(
                "Invalid subnet mask."
            )

            print(
                "Example: 255.255.255.0"
            )


def choose_from_list(
    items,
    title
):
    """
    Display objects in a numbered menu.
    """

    if not items:

        raise RuntimeError(
            f"No {title.lower()} were discovered."
        )

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    for index, item in enumerate(
        items,
        start=1
    ):

        print(
            f"{index:3}. {item.name}"
        )

    print("=" * 70)

    while True:

        try:

            selection = int(
                input(
                    "Select number: "
                ).strip()
            )

            if (
                1 <= selection <= len(items)
            ):

                return items[
                    selection - 1
                ]

            print(
                f"Please select a number "
                f"from 1 to {len(items)}."
            )

        except ValueError:

            print(
                "Please enter a valid number."
            )


# ============================================================
# Inventory Discovery
# ============================================================

def discover_datacenters(content):

    return get_all_objects(
        content,
        [vim.Datacenter]
    )


def discover_templates(content):
    """
    Discover all VM templates.
    """

    templates = []

    vms = get_all_objects(
        content,
        [vim.VirtualMachine]
    )

    for vm in vms:

        try:

            if (
                vm.config
                and vm.config.template
            ):

                templates.append(vm)

        except Exception:

            continue

    templates.sort(
        key=lambda vm: vm.name.lower()
    )

    return templates


def discover_networks(content):
    """
    Discover standard and distributed networks.
    """

    networks = get_all_objects(
        content,
        [vim.Network]
    )

    networks.sort(
        key=lambda network:
        network.name.lower()
    )

    return networks


def discover_hosts(content):

    hosts = get_all_objects(
        content,
        [vim.HostSystem]
    )

    hosts.sort(
        key=lambda host:
        host.name.lower()
    )

    return hosts


def discover_datastores(content):

    datastores = get_all_objects(
        content,
        [vim.Datastore]
    )

    datastores.sort(
        key=lambda datastore:
        datastore.name.lower()
    )

    return datastores


# ============================================================
# Display Inventory
# ============================================================

def display_inventory(content):
    """
    Display vCenter inventory.

    Cluster selection is deliberately not included.
    """

    print()
    print("=" * 70)
    print("VCENTER INVENTORY DISCOVERY")
    print("=" * 70)

    # --------------------------------------------------------
    # Datacenters
    # --------------------------------------------------------

    datacenters = discover_datacenters(
        content
    )

    print()
    print("Datacenters:")

    if not datacenters:

        print(
            "  None found."
        )

    else:

        for dc in datacenters:

            print(
                f"  - {dc.name}"
            )

    # --------------------------------------------------------
    # ESXi Hosts
    # --------------------------------------------------------

    hosts = discover_hosts(
        content
    )

    print()
    print("ESXi Hosts:")

    if not hosts:

        print(
            "  None found."
        )

    else:

        for host in hosts:

            try:

                connection = (
                    host.runtime.connectionState
                )

                maintenance = (
                    host.runtime.inMaintenanceMode
                )

                print(
                    f"  - {host.name} "
                    f"[Connection={connection}, "
                    f"Maintenance={maintenance}]"
                )

            except Exception:

                print(
                    f"  - {host.name}"
                )

    # --------------------------------------------------------
    # Datastores
    # --------------------------------------------------------

    datastores = discover_datastores(
        content
    )

    print()
    print("Datastores:")

    if not datastores:

        print(
            "  None found."
        )

    else:

        for datastore in datastores:

            try:

                free = format_gb(
                    datastore.summary.freeSpace
                )

                capacity = format_gb(
                    datastore.summary.capacity
                )

                accessible = (
                    datastore.summary.accessible
                )

                print(
                    f"  - {datastore.name} "
                    f"[Free={free:.2f} GB, "
                    f"Capacity={capacity:.2f} GB, "
                    f"Accessible={accessible}]"
                )

            except Exception:

                print(
                    f"  - {datastore.name}"
                )

    # --------------------------------------------------------
    # Networks
    # --------------------------------------------------------

    networks = discover_networks(
        content
    )

    print()
    print("Networks / Port Groups:")

    if not networks:

        print(
            "  None found."
        )

    else:

        for network in networks:

            print(
                f"  - {network.name}"
            )

    # --------------------------------------------------------
    # Templates
    # --------------------------------------------------------

    templates = discover_templates(
        content
    )

    print()
    print("Templates:")

    if not templates:

        print(
            "  None found."
        )

    else:

        for template in templates:

            print(
                f"  - {template.name}"
            )

    print()
    print("=" * 70)


# ============================================================
# Host Resource Functions
# ============================================================

def get_host_total_cpu_mhz(host):

    cpu_info = (
        host.hardware.cpuInfo
    )

    return (
        cpu_info.numCpuCores
        * cpu_info.hz
        / 1_000_000
    )


def get_host_used_cpu_mhz(host):

    usage = (
        host.summary.quickStats.overallCpuUsage
    )

    if usage is None:
        return 0.0

    return float(usage)


def get_host_free_cpu_mhz(host):

    total = get_host_total_cpu_mhz(
        host
    )

    used = get_host_used_cpu_mhz(
        host
    )

    return max(
        0.0,
        total - used
    )


def get_host_total_memory_gb(host):

    return format_gb(
        host.hardware.memorySize
    )


def get_host_used_memory_gb(host):

    usage_mb = (
        host.summary.quickStats.overallMemoryUsage
    )

    if usage_mb is None:
        return 0.0

    return usage_mb / 1024


def get_host_free_memory_gb(host):

    total = get_host_total_memory_gb(
        host
    )

    used = get_host_used_memory_gb(
        host
    )

    return max(
        0.0,
        total - used
    )


# ============================================================
# Best ESXi Host
# ============================================================

def get_best_host(
    content,
    cpu_needed,
    memory_gb_needed
):
    """
    Select the best ESXi host.

    Requirements:
        - Connected
        - Not in maintenance mode
        - Enough CPU
        - Enough memory
        - Highest remaining resources
    """

    hosts = discover_hosts(
        content
    )

    candidates = []

    print()
    print("=" * 70)
    print("ESXi HOST RESOURCE EVALUATION")
    print("=" * 70)

    for host in hosts:

        try:

            if (
                host.runtime.connectionState
                != "connected"
            ):

                print(
                    f"[SKIP] {host.name}: "
                    f"Host not connected."
                )

                continue

            if (
                host.runtime.inMaintenanceMode
            ):

                print(
                    f"[SKIP] {host.name}: "
                    f"Host is in maintenance mode."
                )

                continue

            total_cpu_mhz = (
                get_host_total_cpu_mhz(
                    host
                )
            )

            free_cpu_mhz = (
                get_host_free_cpu_mhz(
                    host
                )
            )

            total_memory_gb = (
                get_host_total_memory_gb(
                    host
                )
            )

            free_memory_gb = (
                get_host_free_memory_gb(
                    host
                )
            )

            average_core_mhz = (
                total_cpu_mhz
                /
                max(
                    1,
                    host.hardware.cpuInfo.numCpuCores
                )
            )

            requested_cpu_mhz = (
                cpu_needed
                *
                average_core_mhz
            )

            cpu_after = (
                free_cpu_mhz
                -
                requested_cpu_mhz
            )

            memory_after = (
                free_memory_gb
                -
                memory_gb_needed
            )

            minimum_cpu_after = (
                total_cpu_mhz
                *
                CPU_SAFETY_MARGIN_PERCENT
                /
                100
            )

            minimum_memory_after = (
                total_memory_gb
                *
                MEMORY_SAFETY_MARGIN_PERCENT
                /
                100
            )

            enough_cpu = (
                cpu_after
                >=
                minimum_cpu_after
            )

            enough_memory = (
                memory_after
                >=
                minimum_memory_after
            )

            print()
            print(
                f"Host: {host.name}"
            )

            print(
                f"  CPU Free        : "
                f"{format_cpu_mhz(free_cpu_mhz)}"
            )

            print(
                f"  CPU Required    : "
                f"{format_cpu_mhz(requested_cpu_mhz)}"
            )

            print(
                f"  Memory Free     : "
                f"{free_memory_gb:.2f} GB"
            )

            print(
                f"  Memory Required : "
                f"{memory_gb_needed} GB"
            )

            if not enough_cpu:

                print(
                    "  Result          : "
                    "INSUFFICIENT CPU"
                )

                continue

            if not enough_memory:

                print(
                    "  Result          : "
                    "INSUFFICIENT MEMORY"
                )

                continue

            candidates.append(
                {
                    "host": host,
                    "free_cpu_mhz":
                        free_cpu_mhz,
                    "free_memory_gb":
                        free_memory_gb
                }
            )

            print(
                "  Result          : "
                "SUITABLE"
            )

        except Exception as exc:

            print(
                f"[SKIP] {host.name}: "
                f"{exc}"
            )

    if not candidates:

        raise RuntimeError(
            "No suitable ESXi host found "
            "with enough CPU and memory."
        )

    candidates.sort(
        key=lambda item: (
            item["free_memory_gb"],
            item["free_cpu_mhz"]
        ),
        reverse=True
    )

    selected = candidates[0]

    host = selected["host"]

    print()
    print("=" * 70)
    print("SELECTED ESXi HOST")
    print("=" * 70)

    print(
        f"Host        : {host.name}"
    )

    print(
        f"Free CPU    : "
        f"{format_cpu_mhz(selected['free_cpu_mhz'])}"
    )

    print(
        f"Free Memory : "
        f"{selected['free_memory_gb']:.2f} GB"
    )

    print("=" * 70)

    return host


# ============================================================
# Datastore Accessibility
# ============================================================

def datastore_is_accessible_from_host(
    datastore,
    host
):
    """
    Check whether datastore is mounted by the selected host.

    This is important because a datastore may be visible in
    vCenter but not mounted/accesssible by a particular host.
    """

    try:

        host_datastores = list(
            host.datastore
        )

        for host_datastore in host_datastores:

            if (
                host_datastore._moId
                ==
                datastore._moId
            ):

                return True

        return False

    except Exception:

        return False


def datastore_is_healthy(datastore):
    """
    Check basic datastore health.
    """

    try:

        summary = datastore.summary

        if not summary.accessible:
            return False

        if summary.capacity <= 0:
            return False

        if summary.freeSpace < 0:
            return False

        maintenance_mode = getattr(
            summary,
            "maintenanceMode",
            "normal"
        )

        if maintenance_mode not in (
            None,
            "normal"
        ):

            return False

        return True

    except Exception:

        return False


# ============================================================
# Best Datastore
# ============================================================

def get_best_datastore(
    content,
    host,
    requested_disk_size_gb
):
    """
    Select datastore with maximum free space.

    It MUST:
        - Be accessible
        - Be healthy
        - Be mounted on selected ESXi host
        - Have enough free space
    """

    datastores = discover_datastores(
        content
    )

    candidates = []

    required_free_gb = (
        requested_disk_size_gb
        +
        DATASTORE_OVERHEAD_GB
    )

    print()
    print("=" * 70)
    print("DATASTORE EVALUATION")
    print("=" * 70)

    print(
        f"Selected Host       : {host.name}"
    )

    print(
        f"Requested Disk Size : "
        f"{requested_disk_size_gb} GB"
    )

    print(
        f"Required Free Space : "
        f"{required_free_gb:.2f} GB"
    )

    print("=" * 70)

    for datastore in datastores:

        try:

            summary = datastore.summary

            free_gb = format_gb(
                summary.freeSpace
            )

            capacity_gb = format_gb(
                summary.capacity
            )

            print()
            print(
                f"Datastore: "
                f"{datastore.name}"
            )

            print(
                f"  Capacity       : "
                f"{capacity_gb:.2f} GB"
            )

            print(
                f"  Free Space     : "
                f"{free_gb:.2f} GB"
            )

            print(
                f"  vCenter Access : "
                f"{summary.accessible}"
            )

            if not summary.accessible:

                print(
                    "  Result         : "
                    "SKIP - inaccessible"
                )

                continue

            if not datastore_is_healthy(
                datastore
            ):

                print(
                    "  Result         : "
                    "SKIP - unhealthy"
                )

                continue

            host_access = (
                datastore_is_accessible_from_host(
                    datastore,
                    host
                )
            )

            print(
                f"  Host Access    : "
                f"{host_access}"
            )

            if not host_access:

                print(
                    "  Result         : "
                    f"SKIP - not mounted on "
                    f"{host.name}"
                )

                continue

            if free_gb < required_free_gb:

                print(
                    "  Result         : "
                    "SKIP - insufficient space"
                )

                continue

            candidates.append(
                {
                    "datastore":
                        datastore,
                    "free_gb":
                        free_gb
                }
            )

            print(
                "  Result         : "
                "SUITABLE"
            )

        except Exception as exc:

            print(
                f"  Result         : "
                f"SKIP - {exc}"
            )

    if not candidates:

        raise RuntimeError(
            f"No suitable datastore found. "
            f"Host '{host.name}' does not have "
            f"an accessible healthy datastore "
            f"with at least "
            f"{required_free_gb:.2f} GB free."
        )

    candidates.sort(
        key=lambda item:
        item["free_gb"],
        reverse=True
    )

    selected = candidates[0]

    datastore = selected[
        "datastore"
    ]

    print()
    print("=" * 70)
    print("SELECTED DATASTORE")
    print("=" * 70)

    print(
        f"Datastore  : "
        f"{datastore.name}"
    )

    print(
        f"Free Space : "
        f"{selected['free_gb']:.2f} GB"
    )

    print(
        f"Host       : "
        f"{host.name}"
    )

    print("=" * 70)

    return datastore


# ============================================================
# Resource Pool
# ============================================================

def get_host_resource_pool(host):
    """
    Get the resource pool associated with the ESXi host.

    No cluster selection is performed.
    """

    parent = host.parent

    if parent is None:

        raise RuntimeError(
            f"Host '{host.name}' has no parent "
            f"compute resource."
        )

    resource_pool = getattr(
        parent,
        "resourcePool",
        None
    )

    if resource_pool is None:

        raise RuntimeError(
            f"Unable to determine resource pool "
            f"for host '{host.name}'."
        )

    return resource_pool


# ============================================================
# Relocate Specification
# ============================================================

def build_relocate_spec(
    host,
    datastore
):
    """
    Build VM relocation specification.
    """

    relocate = (
        vim.vm.RelocateSpec()
    )

    relocate.host = host

    relocate.datastore = datastore

    relocate.pool = (
        get_host_resource_pool(
            host
        )
    )

    return relocate


# ============================================================
# Windows Customization
# ============================================================

def build_windows_customization_spec(
    vm_name,
    ip_address,
    subnet_mask,
    gateway,
    dns_server,
    local_admin_password
):
    """
    Build Windows VMware Guest Customization.

    Configures:
        - Computer name
        - Static IP
        - Subnet mask
        - Gateway
        - DNS
        - Administrator password
    """

    # --------------------------------------------------------
    # Network adapter configuration
    # --------------------------------------------------------

    adapter_mapping = (
        vim.vm.customization.AdapterMapping()
    )

    ip_settings = (
        vim.vm.customization.IPSettings()
    )

    fixed_ip = (
        vim.vm.customization.FixedIp()
    )

    fixed_ip.ipAddress = str(
        ip_address
    )

    ip_settings.ip = fixed_ip

    ip_settings.subnetMask = str(
        subnet_mask
    )

    ip_settings.gateway = [
        str(gateway)
    ]

    adapter_mapping.adapter = (
        ip_settings
    )

    # --------------------------------------------------------
    # Global DNS
    # --------------------------------------------------------

    global_ip_settings = (
        vim.vm.customization.GlobalIPSettings()
    )

    global_ip_settings.dnsServerList = [
        str(dns_server)
    ]

    # --------------------------------------------------------
    # Windows Sysprep
    # --------------------------------------------------------

    sysprep = (
        vim.vm.customization.Sysprep()
    )

    # --------------------------------------------------------
    # GUI Unattended
    # --------------------------------------------------------

    gui_unattended = (
        vim.vm.customization.GuiUnattended()
    )

    gui_unattended.autoLogon = False

    gui_unattended.autoLogonCount = 0

    admin_password = (
        vim.vm.customization.Password()
    )

    admin_password.value = (
        local_admin_password
    )

    admin_password.plainText = True

    gui_unattended.password = (
        admin_password
    )

    sysprep.guiUnattended = (
        gui_unattended
    )

    # --------------------------------------------------------
    # Windows computer name
    # --------------------------------------------------------

    user_data = (
        vim.vm.customization.UserData()
    )

    if len(vm_name) > 15:

        raise ValueError(
            f"VM name '{vm_name}' is "
            f"{len(vm_name)} characters. "
            f"Windows computer names should "
            f"not exceed 15 characters."
        )

    computer_name = (
        vim.vm.customization.FixedName()
    )

    computer_name.name = (
        vm_name
    )

    user_data.computerName = (
        computer_name
    )

    user_data.fullName = (
        "VM Administrator"
    )

    user_data.orgName = (
        "VMware"
    )

    sysprep.userData = (
        user_data
    )

    # --------------------------------------------------------
    # Workgroup
    # --------------------------------------------------------

    identification = (
        vim.vm.customization.Identification()
    )

    identification.joinWorkgroup = (
        "WORKGROUP"
    )

    sysprep.identification = (
        identification
    )

    # --------------------------------------------------------
    # Final specification
    # --------------------------------------------------------

    customization_spec = (
        vim.vm.customization.Specification()
    )

    customization_spec.nicSettingMap = [
        adapter_mapping
    ]

    customization_spec.globalIPSettings = (
        global_ip_settings
    )

    customization_spec.identity = (
        sysprep
    )

    return customization_spec


# ============================================================
# Network Device Changes
# ============================================================

def build_network_device_changes(
    template,
    network
):
    """
    Connect all template virtual NICs to the selected network.
    """

    device_changes = []

    for device in (
        template.config.hardware.device
    ):

        if isinstance(
            device,
            vim.vm.device.VirtualEthernetCard
        ):

            nic_spec = (
                vim.vm.device.VirtualDeviceSpec()
            )

            nic_spec.operation = (
                vim.vm.device.VirtualDeviceSpec
                .Operation.edit
            )

            backing = (
                vim.vm.device.VirtualEthernetCard
                .NetworkBackingInfo()
            )

            backing.network = network

            backing.deviceName = (
                network.name
            )

            device.backing = backing

            if device.connectable is None:

                device.connectable = (
                    vim.vm.device.VirtualDevice
                    .ConnectInfo()
                )

            device.connectable.startConnected = True

            device.connectable.connected = True

            device.connectable.allowGuestControl = True

            nic_spec.device = device

            device_changes.append(
                nic_spec
            )

    if not device_changes:

        raise RuntimeError(
            "Selected template does not contain "
            "a virtual Ethernet adapter."
        )

    return device_changes


# ============================================================
# Disk Functions
# ============================================================

def get_first_virtual_disk(vm):

    for device in (
        vm.config.hardware.device
    ):

        if isinstance(
            device,
            vim.vm.device.VirtualDisk
        ):

            return device

    return None


def get_template_disk_size_gb(
    template
):

    disk = get_first_virtual_disk(
        template
    )

    if disk is None:

        raise RuntimeError(
            f"Template '{template.name}' "
            f"has no virtual disk."
        )

    return (
        disk.capacityInKB
        /
        1024
        /
        1024
    )


def expand_disk_if_required(
    vm,
    requested_disk_size_gb
):
    """
    Expand first virtual disk if necessary.
    """

    disk = get_first_virtual_disk(
        vm
    )

    if disk is None:

        raise RuntimeError(
            f"VM '{vm.name}' has no virtual disk."
        )

    current_disk_gb = (
        disk.capacityInKB
        /
        1024
        /
        1024
    )

    print(
        f"Current Disk   : "
        f"{current_disk_gb:.2f} GB"
    )

    print(
        f"Requested Disk : "
        f"{requested_disk_size_gb} GB"
    )

    if (
        requested_disk_size_gb
        <= current_disk_gb
    ):

        print(
            "Disk Expansion : "
            "Not required"
        )

        return False

    print(
        f"Expanding disk "
        f"{current_disk_gb:.2f} -> "
        f"{requested_disk_size_gb:.2f} GB"
    )

    new_capacity_kb = int(
        requested_disk_size_gb
        *
        1024
        *
        1024
    )

    disk_spec = (
        vim.vm.ConfigSpec()
    )

    disk_change = (
        vim.vm.device.VirtualDeviceSpec()
    )

    disk_change.operation = (
        vim.vm.device.VirtualDeviceSpec
        .Operation.edit
    )

    disk.capacityInKB = (
        new_capacity_kb
    )

    disk_change.device = disk

    disk_spec.deviceChange = [
        disk_change
    ]

    task = vm.ReconfigVM_Task(
        spec=disk_spec
    )

    wait_for_task(
        task,
        f"Disk expansion for {vm.name}"
    )

    print(
        "[OK] Disk expansion completed."
    )

    return True


# ============================================================
# VM Existence
# ============================================================

def vm_exists(
    content,
    vm_name
):

    vm = get_obj(
        content,
        [vim.VirtualMachine],
        vm_name
    )

    return vm is not None


# ============================================================
# IP Validation
# ============================================================

def validate_ip_range(
    starting_ip,
    subnet_mask,
    vm_count
):
    """
    Validate requested sequential IP addresses.

    Prevents:
        - Network address
        - Broadcast address
        - IPs outside subnet
    """

    network = ipaddress.IPv4Network(
        f"{starting_ip}/{subnet_mask}",
        strict=False
    )

    usable_hosts = list(
        network.hosts()
    )

    required_ips = []

    current_ip = starting_ip

    for _ in range(vm_count):

        if current_ip not in network:

            raise ValueError(
                f"IP {current_ip} is outside "
                f"subnet {network}."
            )

        if current_ip not in usable_hosts:

            raise ValueError(
                f"IP {current_ip} is not a usable "
                f"host address in {network}."
            )

        required_ips.append(
            current_ip
        )

        current_ip = ipaddress.IPv4Address(
            int(current_ip) + 1
        )

    return required_ips


# ============================================================
# VM Name Generation
# ============================================================

def generate_vm_name(
    naming_context,
    ip_address
):
    """
    Generate:

        NamingContext + ThirdOctet + FourthOctet

    Example:

        HDS
        192.168.231.100

        becomes:

        HDS231100
    """

    octets = str(
        ip_address
    ).split(".")

    if len(octets) != 4:

        raise ValueError(
            f"Invalid IPv4 address: "
            f"{ip_address}"
        )

    third_octet = octets[2]

    fourth_octet = octets[3]

    vm_name = (
        naming_context.upper()
        +
        third_octet
        +
        fourth_octet
    )

    if len(vm_name) > 15:

        raise ValueError(
            f"Generated VM name "
            f"'{vm_name}' is "
            f"{len(vm_name)} characters. "
            f"Windows computer names "
            f"should not exceed 15 characters."
        )

    return vm_name


# ============================================================
# Clone VM
# ============================================================

def clone_vm(
    template,
    vm_name,
    ip_address,
    subnet_mask,
    gateway,
    dns_server,
    local_admin_password,
    host,
    datastore,
    network,
    cpu_count,
    memory_gb,
    disk_size_gb
):
    """
    Clone one Windows VM.
    """

    print()
    print("=" * 70)
    print(
        f"DEPLOYING VM: {vm_name}"
    )
    print("=" * 70)

    print(
        f"VM Name    : {vm_name}"
    )

    print(
        f"IP Address : {ip_address}"
    )

    print(
        f"Host       : {host.name}"
    )

    print(
        f"Datastore  : {datastore.name}"
    )

    print(
        f"Network    : {network.name}"
    )

    print(
        f"CPU        : {cpu_count}"
    )

    print(
        f"Memory     : {memory_gb} GB"
    )

    print(
        f"Disk       : {disk_size_gb} GB"
    )

    # --------------------------------------------------------
    # Relocation
    # --------------------------------------------------------

    relocate_spec = build_relocate_spec(
        host,
        datastore
    )

    # --------------------------------------------------------
    # Hardware
    # --------------------------------------------------------

    config_spec = (
        vim.vm.ConfigSpec()
    )

    config_spec.numCPUs = (
        cpu_count
    )

    config_spec.memoryMB = (
        memory_gb * 1024
    )

    # --------------------------------------------------------
    # Network
    # --------------------------------------------------------

    config_spec.deviceChange = (
        build_network_device_changes(
            template,
            network
        )
    )

    # --------------------------------------------------------
    # Windows Customization
    # --------------------------------------------------------

    customization_spec = (
        build_windows_customization_spec(
            vm_name=vm_name,
            ip_address=ip_address,
            subnet_mask=subnet_mask,
            gateway=gateway,
            dns_server=dns_server,
            local_admin_password=
                local_admin_password
        )
    )

    # --------------------------------------------------------
    # Clone Specification
    # --------------------------------------------------------

    clone_spec = (
        vim.vm.CloneSpec()
    )

    clone_spec.location = (
        relocate_spec
    )

    clone_spec.config = (
        config_spec
    )

    clone_spec.customization = (
        customization_spec
    )

    clone_spec.powerOn = False

    clone_spec.template = False

    # --------------------------------------------------------
    # Clone
    # --------------------------------------------------------

    print()
    print(
        "[1/3] Starting VM clone..."
    )

    try:

        task = template.Clone(
            folder=template.parent,
            name=vm_name,
            spec=clone_spec
        )

        vm = wait_for_task(
            task,
            f"Clone {vm_name}"
        )

    except Exception as exc:

        raise RuntimeError(
            f"Clone failed for "
            f"'{vm_name}': {exc}"
        ) from exc

    print(
        f"[OK] Clone completed: "
        f"{vm_name}"
    )

    # --------------------------------------------------------
    # Disk Expansion
    # --------------------------------------------------------

    print()
    print(
        "[2/3] Checking disk..."
    )

    try:

        expand_disk_if_required(
            vm,
            disk_size_gb
        )

    except Exception as exc:

        raise RuntimeError(
            f"Disk expansion failed for "
            f"'{vm_name}': {exc}"
        ) from exc

    # --------------------------------------------------------
    # Power On
    # --------------------------------------------------------

    print()
    print(
        "[3/3] Powering on VM..."
    )

    try:

        power_task = (
            vm.PowerOnVM_Task()
        )

        wait_for_task(
            power_task,
            f"Power on {vm_name}"
        )

    except Exception as exc:

        raise RuntimeError(
            f"Power-on failed for "
            f"'{vm_name}': {exc}"
        ) from exc

    print()
    print("=" * 70)
    print(
        f"[SUCCESS] {vm_name} "
        f"-> {ip_address}"
    )
    print("=" * 70)

    return vm


# ============================================================
# Multiple VM Deployment
# ============================================================

def deploy_multiple_vms(
    content,
    template,
    network,
    host,
    datastore,
    cpu_count,
    memory_gb,
    disk_size_gb,
    vm_count,
    naming_context,
    starting_ip,
    subnet_mask,
    gateway,
    dns_server,
    local_admin_password
):
    """
    Deploy multiple VMs sequentially.
    """

    # --------------------------------------------------------
    # Validate IP range
    # --------------------------------------------------------

    ip_addresses = validate_ip_range(
        starting_ip,
        subnet_mask,
        vm_count
    )

    # --------------------------------------------------------
    # Build deployment plan
    # --------------------------------------------------------

    deployment_plan = []

    for ip_address in ip_addresses:

        vm_name = generate_vm_name(
            naming_context,
            ip_address
        )

        deployment_plan.append(
            {
                "name": vm_name,
                "ip": ip_address
            }
        )

    # --------------------------------------------------------
    # Check existing VMs before starting
    # --------------------------------------------------------

    for item in deployment_plan:

        if vm_exists(
            content,
            item["name"]
        ):

            raise RuntimeError(
                f"VM '{item['name']}' already exists. "
                f"Deployment stopped before creating "
                f"any VMs."
            )

    # --------------------------------------------------------
    # Display plan
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("DEPLOYMENT PLAN")
    print("=" * 70)

    print(
        f"Template  : {template.name}"
    )

    print(
        f"Host      : {host.name}"
    )

    print(
        f"Datastore : {datastore.name}"
    )

    print(
        f"Network   : {network.name}"
    )

    print()

    for index, item in enumerate(
        deployment_plan,
        start=1
    ):

        print(
            f"{index:3}. "
            f"{item['name']} "
            f"-> "
            f"{item['ip']}"
        )

    print("=" * 70)

    # --------------------------------------------------------
    # Deploy sequentially
    # --------------------------------------------------------

    successful = []

    failed = []

    for index, item in enumerate(
        deployment_plan,
        start=1
    ):

        vm_name = item["name"]

        ip_address = item["ip"]

        print()
        print("#" * 70)

        print(
            f"VM {index}/{vm_count}: "
            f"{vm_name}"
        )

        print(
            f"IP Address: "
            f"{ip_address}"
        )

        print("#" * 70)

        try:

            vm = clone_vm(
                template=template,
                vm_name=vm_name,
                ip_address=ip_address,
                subnet_mask=subnet_mask,
                gateway=gateway,
                dns_server=dns_server,
                local_admin_password=
                    local_admin_password,
                host=host,
                datastore=datastore,
                network=network,
                cpu_count=cpu_count,
                memory_gb=memory_gb,
                disk_size_gb=disk_size_gb
            )

            successful.append(
                {
                    "name": vm.name,
                    "ip": str(ip_address),
                    "host": host.name,
                    "datastore":
                        datastore.name,
                    "network":
                        network.name
                }
            )

        except Exception as exc:

            failed.append(
                {
                    "name": vm_name,
                    "ip": str(ip_address),
                    "error": str(exc)
                }
            )

            print()
            print(
                f"[FAILED] "
                f"{vm_name}: "
                f"{exc}"
            )

            # Continue with next VM.
            continue

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("DEPLOYMENT COMPLETED")
    print("=" * 70)

    if successful:

        print()
        print("Successful VMs:")

        for item in successful:

            print(
                f"  {item['name']} "
                f"-> "
                f"{item['ip']}"
            )

            print(
                f"      Host      : "
                f"{item['host']}"
            )

            print(
                f"      Datastore : "
                f"{item['datastore']}"
            )

            print(
                f"      Network   : "
                f"{item['network']}"
            )

    if failed:

        print()
        print("Failed VMs:")

        for item in failed:

            print(
                f"  {item['name']} "
                f"-> "
                f"{item['ip']}"
            )

            print(
                f"      Error: "
                f"{item['error']}"
            )

    print()
    print(
        f"Successful : "
        f"{len(successful)}"
    )

    print(
        f"Failed     : "
        f"{len(failed)}"
    )

    print("=" * 70)

    return successful, failed


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("VMWARE WINDOWS VM BULK DEPLOYMENT")
    print("=" * 70)

    print()
    print(
        "Cluster selection is NOT used."
    )

    # ========================================================
    # vCenter Selection
    # ========================================================

    vc_host = choose_vcenter()

    # ========================================================
    # Credentials
    # ========================================================

    username = input(
        "Username: "
    ).strip()

    if not username:

        raise ValueError(
            "Username cannot be empty."
        )

    password = getpass.getpass(
        "Password: "
    )

    if not password:

        raise ValueError(
            "Password cannot be empty."
        )

    # ========================================================
    # VM Configuration
    # ========================================================

    cpu_count = prompt_positive_int(
        "CPU Count: "
    )

    memory_gb = prompt_positive_int(
        "Memory (GB): "
    )

    disk_size_gb = prompt_positive_int(
        "Disk Size (GB): "
    )

    vm_count = prompt_positive_int(
        "Number of VMs to create: "
    )

    naming_context = input(
        "Naming Context "
        "(Example: HDS/MGM/DEV/APP): "
    ).strip().upper()

    if not naming_context:

        raise ValueError(
            "Naming Context cannot be empty."
        )

    # ========================================================
    # Network Configuration
    # ========================================================

    starting_ip = prompt_ipv4(
        "Starting IP Address: "
    )

    subnet_mask = prompt_subnet_mask(
        "Subnet Mask: "
    )

    gateway = prompt_ipv4(
        "Gateway: "
    )

    dns_server = prompt_ipv4(
        "DNS Server: "
    )

    # ========================================================
    # Windows Administrator Password
    # ========================================================

    local_admin_password = (
        getpass.getpass(
            "Local Administrator Password: "
        )
    )

    if not local_admin_password:

        raise ValueError(
            "Local Administrator Password "
            "cannot be empty."
        )

    # ========================================================
    # Optional Datacenter
    # ========================================================

    datacenter_name = input(
        "Datacenter Name (Optional): "
    ).strip()

    # ========================================================
    # Connect
    # ========================================================

    try:

        si = connect_vcenter(
            vc_host,
            username,
            password
        )

        content = (
            si.RetrieveContent()
        )

        # ====================================================
        # Discovery
        # ====================================================

        display_inventory(
            content
        )

        # ====================================================
        # Datacenter
        # ====================================================

        datacenters = (
            discover_datacenters(
                content
            )
        )

        datacenter = None

        if datacenter_name:

            datacenter = get_obj(
                content,
                [vim.Datacenter],
                datacenter_name
            )

            if datacenter is None:

                raise RuntimeError(
                    f"Datacenter "
                    f"'{datacenter_name}' "
                    f"not found."
                )

            print()
            print(
                f"[OK] Datacenter: "
                f"{datacenter.name}"
            )

        elif len(datacenters) == 1:

            datacenter = (
                datacenters[0]
            )

            print()
            print(
                f"[OK] Automatically selected "
                f"datacenter: "
                f"{datacenter.name}"
            )

        elif len(datacenters) > 1:

            datacenter = choose_from_list(
                datacenters,
                "Datacenters"
            )

            print()
            print(
                f"[OK] Datacenter: "
                f"{datacenter.name}"
            )

        else:

            raise RuntimeError(
                "No datacenters found."
            )

        # ====================================================
        # Template Selection
        # ====================================================

        templates = (
            discover_templates(
                content
            )
        )

        if not templates:

            raise RuntimeError(
                "No VMware templates found."
            )

        template = choose_from_list(
            templates,
            "AVAILABLE TEMPLATES"
        )

        if not template.config.template:

            raise RuntimeError(
                f"'{template.name}' "
                f"is not a template."
            )

        print()
        print(
            f"[OK] Selected Template: "
            f"{template.name}"
        )

        # ====================================================
        # Network Selection
        # ====================================================

        networks = (
            discover_networks(
                content
            )
        )

        if not networks:

            raise RuntimeError(
                "No networks / port groups found."
            )

        network = choose_from_list(
            networks,
            "AVAILABLE NETWORKS / PORT GROUPS"
        )

        print()
        print(
            f"[OK] Selected Network: "
            f"{network.name}"
        )

        # ====================================================
        # IP Validation
        # ====================================================

        print()
        print(
            "Validating IP range..."
        )

        ip_addresses = (
            validate_ip_range(
                starting_ip,
                subnet_mask,
                vm_count
            )
        )

        print(
            f"[OK] {len(ip_addresses)} "
            f"IP addresses available."
        )

        # ====================================================
        # VM Name Preview
        # ====================================================

        print()
        print("=" * 70)
        print("VM NAME / IP PREVIEW")
        print("=" * 70)

        for ip_address in ip_addresses:

            vm_name = generate_vm_name(
                naming_context,
                ip_address
            )

            print(
                f"{ip_address} "
                f"-> "
                f"{vm_name}"
            )

        print("=" * 70)

        # ====================================================
        # Best ESXi Host
        # ====================================================

        host = get_best_host(
            content,
            cpu_count,
            memory_gb
        )

        # ====================================================
        # Best Datastore
        # ========================================================

        datastore = (
            get_best_datastore(
                content,
                host,
                disk_size_gb
            )
        )

        # ====================================================
        # Template Disk Information
        # ====================================================

        template_disk_gb = (
            get_template_disk_size_gb(
                template
            )
        )

        # ====================================================
        # Final Configuration
        # ====================================================

        print()
        print("=" * 70)
        print("FINAL DEPLOYMENT CONFIGURATION")
        print("=" * 70)

        print(
            f"vCenter             : "
            f"{vc_host}"
        )

        print(
            f"Datacenter          : "
            f"{datacenter.name}"
        )

        print(
            f"Template            : "
            f"{template.name}"
        )

        print(
            f"Template Disk       : "
            f"{template_disk_gb:.2f} GB"
        )

        print(
            f"Requested Disk      : "
            f"{disk_size_gb} GB"
        )

        print(
            f"ESXi Host           : "
            f"{host.name}"
        )

        print(
            f"Datastore           : "
            f"{datastore.name}"
        )

        print(
            f"Network             : "
            f"{network.name}"
        )

        print(
            f"CPU                 : "
            f"{cpu_count}"
        )

        print(
            f"Memory              : "
            f"{memory_gb} GB"
        )

        print(
            f"VM Count            : "
            f"{vm_count}"
        )

        print(
            f"Naming Context      : "
            f"{naming_context}"
        )

        print(
            f"Starting IP         : "
            f"{starting_ip}"
        )

        print(
            f"Subnet Mask         : "
            f"{subnet_mask}"
        )

        print(
            f"Gateway             : "
            f"{gateway}"
        )

        print(
            f"DNS Server          : "
            f"{dns_server}"
        )

        print(
            "Cluster Selection   : "
            "NOT USED"
        )

        print("=" * 70)

        # ====================================================
        # Confirmation
        # ====================================================

        confirmation = input(
            "\nStart deployment? [y/N]: "
        ).strip().lower()

        if confirmation not in (
            "y",
            "yes"
        ):

            print(
                "\nDeployment cancelled."
            )

            return

        # ====================================================
        # Deploy
        # ====================================================

        deploy_multiple_vms(
            content=content,
            template=template,
            network=network,
            host=host,
            datastore=datastore,
            cpu_count=cpu_count,
            memory_gb=memory_gb,
            disk_size_gb=disk_size_gb,
            vm_count=vm_count,
            naming_context=naming_context,
            starting_ip=starting_ip,
            subnet_mask=subnet_mask,
            gateway=gateway,
            dns_server=dns_server,
            local_admin_password=
                local_admin_password
        )

    # ========================================================
    # Error Handling
    # ========================================================

    except vim.fault.InvalidLogin as exc:

        print_exception(
            "AUTHENTICATION ERROR",
            exc
        )

        sys.exit(1)

    except vim.fault.NoPermission as exc:

        print_exception(
            "VMWARE PERMISSION ERROR",
            exc
        )

        sys.exit(1)

    except vim.fault.NotFound as exc:

        print_exception(
            "VMWARE OBJECT NOT FOUND",
            exc
        )

        sys.exit(1)

    except vim.fault.CustomizationFault as exc:

        print_exception(
            "WINDOWS CUSTOMIZATION ERROR",
            exc
        )

        sys.exit(1)

    except vim.fault.VimFault as exc:

        print_exception(
            "VMWARE FAULT",
            exc
        )

        sys.exit(1)

    except ValueError as exc:

        print_exception(
            "INPUT / VALIDATION ERROR",
            exc
        )

        sys.exit(1)

    except RuntimeError as exc:

        print_exception(
            "DEPLOYMENT ERROR",
            exc
        )

        sys.exit(1)

    except KeyboardInterrupt:

        print(
            "\n\nDeployment interrupted by user."
        )

        sys.exit(130)

    except Exception as exc:

        print_exception(
            "UNEXPECTED ERROR",
            exc
        )

        sys.exit(1)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    main()