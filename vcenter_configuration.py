import json
import os
import tkinter as tk
from tkinter import ttk, messagebox


CONFIG_FILE = "vcenters.json"


class VCenterConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VMware Deployment Tool - vCenter Configuration")
        self.root.geometry("700x450")
        self.root.resizable(False, False)

        self.vcenters = []

        self.load_vcenters()
        self.create_ui()
        self.refresh_list()

    # ========================================================
    # JSON STORAGE
    # ========================================================

    def load_vcenters(self):
        """Load configured vCenters from JSON."""

        if not os.path.exists(CONFIG_FILE):
            self.vcenters = []
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, list):
                self.vcenters = data
            else:
                self.vcenters = []

        except (json.JSONDecodeError, OSError):
            self.vcenters = []

    def save_vcenters(self):
        """Save configured vCenters to JSON."""

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                json.dump(
                    self.vcenters,
                    file,
                    indent=4
                )

        except OSError as exc:
            messagebox.showerror(
                "Save Error",
                f"Unable to save vCenter configuration:\n\n{exc}"
            )

    # ========================================================
    # UI
    # ========================================================

    def create_ui(self):

        title = ttk.Label(
            self.root,
            text="vCenter Configuration",
            font=("Arial", 18, "bold")
        )

        title.pack(pady=(20, 5))

        subtitle = ttk.Label(
            self.root,
            text="Configure vCenters used by the deployment tool."
        )

        subtitle.pack(pady=(0, 20))

        # ----------------------------------------------------
        # Table
        # ----------------------------------------------------

        table_frame = ttk.Frame(self.root)
        table_frame.pack(
            fill="both",
            expand=True,
            padx=30
        )

        columns = (
            "vcenter",
            "username"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=10
        )

        self.tree.heading(
            "vcenter",
            text="vCenter IP / FQDN"
        )

        self.tree.heading(
            "username",
            text="Username"
        )

        self.tree.column(
            "vcenter",
            width=300
        )

        self.tree.column(
            "username",
            width=250
        )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # ----------------------------------------------------
        # Buttons
        # ----------------------------------------------------

        button_frame = ttk.Frame(
            self.root
        )

        button_frame.pack(
            pady=20
        )

        add_button = ttk.Button(
            button_frame,
            text="Add vCenter",
            command=self.add_vcenter
        )

        add_button.grid(
            row=0,
            column=0,
            padx=10
        )

        remove_button = ttk.Button(
            button_frame,
            text="Remove vCenter",
            command=self.remove_vcenter
        )

        remove_button.grid(
            row=0,
            column=1,
            padx=10
        )

        close_button = ttk.Button(
            button_frame,
            text="Close",
            command=self.root.destroy
        )

        close_button.grid(
            row=0,
            column=2,
            padx=10
        )

    # ========================================================
    # LIST
    # ========================================================

    def refresh_list(self):
        """Refresh the vCenter table."""

        for item in self.tree.get_children():
            self.tree.delete(item)

        for vcenter in self.vcenters:

            self.tree.insert(
                "",
                "end",
                values=(
                    vcenter.get("host", ""),
                    vcenter.get("username", "")
                )
            )

    # ========================================================
    # ADD VCENTER
    # ========================================================

    def add_vcenter(self):

        window = tk.Toplevel(
            self.root
        )

        window.title("Add vCenter")
        window.geometry("450x250")
        window.resizable(False, False)

        window.transient(self.root)
        window.grab_set()

        # ----------------------------------------------------
        # vCenter
        # ----------------------------------------------------

        ttk.Label(
            window,
            text="vCenter IP / FQDN:"
        ).pack(
            anchor="w",
            padx=30,
            pady=(25, 5)
        )

        host_entry = ttk.Entry(
            window,
            width=45
        )

        host_entry.pack(
            padx=30
        )

        # ----------------------------------------------------
        # Username
        # ----------------------------------------------------

        ttk.Label(
            window,
            text="Username:"
        ).pack(
            anchor="w",
            padx=30,
            pady=(15, 5)
        )

        username_entry = ttk.Entry(
            window,
            width=45
        )

        username_entry.pack(
            padx=30
        )

        # ----------------------------------------------------
        # Buttons
        # ----------------------------------------------------

        button_frame = ttk.Frame(
            window
        )

        button_frame.pack(
            pady=25
        )

        def save():

            host = host_entry.get().strip()
            username = username_entry.get().strip()

            if not host:

                messagebox.showwarning(
                    "Missing vCenter",
                    "Please enter the vCenter IP/FQDN.",
                    parent=window
                )

                return

            if not username:

                messagebox.showwarning(
                    "Missing Username",
                    "Please enter the vCenter username.",
                    parent=window
                )

                return

            # Prevent duplicate vCenters.
            for existing in self.vcenters:

                if existing.get("host", "").lower() == host.lower():

                    messagebox.showwarning(
                        "Already Exists",
                        "This vCenter is already configured.",
                        parent=window
                    )

                    return

            self.vcenters.append(
                {
                    "host": host,
                    "username": username
                }
            )

            self.save_vcenters()
            self.refresh_list()

            window.destroy()

        ttk.Button(
            button_frame,
            text="Save",
            command=save
        ).grid(
            row=0,
            column=0,
            padx=10
        )

        ttk.Button(
            button_frame,
            text="Cancel",
            command=window.destroy
        ).grid(
            row=0,
            column=1,
            padx=10
        )

        host_entry.focus()

    # ========================================================
    # REMOVE VCENTER
    # ========================================================

    def remove_vcenter(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showwarning(
                "No Selection",
                "Please select a vCenter to remove."
            )

            return

        item = selected[0]

        values = self.tree.item(
            item,
            "values"
        )

        host = values[0]

        confirm = messagebox.askyesno(
            "Remove vCenter",
            f"Remove '{host}' from the configured vCenters?"
        )

        if not confirm:
            return

        self.vcenters = [
            vcenter
            for vcenter in self.vcenters
            if vcenter.get("host") != host
        ]

        self.save_vcenters()
        self.refresh_list()


# ============================================================
# MAIN
# ============================================================

def main():

    root = tk.Tk()

    app = VCenterConfigApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()
