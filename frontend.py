import tkinter as tk
from tkinter import ttk, messagebox


class VMwareDeploymentGUI:
    def __init__(self, root):
        self.root = root

        self.root.title("VMware Windows VM Deployment")
        self.root.geometry("1100x800")
        self.root.minsize(950, 700)

        self.configure_style()
        self.build_ui()

    # ==========================================================
    # Styling
    # ==========================================================

    def configure_style(self):

        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 20, "bold")
        )

        style.configure(
            "Section.TLabel",
            font=("Segoe UI", 12, "bold")
        )

        style.configure(
            "TLabel",
            font=("Segoe UI", 10)
        )

        style.configure(
            "TButton",
            font=("Segoe UI", 10),
            padding=7
        )

        style.configure(
            "Deploy.TButton",
            font=("Segoe UI", 11, "bold"),
            padding=10
        )

    # ==========================================================
    # Main UI
    # ==========================================================

    def build_ui(self):

        # ------------------------------------------------------
        # Header
        # ------------------------------------------------------

        header = ttk.Frame(self.root, padding=(20, 15))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="VMware Windows VM Deployment",
            style="Title.TLabel"
        ).pack(side="left")

        ttk.Label(
            header,
            text="vCenter / PyVmomi",
            foreground="#666666"
        ).pack(side="right")

        # ------------------------------------------------------
        # Main container
        # ------------------------------------------------------

        main = ttk.Frame(self.root, padding=(20, 5))
        main.pack(fill="both", expand=True)

        # Left side = configuration
        # Right side = deployment information

        left = ttk.Frame(main)
        left.pack(
            side="left",
            fill="y",
            padx=(0, 10)
        )

        right = ttk.Frame(main)
        right.pack(
            side="right",
            fill="both",
            expand=True
        )

        self.build_connection_section(left)
        self.build_vm_section(left)
        self.build_network_section(left)
        self.build_template_section(left)

        self.build_deployment_section(right)
        self.build_log_section(right)

    # ==========================================================
    # Connection Section
    # ==========================================================

    def build_connection_section(self, parent):

        frame = ttk.LabelFrame(
            parent,
            text="vCenter Connection",
            padding=12
        )

        frame.pack(
            fill="x",
            pady=(0, 10)
        )

        # vCenter
        ttk.Label(
            frame,
            text="vCenter IP / FQDN:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=4
        )

        self.vcenter_entry = ttk.Entry(
            frame,
            width=32
        )

        self.vcenter_entry.grid(
            row=0,
            column=1,
            pady=4
        )

        # Username
        ttk.Label(
            frame,
            text="Username:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=4
        )

        self.username_entry = ttk.Entry(
            frame,
            width=32
        )

        self.username_entry.grid(
            row=1,
            column=1,
            pady=4
        )

        # Password
        ttk.Label(
            frame,
            text="Password:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=4
        )

        self.password_entry = ttk.Entry(
            frame,
            width=32,
            show="*"
        )

        self.password_entry.grid(
            row=2,
            column=1,
            pady=4
        )

        # Connect button
        self.connect_button = ttk.Button(
            frame,
            text="Connect & Discover",
            command=self.connect_vcenter
        )

        self.connect_button.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(10, 0)
        )

    # ==========================================================
    # VM Configuration
    # ==========================================================

    def build_vm_section(self, parent):

        frame = ttk.LabelFrame(
            parent,
            text="VM Configuration",
            padding=12
        )

        frame.pack(
            fill="x",
            pady=(0, 10)
        )

        # CPU
        ttk.Label(
            frame,
            text="CPU Count:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=4
        )

        self.cpu_entry = ttk.Entry(
            frame,
            width=15
        )

        self.cpu_entry.insert(0, "4")

        self.cpu_entry.grid(
            row=0,
            column=1,
            pady=4
        )

        # Memory
        ttk.Label(
            frame,
            text="Memory (GB):"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=4
        )

        self.memory_entry = ttk.Entry(
            frame,
            width=15
        )

        self.memory_entry.insert(0, "16")

        self.memory_entry.grid(
            row=1,
            column=1,
            pady=4
        )

        # Disk
        ttk.Label(
            frame,
            text="Disk Size (GB):"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=4
        )

        self.disk_entry = ttk.Entry(
            frame,
            width=15
        )

        self.disk_entry.insert(0, "100")

        self.disk_entry.grid(
            row=2,
            column=1,
            pady=4
        )

        # VM Count
        ttk.Label(
            frame,
            text="Number of VMs:"
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=4
        )

        self.vm_count_entry = ttk.Entry(
            frame,
            width=15
        )

        self.vm_count_entry.insert(0, "3")

        self.vm_count_entry.grid(
            row=3,
            column=1,
            pady=4
        )

        # Naming context
        ttk.Label(
            frame,
            text="Naming Context:"
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=4
        )

        self.naming_entry = ttk.Entry(
            frame,
            width=15
        )

        self.naming_entry.insert(0, "HDS")

        self.naming_entry.grid(
            row=4,
            column=1,
            pady=4
        )

    # ==========================================================
    # Network Configuration
    # ==========================================================

    def build_network_section(self, parent):

        frame = ttk.LabelFrame(
            parent,
            text="Network Configuration",
            padding=12
        )

        frame.pack(
            fill="x",
            pady=(0, 10)
        )

        fields = [
            ("Starting IP:", "192.168.231.100"),
            ("Subnet Mask:", "255.255.255.0"),
            ("Gateway:", "192.168.231.1"),
            ("DNS Server:", "192.168.231.10"),
        ]

        self.network_entries = {}

        for row, (label, default) in enumerate(fields):

            ttk.Label(
                frame,
                text=label
            ).grid(
                row=row,
                column=0,
                sticky="w",
                pady=4
            )

            entry = ttk.Entry(
                frame,
                width=20
            )

            entry.insert(0, default)

            entry.grid(
                row=row,
                column=1,
                pady=4
            )

            self.network_entries[label] = entry

        # Local Administrator Password
        ttk.Label(
            frame,
            text="Local Admin Password:"
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=4
        )

        self.admin_password_entry = ttk.Entry(
            frame,
            width=20,
            show="*"
        )

        self.admin_password_entry.grid(
            row=4,
            column=1,
            pady=4
        )

    # ==========================================================
    # Template / Datacenter
    # ==========================================================

    def build_template_section(self, parent):

        frame = ttk.LabelFrame(
            parent,
            text="VMware Selection",
            padding=12
        )

        frame.pack(
            fill="x",
            pady=(0, 10)
        )

        # Datacenter
        ttk.Label(
            frame,
            text="Datacenter:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=4
        )

        self.datacenter_combo = ttk.Combobox(
            frame,
            width=27,
            state="readonly"
        )

        self.datacenter_combo["values"] = [
            "Datacenter-01",
            "Datacenter-02"
        ]

        self.datacenter_combo.current(0)

        self.datacenter_combo.grid(
            row=0,
            column=1,
            pady=4
        )

        # Template
        ttk.Label(
            frame,
            text="Template:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=4
        )

        self.template_combo = ttk.Combobox(
            frame,
            width=27,
            state="readonly"
        )

        self.template_combo["values"] = [
            "WIN2022-TEMPLATE",
            "WIN2019-TEMPLATE",
            "WIN2025-TEMPLATE"
        ]

        self.template_combo.current(0)

        self.template_combo.grid(
            row=1,
            column=1,
            pady=4
        )

        # Network
        ttk.Label(
            frame,
            text="Network / Port Group:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=4
        )

        self.network_combo = ttk.Combobox(
            frame,
            width=27,
            state="readonly"
        )

        self.network_combo["values"] = [
            "VM Network",
            "Production",
            "Server VLAN 231",
            "DMZ"
        ]

        self.network_combo.current(0)

        self.network_combo.grid(
            row=2,
            column=1,
            pady=4
        )

    # ==========================================================
    # Deployment Section
    # ==========================================================

    def build_deployment_section(self, parent):

        frame = ttk.LabelFrame(
            parent,
            text="Deployment",
            padding=12
        )

        frame.pack(
            fill="x",
            pady=(0, 10)
        )

        # Selected Host
        ttk.Label(
            frame,
            text="Selected ESXi Host:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.host_value = ttk.Label(
            frame,
            text="Automatic",
            foreground="#0066cc"
        )

        self.host_value.grid(
            row=0,
            column=1,
            sticky="w",
            pady=5
        )

        # Selected datastore
        ttk.Label(
            frame,
            text="Selected Datastore:"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.datastore_value = ttk.Label(
            frame,
            text="Automatic",
            foreground="#0066cc"
        )

        self.datastore_value.grid(
            row=1,
            column=1,
            sticky="w",
            pady=5
        )

        # Status
        ttk.Label(
            frame,
            text="Status:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.status_value = ttk.Label(
            frame,
            text="Ready",
            foreground="green"
        )

        self.status_value.grid(
            row=2,
            column=1,
            sticky="w",
            pady=5
        )

        # Progress
        self.progress = ttk.Progressbar(
            frame,
            orient="horizontal",
            mode="determinate",
            maximum=100
        )

        self.progress.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=10
        )

        # Progress percentage
        self.progress_label = ttk.Label(
            frame,
            text="0%"
        )

        self.progress_label.grid(
            row=4,
            column=0,
            columnspan=2
        )

        # Deploy button
        self.deploy_button = ttk.Button(
            frame,
            text="DEPLOY VMs",
            style="Deploy.TButton",
            command=self.deploy_vms
        )

        self.deploy_button.grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(15, 5)
        )

        frame.columnconfigure(
            1,
            weight=1
        )

    # ==========================================================
    # Log Section
    # ==========================================================

    def build_log_section(self, parent):

        frame = ttk.LabelFrame(
            parent,
            text="Deployment Progress / Log",
            padding=10
        )

        frame.pack(
            fill="both",
            expand=True
        )

        # ------------------------------------------------------
        # Treeview
        # ------------------------------------------------------

        columns = (
            "vm",
            "ip",
            "host",
            "datastore",
            "network",
            "progress",
            "status"
        )

        self.deployment_tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=10
        )

        headings = {
            "vm": "VM Name",
            "ip": "IP Address",
            "host": "Host",
            "datastore": "Datastore",
            "network": "Network",
            "progress": "Clone %",
            "status": "Status"
        }

        widths = {
            "vm": 130,
            "ip": 115,
            "host": 120,
            "datastore": 130,
            "network": 130,
            "progress": 70,
            "status": 100
        }

        for column in columns:

            self.deployment_tree.heading(
                column,
                text=headings[column]
            )

            self.deployment_tree.column(
                column,
                width=widths[column],
                anchor="center"
            )

        self.deployment_tree.pack(
            fill="x",
            pady=(0, 10)
        )

        # ------------------------------------------------------
        # Log output
        # ------------------------------------------------------

        self.log_text = tk.Text(
            frame,
            height=15,
            bg="#111827",
            fg="#d1fae5",
            insertbackground="white",
            font=("Consolas", 9),
            relief="flat"
        )

        self.log_text.pack(
            fill="both",
            expand=True
        )

        self.log(
            "VMware deployment interface initialized."
        )

        self.log(
            "Connect to vCenter to discover inventory."
        )

    # ==========================================================
    # Logging
    # ==========================================================

    def log(self, message):

        self.log_text.insert(
            "end",
            message + "\n"
        )

        self.log_text.see("end")

        self.root.update_idletasks()

    # ==========================================================
    # Connect
    # ==========================================================

    def connect_vcenter(self):

        host = self.vcenter_entry.get().strip()
        username = self.username_entry.get().strip()

        if not host:
            messagebox.showerror(
                "Error",
                "Enter vCenter IP/FQDN."
            )
            return

        if not username:
            messagebox.showerror(
                "Error",
                "Enter username."
            )
            return

        self.status_value.config(
            text="Connecting...",
            foreground="#cc8800"
        )

        self.log(
            f"Connecting to vCenter: {host}"
        )

        # ------------------------------------------------------
        # DEMO ONLY
        #
        # Replace this section with:
        #
        # si = connect_vcenter(
        #     host,
        #     username,
        #     password
        # )
        #
        # Then populate the Combobox values from:
        #
        # discover_datacenters()
        # discover_templates()
        # discover_networks()
        #
        # ------------------------------------------------------

        self.host_value.config(
            text="esxi-01.example.local"
        )

        self.datastore_value.config(
            text="Datastore-Production"
        )

        self.status_value.config(
            text="Connected",
            foreground="green"
        )

        self.log(
            "[OK] Connected to vCenter."
        )

        self.log(
            "[OK] Inventory discovered."
        )

        self.log(
            "Templates loaded."
        )

        self.log(
            "Networks loaded."
        )

    # ==========================================================
    # Deployment
    # ==========================================================

    def deploy_vms(self):

        try:

            vm_count = int(
                self.vm_count_entry.get()
            )

            if vm_count <= 0:
                raise ValueError

        except ValueError:

            messagebox.showerror(
                "Invalid VM Count",
                "Enter a valid VM count."
            )

            return

        naming = (
            self.naming_entry
            .get()
            .strip()
            .upper()
        )

        starting_ip = (
            self.network_entries["Starting IP:"]
            .get()
            .strip()
        )

        template = (
            self.template_combo
            .get()
        )

        network = (
            self.network_combo
            .get()
        )

        host = (
            self.host_value.cget("text")
        )

        datastore = (
            self.datastore_value.cget("text")
        )

        if not naming:

            messagebox.showerror(
                "Error",
                "Enter a naming context."
            )

            return

        if not template:

            messagebox.showerror(
                "Error",
                "Select a template."
            )

            return

        if not network:

            messagebox.showerror(
                "Error",
                "Select a network."
            )

            return

        # ------------------------------------------------------
        # Confirmation
        # ------------------------------------------------------

        confirm = messagebox.askyesno(
            "Confirm Deployment",
            (
                f"Deploy {vm_count} VM(s)?\n\n"
                f"Template: {template}\n"
                f"Network: {network}\n"
                f"Host: {host}\n"
                f"Datastore: {datastore}\n"
                f"Starting IP: {starting_ip}\n"
                f"Naming Context: {naming}"
            )
        )

        if not confirm:
            return

        self.deploy_button.config(
            state="disabled"
        )

        self.status_value.config(
            text="Deploying...",
            foreground="#cc8800"
        )

        self.progress["value"] = 0

        # ------------------------------------------------------
        # Demo deployment
        #
        # Replace this with:
        #
        # deploy_multiple_vms(...)
        #
        # ------------------------------------------------------

        self.deployment_tree.delete(
            *self.deployment_tree.get_children()
        )

        for index in range(vm_count):

            # Demo IP generation
            octets = starting_ip.split(".")

            if len(octets) == 4:

                try:

                    last_octet = (
                        int(octets[3]) + index
                    )

                    ip = (
                        f"{octets[0]}."
                        f"{octets[1]}."
                        f"{octets[2]}."
                        f"{last_octet}"
                    )

                except ValueError:

                    ip = "Invalid IP"

            else:

                ip = "Invalid IP"

            # Example:
            #
            # 192.168.231.100
            #       231 + 100
            #
            # HDS231100

            if len(octets) == 4:

                try:

                    vm_name = (
                        f"{naming}"
                        f"{octets[2]}"
                        f"{int(octets[3]) + index}"
                    )

                except ValueError:

                    vm_name = f"{naming}-VM-{index + 1}"

            else:

                vm_name = f"{naming}-VM-{index + 1}"

            item_id = self.deployment_tree.insert(
                "",
                "end",
                values=(
                    vm_name,
                    ip,
                    host,
                    datastore,
                    network,
                    "0%",
                    "Starting"
                )
            )

            self.log(
                f"Starting deployment: "
                f"{vm_name} -> {ip}"
            )

            # Simulate progress
            for progress in (
                10,
                25,
                50,
                75,
                100
            ):

                self.root.update_idletasks()

                self.deployment_tree.item(
                    item_id,
                    values=(
                        vm_name,
                        ip,
                        host,
                        datastore,
                        network,
                        f"{progress}%",
                        (
                            "Cloning"
                            if progress < 100
                            else "Powered On"
                        )
                    )
                )

                self.progress["value"] = (
                    (
                        index * 100
                    ) + progress
                ) / vm_count

                self.progress_label.config(
                    text=(
                        f"{int(self.progress['value'])}%"
                    )
                )

                self.root.after(100)

            self.log(
                f"[OK] {vm_name} deployed."
            )

        # ------------------------------------------------------
        # Finished
        # ------------------------------------------------------

        self.status_value.config(
            text="Deployment Completed",
            foreground="green"
        )

        self.progress["value"] = 100

        self.progress_label.config(
            text="100%"
        )

        self.deploy_button.config(
            state="normal"
        )

        self.log(
            "======================================"
        )

        self.log(
            "Deployment Completed"
        )

        self.log(
            "======================================"
        )

        messagebox.showinfo(
            "Deployment Completed",
            f"{vm_count} VM(s) deployed successfully."
        )


# ==========================================================
# Application Entry Point
# ==========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = VMwareDeploymentGUI(
        root
    )

    root.mainloop()