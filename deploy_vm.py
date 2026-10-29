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
"""

import atexit
import getpass
import ipaddress
import json
import ssl
import sys
import time
from pathlib import Path

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl


# ============================================================
# Constants
# ============================================================

DATASTORE_OVERHEAD_GB = 1.0
CPU_SAFETY_MARGIN_PERCENT = 5.0
MEMORY_SAFETY_MARGIN_PERCENT = 5.0
VCENTER_CONFIG_FILE = "vcenters.json"


# ============================================================
# Utility Functions
# ============================================================

def format_gb(bytes_value: int) -> float:
    return bytes_value / (1024 ** 3)

def format_cpu_mhz(mhz: int) -> str:
    if mhz >= 1000:
        return f"{mhz / 1000:.2f} GHz"
    return f"{mhz:.0f} MHz"

def get_obj(content, vimtype, name):
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True
    )
    try:
        for obj in container.view:
            if obj.name == name:
                return obj
    finally:
        container.Destroy()
    return None

def get_all_objects(content, vimtype):
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True
    )
    try:
        return list(container.view)
    finally:
        container.Destroy()

def print_exception(prefix: str, exc: Exception):
    print("\n" + "=" * 70)
    print(prefix)
    print("=" * 70)
    print(f"Error: {exc}")
    print("=" * 70)


# ============================================================
# vCenter Configuration
# ============================================================

def load_vcenters():
    config_path = Path(VCENTER_CONFIG_FILE)
    if not config_path.exists():
        raise RuntimeError(f"vCenter configuration file '{VCENTER_CONFIG_FILE}' was not found.")

    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = json.load(file)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in '{VCENTER_CONFIG_FILE}': {exc}") from exc

    vcenters = config.get("vcenters")
    if not isinstance(vcenters, list) or not vcenters:
        raise RuntimeError(f"No vCenters are configured in '{VCENTER_CONFIG_FILE}'.")

    for index, vcenter in enumerate(vcenters, start=1):
        if not isinstance(vcenter, dict):
            raise RuntimeError(f"vCenter entry #{index} is invalid.")
        if not vcenter.get("name"):
            raise RuntimeError(f"vCenter entry #{index} is missing 'name'.")
        if not vcenter.get("host"):
            raise RuntimeError(f"vCenter '{vcenter.get('name')}' is missing 'host'.")
        if not vcenter.get("username"):
            raise RuntimeError(f"vCenter '{vcenter.get('name')}' is missing 'username'.")

    return vcenters

def select_vcenter():
    vcenters = load_vcenters()
    print("\n" + "=" * 70)
    print("SELECT VCENTER")
    print("=" * 70)

    for index, vcenter in enumerate(vcenters, start=1):
        print(f"{index:3}. {vcenter['name']}")
    print()

    while True:
        try:
            selection = int(input("Select vCenter number: ").strip())
            if 1 <= selection <= len(vcenters):
                selected = vcenters[selection - 1]
                print(f"\n[OK] Selected vCenter: {selected['name']}")
                return selected
            print(f"Please select a number from 1 to {len(vcenters)}.")
        except ValueError:
            print("Please enter a valid number.")


# ============================================================
# vCenter Connection
# ============================================================

def connect_vcenter(host: str, user: str, password: str):
    try:
        print("\nConnecting to vCenter...")
        print(f"vCenter : {host}")
        print(f"User    : {user}")

        context = ssl._create_unverified_context()
        si = SmartConnect(host=host, user=user, pwd=password, sslContext=context)

        if si is None:
            raise RuntimeError("SmartConnect returned no service instance.")

        atexit.register(Disconnect, si)
        print("[OK] Connected to vCenter.")
        return si

    except vim.fault.InvalidLogin as exc:
        raise RuntimeError(f"Authentication failed. Check username/password. vCenter returned: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Unable to connect to vCenter '{host}': {exc}") from exc


# ============================================================
# Task Handling
# ============================================================

def wait_for_task(task, task_name="VMware Task"):
    last_progress = -1
    while True:
        state = task.info.state
        if state == vim.TaskInfo.State.success:
            print(f"[OK] {task_name} completed.")
            return task.info.result

        if state == vim.TaskInfo.State.error:
            error = task.info.error
            if error is not None:
                message = getattr(error, "msg", str(error))
            else:
                message = "Unknown VMware task error."
            raise RuntimeError(f"{task_name} failed: {message}")

        progress = task.info.progress
        if progress is not None and progress != last_progress:
            print(f"    {task_name} progress: {progress}%")
            last_progress = progress

        time.sleep(1)


# ============================================================
# Input Helpers
# ============================================================

def prompt_positive_int(prompt: str) -> int:
    while True:
        value = input(prompt).strip()
        try:
            number = int(value)
            if number <= 0:
                raise ValueError
            return number
        except ValueError:
            print("Please enter a positive integer.")

def prompt_ipv4(prompt: str) -> ipaddress.IPv4Address:
    while True:
        value = input(prompt).strip()
        try:
            address = ipaddress.IPv4Address(value)
            return address
        except ValueError:
            print(f"Invalid IPv4 address: {value}")

def prompt_subnet_mask(prompt: str) -> ipaddress.IPv4Address:
    while True:
        value = input(prompt).strip()
        try:
            mask = ipaddress.IPv4Address(value)
            ipaddress.IPv4Network(f"0.0.0.0/{mask}")
            return mask
        except ValueError:
            print("Invalid subnet mask. Example: 255.255.255.0")

def choose_from_list(items, title: str):
    if not items:
        raise RuntimeError(f"No {title.lower()} were discovered.")
    
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    for index, item in enumerate(items, start=1):
        print(f"{index:3}. {item.name}")
    print()

    while True:
        try:
            selection = int(input(f"Select {title[:-1]} number: ").strip())
            if 1 <= selection <= len(items):
                return items[selection - 1]
            print(f"Please select a number from 1 to {len(items)}.")
        except ValueError:
            print("Please enter a valid number.")


# ============================================================
# Inventory Discovery
# ============================================================

def discover_datacenters(content):
    return get_all_objects(content, [vim.Datacenter])

def discover_templates(content):
    templates = []
    vms = get_all_objects(content, [vim.VirtualMachine])
    for vm in vms:
        try:
            if vm.config and vm.config.template:
                templates.append(vm)
        except Exception:
            continue
    templates.sort(key=lambda vm: vm.name.lower())
    return templates

def discover_networks(content):
    networks = get_all_objects(content, [vim.Network])
    networks.sort(key=lambda network: network.name.lower())
    return networks

def discover_hosts(content):
    hosts = get_all_objects(content, [vim.HostSystem])
    hosts.sort(key=lambda host: host.name.lower())
    return hosts

def discover_datastores(content):
    datastores = get_all_objects(content, [vim.Datastore])
    datastores.sort(key=lambda datastore: datastore.name.lower())
    return datastores

def display_inventory(content):
    print("\n" + "=" * 70)
    print("vCENTER INVENTORY DISCOVERY")
    print("=" * 70)

    datacenters = discover_datacenters(content)
    print("\nDatacenters:")
    if not datacenters:
        print("  None found.")
    else:
        for dc in datacenters:
            print(f"  - {dc.name}")

    hosts = discover_hosts(content)
    print("\nESXi Hosts:")
    if not hosts:
        print("  None found.")
    else:
        for host in hosts:
            try:
                connection = host.runtime.connectionState
                maintenance = host.runtime.inMaintenanceMode
                print(f"  - {host.name} [Connection={connection}, Maintenance={maintenance}]")
            except Exception:
                print(f"  - {host.name}")

    datastores = discover_datastores(content)
    print("\nDatastores:")
    if not datastores:
        print("  None found.")
    else:
        for datastore in datastores:
            try:
                free = format_gb(datastore.summary.freeSpace)
                capacity = format_gb(datastore.summary.capacity)
                accessible = datastore.summary.accessible
                print(f"  - {datastore.name} [Free={free:.2f} GB, Capacity={capacity:.2f} GB, Accessible={accessible}]")
            except Exception:
                print(f"  - {datastore.name}")

    networks = discover_networks(content)
    print("\nNetworks / Port Groups:")
    if not networks:
        print("  None found.")
    else:
        for network in networks:
            print(f"  - {network.name}")

    templates = discover_templates(content)
    print("\nTemplates:")
    if not templates:
        print("  None found.")
    else:
        for template in templates:
            print(f"  - {template.name}")
    print("\n" + "=" * 70)


# ============================================================
# Host Resource Calculations
# ============================================================

def get_host_total_cpu_mhz(host):
    cpu_info = host.hardware.cpuInfo
    return cpu_info.numCpuCores * cpu_info.hz / 1_000_000

def get_host_used_cpu_mhz(host):
    usage = host.summary.quickStats.overallCpuUsage
    if usage is None:
        return 0.0
    return float(usage)

def get_host_free_cpu_mhz(host):
    total = get_host_total_cpu_mhz(host)
    used = get_host_used_cpu_mhz(host)
    return max(0.0, total - used)

def get_host_total_memory_gb(host):
    return format_gb(host.hardware.memorySize)

def get_host_used_memory_gb(host):
    usage_mb = host.summary.quickStats.overallMemoryUsage
    if usage_mb is None:
        return 0.0
    return usage_mb / 1024

def get_host_free_memory_gb(host):
    total = get_host_total_memory_gb(host)
    used = get_host_used_memory_gb(host)
    return max(0.0, total - used)


# ============================================================
# Best ESXi Host
# ============================================================

def get_best_host(content, cpu_needed: int, memory_gb_needed: int):
    hosts = discover_hosts(content)
    candidates = []

    print("\n" + "=" * 70)
    print("HOST RESOURCE EVALUATION")
    print("=" * 70)

    for host in hosts:
        try:
            if host.runtime.connectionState != "connected":
                print(f"[SKIP] {host.name}: Host is not connected.")
                continue
            if host.runtime.inMaintenanceMode:
                print(f"[SKIP] {host.name}: Host is in maintenance mode.")
                continue

            total_cpu_mhz = get_host_total_cpu_mhz(host)
            free_cpu_mhz = get_host_free_cpu_mhz(host)
            total_memory_gb = get_host_total_memory_gb(host)
            free_memory_gb = get_host_free_memory_gb(host)

            average_core_mhz = total_cpu_mhz / max(1, host.hardware.cpuInfo.numCpuCores)
            requested_cpu_mhz = cpu_needed * average_core_mhz

            cpu_after = free_cpu_mhz - requested_cpu_mhz
            memory_after = free_memory_gb - memory_gb_needed

            minimum_cpu_after = total_cpu_mhz * CPU_SAFETY_MARGIN_PERCENT / 100
            minimum_memory_after = total_memory_gb * MEMORY_SAFETY_MARGIN_PERCENT / 100

            enough_cpu = cpu_after >= minimum_cpu_after
            enough_memory = memory_after >= minimum_memory_after

            print(f"\nHost: {host.name}")
            print(f"  CPU Free        : {format_cpu_mhz(free_cpu_mhz)}")
            print(f"  CPU Required    : {format_cpu_mhz(requested_cpu_mhz)}")
            print(f"  Memory Free     : {free_memory_gb:.2f} GB")
            print(f"  Memory Required : {memory_gb_needed} GB")

            if not enough_cpu:
                print("  Result          : INSUFFICIENT CPU")
                continue
            if not enough_memory:
                print("  Result          : INSUFFICIENT MEMORY")
                continue

            candidates.append({
                "host": host,
                "free_cpu_mhz": free_cpu_mhz,
                "free_memory_gb": free_memory_gb,
                "cpu_after": cpu_after,
                "memory_after": memory_after,
            })
            print("  Result          : SUITABLE")

        except Exception as exc:
            print(f"[SKIP] {host.name}: Could not evaluate resources: {exc}")

    if not candidates:
        raise RuntimeError("No suitable ESXi host found with enough CPU and memory resources.")

    candidates.sort(
        key=lambda item: (item["free_memory_gb"], item["free_cpu_mhz"]),
        reverse=True
    )
    selected = candidates[0]
    host = selected["host"]

    print("\n" + "=" * 70)
    print("SELECTED ESXi HOST")
    print("=" * 70)
    print(f"Host             : {host.name}")
    print(f"Free CPU         : {format_cpu_mhz(selected['free_cpu_mhz'])}")
    print(f"Free Memory      : {selected['free_memory_gb']:.2f} GB")
    print("=" * 70)

    return host


# ============================================================
# Datastore Accessibility
# ============================================================

def datastore_is_accessible_from_host(datastore, host):
    try:
        host_datastores = list(host.datastore)
        for host_datastore in host_datastores:
            if host_datastore._moId == datastore._moId:
                return True
        return False
    except Exception:
        return False

def datastore_is_healthy(datastore):
    try:
        summary = datastore.summary
        if not summary.accessible:
            return False
        if summary.capacity <= 0:
            return False
        if summary.freeSpace < 0:
            return False
        maintenance_mode = getattr(summary, "maintenanceMode", "normal")
        if maintenance_mode not in (None, "normal"):
            return False
        return True
    except Exception:
        return False


# ============================================================
# Best Datastore
# ============================================================

def get_best_datastore(content, host, requested_disk_size_gb):
    datastores = discover_datastores(content)
    candidates = []

    print("\n" + "=" * 70)
    print("DATASTORE EVALUATION")
    print("=" * 70)
    print(f"Selected Host       : {host.name}")
    print(f"Requested Disk Size : {requested_disk_size_gb} GB")

    required_free_gb = requested_disk_size_gb + DATASTORE_OVERHEAD_GB
    print(f"Minimum Free Space  : {required_free_gb:.2f} GB\n")

    for datastore in datastores:
        try:
            summary = datastore.summary
            free_gb = format_gb(summary.freeSpace)
            capacity_gb = format_gb(summary.capacity)

            print(f"Datastore: {datastore.name}")
            print(f"  Capacity       : {capacity_gb:.2f} GB")
            print(f"  Free Space     : {free_gb:.2f} GB")
            print(f"  vCenter Access : {summary.accessible}")

            if not summary.accessible:
                print("  Result         : SKIP - inaccessible to vCenter\n")
                continue
            if not datastore_is_healthy(datastore):
                print("  Result         : SKIP - datastore is not healthy\n")
                continue

            host_access = datastore_is_accessible_from_host(datastore, host)
            print(f"  Host Access    : {host_access}")

            if not host_access:
                print(f"  Result         : SKIP - not mounted on host {host.name}\n")
                continue
            if free_gb < required_free_gb:
                print(f"  Result         : SKIP - only {free_gb:.2f} GB free\n")
                continue

            candidates.append({"datastore": datastore, "free_gb": free_gb})
            print("  Result         : SUITABLE\n")
        except Exception as exc:
            print(f"  Result         : SKIP - evaluation error: {exc}\n")

    if not candidates:
        raise RuntimeError(f"No suitable datastore found. Host '{host.name}' does not have an accessible healthy datastore with at least {required_free_gb:.2f} GB free.")

    candidates.sort(key=lambda item: item["free_gb"], reverse=True)
    selected = candidates[0]
    datastore = selected["datastore"]

    print("=" * 70)
    print("SELECTED DATASTORE")
    print("=" * 70)
    print(f"Datastore   : {datastore.name}")
    print(f"Free Space  : {selected['free_gb']:.2f} GB")
    print(f"Host        : {host.name}")
    print("=" * 70)

    return datastore


# ============================================================
# Resource Pool
# ============================================================

def get_host_resource_pool(host):
    parent = host.parent
    if parent is None:
        raise RuntimeError(f"Host '{host.name}' has no parent compute resource.")
    resource_pool = getattr(parent, "resourcePool", None)
    if resource_pool is None:
        raise RuntimeError(f"Unable to determine resource pool for host '{host.name}'.")
    return resource_pool


# ============================================================
# Relocate Specification
# ============================================================

def build_relocate_spec(host, datastore):
    relocate = vim.vm.RelocateSpec()
    relocate.host = host
    relocate.datastore = datastore
    relocate.pool = get_host_resource_pool(host)
    return relocate


# ============================================================
# Windows Customization
# ============================================================

def build_windows_customization_spec(
    vm_name, ip_address, subnet_mask, gateway, dns_server, local_admin_password
):
    adapter_mapping = vim.vm.customization.AdapterMapping()
    ip_settings = vim.vm.customization.IPSettings()
    
    fixed_ip = vim.vm.customization.FixedIp()
    fixed_ip.ipAddress = str(ip_address)
    ip_settings.ip = fixed_ip
    ip_settings.subnetMask = str(subnet_mask)
    ip_settings.gateway = [str(gateway)]
    adapter_mapping.adapter = ip_settings

    global_ip_settings = vim.vm.customization.GlobalIPSettings()
    global_ip_settings.dnsServerList = [str(dns_server)]

    sysprep = vim.vm.customization.Sysprep()
    
    gui_unattended = vim.vm.customization.GuiUnattended()
    gui_unattended.autoLogon = False
    gui_unattended.autoLogonCount = 0

    admin_password = vim.vm.customization.Password()
    admin_password.value = local_admin_password
    admin_password.plainText = True
    gui_unattended.password = admin_password
    sysprep.guiUnattended = gui_unattended

    user_data = vim.vm.customization.UserData()
    if len(vm_name) > 15:
        raise ValueError(f"VM name '{vm_name}' is {len(vm_name)} characters long. Windows computer names should not exceed 15 characters.")
    
    user_data.computerName = vim.vm.customization.FixedName()
    user_data.computerName.name = vm_name
    user_data.fullName = "VM Administrator"
    user_data.orgName = "VMware"
    sysprep.userData = user_data

    identification = vim.vm.customization.Identification()
    identification.joinWorkgroup = "WORKGROUP"
    sysprep.identification = identification

    customization_spec = vim.vm.customization.Specification()
    customization_spec.nicSettingMap = [adapter_mapping]
    customization_spec.globalIPSettings = global_ip_settings
    customization_spec.identity = sysprep

    return customization_spec


# ============================================================
# VM NIC Configuration
# ============================================================

def build_network_device_changes(template, network):
    device_changes = []
    for device in template.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualEthernetCard):
            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            
            backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
            backing.network = network
            backing.deviceName = network.name
            device.backing = backing

            if device.connectable is None:
                device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            device.connectable.startConnected = True
            device.connectable.connected = True
            device.connectable.allowGuestControl = True

            nic_spec.device = device
            device_changes.append(nic_spec)

    if not device_changes:
        raise RuntimeError("The selected template does not contain a virtual Ethernet adapter.")
    return device_changes


# ============================================================
# Disk Helpers
# ============================================================

def get_first_virtual_disk(vm):
    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualDisk):
            return device
    return None

def get_template_disk_size_gb(template):
    disk = get_first_virtual_disk(template)
    if disk is None:
        raise RuntimeError(f"Template '{template.name}' has no virtual disk.")
    return disk.capacityInKB / 1024 / 1024


# ============================================================
# Disk Expansion
# ============================================================

def expand_disk_if_required(vm, requested_disk_size_gb):
    disk = get_first_virtual_disk(vm)
    if disk is None:
        raise RuntimeError(f"VM '{vm.name}' has no virtual disk.")

    current_disk_gb = disk.capacityInKB / 1024 / 1024
    print(f"\nDisk Size       : {current_disk_gb:.2f} GB")
    print(f"Requested Size  : {requested_disk_size_gb} GB")

    if requested_disk_size_gb <= current_disk_gb:
        print("Disk Expansion  : Not required")
        return False

    print(f"Disk Expansion  : {current_disk_gb:.2f} -> {requested_disk_size_gb:.2f} GB")
    new_capacity_kb = int(requested_disk_size_gb * 1024 * 1024)

    disk_spec = vim.vm.ConfigSpec()
    disk_change = vim.vm.device.VirtualDeviceSpec()
    disk_change.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
    disk.capacityInKB = new_capacity_kb
    disk_change.device = disk
    disk_spec.deviceChange = [disk_change]

    task = vm.ReconfigVM_Task(spec=disk_spec)
    wait_for_task(task, f"Disk expansion for {vm.name}")
    print("[OK] Disk expansion completed.")
    return True


# ============================================================
# IP Validation
# ============================================================

def validate_ip_range(starting_ip, subnet_mask, vm_count):
    network = ipaddress.IPv4Network(f"{starting_ip}/{subnet_mask}", strict=False)
    usable_hosts = list(network.hosts())
    required_ips = []
    current_ip = starting_ip

    for _ in range(vm_count):
        if current_ip not in network:
            raise ValueError(f"IP {current_ip} is outside subnet {network}.")
        if current_ip not in usable_hosts:
            raise ValueError(f"IP {current_ip} is not a usable host address in {network}.")
        required_ips.append(current_ip)
        current_ip = ipaddress.IPv4Address(int(current_ip) + 1)

    return required_ips


# ============================================================
# VM Name Generation
# ============================================================

def generate_vm_name(naming_context, ip_address):
    octets = str(ip_address).split(".")
    if len(octets) != 4:
        raise ValueError(f"Invalid IPv4 address: {ip_address}")

    # Zero-pad the 3rd and 4th octets to 3 digits (e.g., 67 -> 067)
    third_octet = octets[2].zfill(3)
    fourth_octet = octets[3].zfill(3)
    
    vm_name = naming_context.upper() + third_octet + fourth_octet

    if len(vm_name) > 15:
        raise ValueError(
            f"Generated VM name '{vm_name}' is {len(vm_name)} characters. "
            "Windows computer names should not exceed 15 characters."
        )
    
    return vm_name


# ============================================================
# Existing VM Check
# ============================================================

def vm_exists(content, vm_name):
    vm = get_obj(content, [vim.VirtualMachine], vm_name)
    return vm is not None


# ============================================================
# Clone VM
# ============================================================

def clone_vm(
    content, template, vm_name, ip_address, subnet_mask, gateway, dns_server,
    local_admin_password, host, datastore, network, cpu_count, memory_gb, disk_size_gb,
    vm_owner="", is_esxi=False
):
    print("\n" + "=" * 70)
    print(f"DEPLOYING VM: {vm_name}")
    print("=" * 70)
    print(f"VM Name       : {vm_name}")
    print(f"IP Address    : {ip_address}")
    print(f"Host          : {host.name}")
    print(f"Datastore     : {datastore.name}")
    print(f"Network       : {network.name}")
    print(f"CPU           : {cpu_count}")
    print(f"Memory        : {memory_gb} GB")
    print(f"Disk          : {disk_size_gb} GB")
    if vm_owner:
        print(f"VM Owner      : {vm_owner}")

    relocate_spec = build_relocate_spec(host, datastore)
    config_spec = vim.vm.ConfigSpec()
    config_spec.numCPUs = cpu_count
    config_spec.memoryMB = memory_gb * 1024
    config_spec.deviceChange = build_network_device_changes(template, network)
    
    # Add VM Owner to the vCenter VM Notes/Annotations
    if vm_owner:
        config_spec.annotation = f"VM Owner: {vm_owner}"

    # Auto-detect ESXi if not explicitly set
    if not is_esxi:
        tmpl_name = str(getattr(template, "name", "")).lower()
        guest_id = str(getattr(getattr(template, "config", None), "guestId", "")).lower()
        if "esxi" in tmpl_name or "vmkernel" in guest_id or "esx" in guest_id:
            is_esxi = True

    clone_spec = vim.vm.CloneSpec()
    clone_spec.location = relocate_spec
    clone_spec.powerOn = False
    clone_spec.template = False

    # IF ESXi: Inject vApp and guestinfo properties for nested ESXi...
    if is_esxi:
        print("[ESXi Mode] Injecting vApp and guestinfo properties for nested ESXi...")
        
        # 1. Standard extraConfig (fallback)
        extra_config = [
            vim.option.OptionValue(key="guestinfo.ipaddress", value=str(ip_address)),
            vim.option.OptionValue(key="guestinfo.netmask", value=str(subnet_mask)),
            vim.option.OptionValue(key="guestinfo.gateway", value=str(gateway) if gateway else ""),
            vim.option.OptionValue(key="guestinfo.dns", value=str(dns_server) if dns_server else ""),
            vim.option.OptionValue(key="guestinfo.password", value=str(local_admin_password)),
            vim.option.OptionValue(key="guestinfo.hostname", value=str(vm_name))
        ]
        config_spec.extraConfig = extra_config
        
        # 2. vAppConfig properties (Required for standard OVA/OVF deployed ESXi appliances)
        vapp_spec = vim.vApp.VmConfigSpec()
        vapp_properties = [
            vim.vApp.PropertySpec(operation='add', info=vim.vApp.PropertyInfo(id='guestinfo.interface.0.ip.0.address', value=str(ip_address))),
            vim.vApp.PropertySpec(operation='add', info=vim.vApp.PropertyInfo(id='guestinfo.interface.0.ip.0.netmask', value=str(subnet_mask))),
            vim.vApp.PropertySpec(operation='add', info=vim.vApp.PropertyInfo(id='guestinfo.interface.0.route.0.gateway', value=str(gateway) if gateway else "")),
            vim.vApp.PropertySpec(operation='add', info=vim.vApp.PropertyInfo(id='guestinfo.dns.servers', value=str(dns_server) if dns_server else ""))
        ]
        vapp_spec.property = vapp_properties
        config_spec.vAppConfig = vapp_spec
        
        clone_spec.config = config_spec
        # Do NOT attach customization spec for ESXi
    else:
        # Standard Windows/Linux behavior
        customization_spec = build_windows_customization_spec(
            vm_name=vm_name, ip_address=ip_address, subnet_mask=subnet_mask,
            gateway=gateway, dns_server=dns_server, local_admin_password=local_admin_password
        )
        clone_spec.config = config_spec
        clone_spec.customization = customization_spec

    print("\n[1/3] Starting VM clone...")
    try:
        task = template.Clone(
            folder=template.parent,
            name=vm_name,
            spec=clone_spec
        )
        vm = wait_for_task(task, f"Clone {vm_name}")
    except Exception as exc:
        raise RuntimeError(f"Clone failed for VM '{vm_name}': {exc}") from exc

    print(f"[OK] VM '{vm_name}' cloned successfully.")
    print("\n[2/3] Checking disk size...")
    
    try:
        expand_disk_if_required(vm, disk_size_gb)
    except Exception as exc:
        raise RuntimeError(f"Disk expansion failed for VM '{vm_name}': {exc}") from exc

    print("\n[3/3] Powering on VM...")
    try:
        power_task = vm.PowerOnVM_Task()
        wait_for_task(power_task, f"Power on {vm_name}")
    except Exception as exc:
        raise RuntimeError(f"Power-on failed for VM '{vm_name}': {exc}") from exc

    print("\n" + "=" * 70)
    print(f"[SUCCESS] {vm_name} -> {ip_address}")
    print("=" * 70)

    return vm


# ============================================================
# Deploy Multiple VMs
# ============================================================

def deploy_multiple_vms(
    content, template, network, host, datastore, cpu_count, memory_gb, disk_size_gb,
    vm_count, naming_context, starting_ip, subnet_mask, gateway, dns_server, local_admin_password,
    vm_owner="", is_esxi=False
):
    ip_addresses = validate_ip_range(starting_ip, subnet_mask, vm_count)
    deployment_plan = []

    for ip_address in ip_addresses:
        vm_name = generate_vm_name(naming_context, ip_address)
        deployment_plan.append({"name": vm_name, "ip": ip_address})

    for item in deployment_plan:
        if vm_exists(content, item["name"]):
            raise RuntimeError(f"VM '{item['name']}' already exists. Deployment stopped before creating any VMs.")

    print("\n" + "=" * 70)
    print("DEPLOYMENT PLAN")
    print("=" * 70)
    print(f"Template    : {template.name}")
    print(f"Host        : {host.name}")
    print(f"Datastore   : {datastore.name}")
    print(f"Network     : {network.name}\n")

    for number, item in enumerate(deployment_plan, start=1):
        print(f"{number:3}. {item['name']} -> {item['ip']}")
    print("=" * 70)

    successful = []
    failed = []

    for index, item in enumerate(deployment_plan, start=1):
        vm_name = item["name"]
        ip_address = item["ip"]

        print("\n" + "#" * 70)
        print(f"VM {index}/{vm_count}: {vm_name}")
        print(f"IP Address: {ip_address}")
        print("#" * 70)

        try:
            vm = clone_vm(
                content=content,
                template=template,
                vm_name=vm_name,
                ip_address=ip_address,
                subnet_mask=subnet_mask,
                gateway=gateway,
                dns_server=dns_server,
                local_admin_password=local_admin_password,
                host=host,
                datastore=datastore,
                network=network,
                cpu_count=cpu_count,
                memory_gb=memory_gb,
                disk_size_gb=disk_size_gb,
                vm_owner=vm_owner,
                is_esxi=is_esxi
            )
            successful.append({
                "name": vm.name,
                "ip": str(ip_address),
                "host": host.name,
                "datastore": datastore.name,
                "network": network.name
            })
        except Exception as exc:
            failed.append({"name": vm_name, "ip": str(ip_address), "error": str(exc)})
            print(f"\n[FAILED] {vm_name}: {exc}")
            continue

    print("\n" + "=" * 70)
    print("DEPLOYMENT COMPLETED")
    print("=" * 70)

    if successful:
        print("\nSuccessful VMs:")
        for item in successful:
            print(f"  {item['name']} -> {item['ip']}")

    if failed:
        print("\nFailed VMs:")
        for item in failed:
            print(f"  {item['name']} -> {item['ip']}")
            print(f"      Error: {item['error']}")

    print(f"\nSuccessful: {len(successful)}")
    print(f"Failed    : {len(failed)}")
    print("=" * 70)

    return successful, failed


# ============================================================
# Main
# ============================================================

def main():
    print("\n" + "=" * 70)
    print("VMWARE WINDOWS VM BULK DEPLOYMENT")
    print("=" * 70)
    print("\nCluster selection is NOT used.")

    # vCenter selection
    selected_vcenter = select_vcenter()
    vc_host = selected_vcenter["host"]
    username = selected_vcenter["username"]
    password = getpass.getpass("Password: ")

    if not password:
        raise ValueError("Password cannot be empty.")

    # VM configuration
    cpu_count = prompt_positive_int("CPU Count: ")
    memory_gb = prompt_positive_int("Memory (GB): ")
    disk_size_gb = prompt_positive_int("Disk Size (GB) [Default: 40]: ")
    vm_count = prompt_positive_int("Number of VMs to create: ")
    
    naming_context = input("Naming Context (Example: XCD): ").strip().upper()
    if not naming_context:
        raise ValueError("Naming Context cannot be empty.")

    vm_owner = input("VM Owner (Optional): ").strip()

    # Network settings
    starting_ip = prompt_ipv4("Starting IP Address: ")
    subnet_mask = prompt_subnet_mask("Subnet Mask (e.g. 255.255.255.0): ")
    gateway = prompt_ipv4("Gateway: ")
    dns_server = prompt_ipv4("DNS Server (e.g. 208.67.222.222): ")

    # Windows Administrator password
    local_admin_password = getpass.getpass("Local Administrator Password: ")
    if not local_admin_password:
        raise ValueError("Local Administrator Password cannot be empty.")

    # Optional datacenter
    datacenter_name = input("Datacenter Name (Optional): ").strip()

    si = None
    try:
        si = connect_vcenter(vc_host, username, password)
        content = si.RetrieveContent()

        # Discovery
        display_inventory(content)

        # Datacenter selection
        datacenters = discover_datacenters(content)
        datacenter = None
        if datacenter_name:
            datacenter = get_obj(content, [vim.Datacenter], datacenter_name)
            if datacenter is None:
                raise RuntimeError(f"Datacenter '{datacenter_name}' not found.")
            print(f"\n[OK] Datacenter selected: {datacenter.name}")
        elif len(datacenters) == 1:
            datacenter = datacenters[0]
            print(f"\n[OK] Automatically selected only datacenter: {datacenter.name}")
        else:
            print("\nMultiple datacenters detected.")
            datacenter = choose_from_list(datacenters, "Datacenters")
            print(f"[OK] Selected datacenter: {datacenter.name}")

        # Template selection
        templates = discover_templates(content)
        if not templates:
            raise RuntimeError("No VMware templates were found.")
        template = choose_from_list(templates, "Templates")
        if not template.config.template:
            raise RuntimeError(f"Selected object '{template.name}' is not a template.")
        print(f"\n[OK] Selected Template: {template.name}")

        # Network selection
        networks = discover_networks(content)
        if not networks:
            raise RuntimeError("No networks / port groups were found.")
        network = choose_from_list(networks, "Networks / Port Groups")
        print(f"\n[OK] Selected Network: {network.name}")

        # Validate IP range
        print("\nValidating requested IP range...")
        ip_addresses = validate_ip_range(starting_ip, subnet_mask, vm_count)
        print(f"[OK] {len(ip_addresses)} IP addresses are available in the requested subnet.")

        for ip_address in ip_addresses:
            vm_name = generate_vm_name(naming_context, ip_address)
            print(f"  {ip_address} -> {vm_name}")

        # Select best ESXi host
        host = get_best_host(content, cpu_count, memory_gb)

        # Select best datastore
        datastore = get_best_datastore(content, host, disk_size_gb)

        # Template disk
        template_disk_gb = get_template_disk_size_gb(template)

        # Final configuration
        print("\n" + "=" * 70)
        print("FINAL DEPLOYMENT CONFIGURATION")
        print("=" * 70)
        print(f"vCenter             : {selected_vcenter['name']}")
        print(f"Datacenter          : {datacenter.name if datacenter else 'Automatic'}")
        print(f"Template            : {template.name}")
        print(f"Template Disk       : {template_disk_gb:.2f} GB")
        print(f"Requested Disk      : {disk_size_gb} GB")
        print(f"ESXi Host           : {host.name}")
        print(f"Datastore           : {datastore.name}")
        print(f"Network             : {network.name}")
        print(f"CPU                 : {cpu_count}")
        print(f"Memory              : {memory_gb} GB")
        print(f"VM Count            : {vm_count}")
        print(f"Naming Context      : {naming_context}")
        print(f"VM Owner            : {vm_owner}")
        print(f"Starting IP         : {starting_ip}")
        print(f"Subnet Mask         : {subnet_mask}")
        print(f"Gateway             : {gateway}")
        print(f"DNS Server          : {dns_server}")
        print("Cluster Selection   : NOT USED")
        print("=" * 70)

        # Confirmation
        confirmation = input("\nStart deployment? [y/N]: ").strip().lower()
        if confirmation not in ("y", "yes"):
            print("\nDeployment cancelled.")
            return

        # Deploy VMs
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
            local_admin_password=local_admin_password,
            vm_owner=vm_owner
        )

    except vim.fault.InvalidLogin as exc:
        print_exception("AUTHENTICATION ERROR", exc)
        sys.exit(1)
    except vim.fault.NoPermission as exc:
        print_exception("VMWARE PERMISSION ERROR", exc)
        sys.exit(1)
    except vim.fault.NotFound as exc:
        print_exception("VMWARE OBJECT NOT FOUND", exc)
        sys.exit(1)
    except vim.fault.CustomizationFault as exc:
        print_exception("WINDOWS CUSTOMIZATION ERROR", exc)
        sys.exit(1)
    except vim.fault.VimFault as exc:
        print_exception("VMWARE FAULT", exc)
        sys.exit(1)
    except ValueError as exc:
        print_exception("INPUT / VALIDATION ERROR", exc)
        sys.exit(1)
    except RuntimeError as exc:
        print_exception("DEPLOYMENT ERROR", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nDeployment interrupted by user.")
        sys.exit(130)
    except Exception as exc:
        print_exception("UNEXPECTED ERROR", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()