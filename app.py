from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
import ipaddress
import datetime
import sqlite3
import base64
import traceback
import threading
import time
import subprocess
import platform
import socket
import requests
import concurrent.futures
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from werkzeug.security import generate_password_hash, check_password_hash
from pyVmomi import vim, vmodl
import re

def ping_ip(ip):
    """Returns True if host responds to a ping request or has open ports."""
    try:
        is_win = platform.system().lower() == 'windows'
        param = '-n' if is_win else '-c'
        timeout_flag = '-w' if is_win else '-W'
        timeout_val = '800' if is_win else '1'
        command = ['ping', param, '1', timeout_flag, timeout_val, str(ip)]
        res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
        if res.returncode == 0:
            out = res.stdout.lower()
            if is_win:
                if ("ttl=" in out or "bytes=" in out) and "unreachable" not in out:
                    return True
            else:
                return True
    except Exception:
        pass

    # Quick TCP fallback for firewall-blocked ICMP
    for port in (443, 80, 22, 3389, 445):
        try:
            with socket.create_connection((str(ip), port), timeout=0.25):
                return True
        except Exception:
            pass
    return False


# ============================================================
# APPLICATION
# ============================================================
app = Flask(__name__)
CORS(app)

# Global cache dictionary for backend query acceleration
APP_CACHE = {}

def get_cached_response(cache_key, max_age_seconds, fetch_function, *args, **kwargs):
    now = time.time()
    if cache_key in APP_CACHE:
        cached_data, timestamp = APP_CACHE[cache_key]
        if now - timestamp < max_age_seconds:
            return cached_data
            
    # Fetch fresh data
    data = fetch_function(*args, **kwargs)
    APP_CACHE[cache_key] = (data, now)
    return data

# ============================================================
# PATHS & DATABASE SETUP
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "vcenters.json")
INVENTORY_DB = os.path.join(BASE_DIR, "inventory.db")

def init_db():
    try:
        conn = sqlite3.connect(INVENTORY_DB)
        cursor = conn.cursor()
        
        # 1. Inventory Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, vmName TEXT, ipAddress TEXT, vcenter TEXT, esxiHost TEXT, datastore TEXT, network TEXT, cpu INTEGER, memoryGb INTEGER, diskGb INTEGER, vmOwner TEXT, provisionedBy TEXT)''')
        cursor.execute("PRAGMA table_info(inventory)")
        if "templatename" not in [col[1].lower() for col in cursor.fetchall()]:
            cursor.execute("ALTER TABLE inventory ADD COLUMN templateName TEXT DEFAULT 'Unknown'")
            
        # 2. Roles Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
        cursor.execute("SELECT COUNT(*) FROM roles")
        if cursor.fetchone()[0] == 0:
            for r in ["Admin", "Deployer", "Viewer"]:
                cursor.execute("INSERT INTO roles (name) VALUES (?)", (r,))

        # 3. Users Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, fullName TEXT, role TEXT, createdAt TEXT, password TEXT)''')
        
        # Force-ensure the admin user exists with the correct hash & password
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hashed_pwd = generate_password_hash("admin123")
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, fullName, role, createdAt, password) VALUES (?, ?, ?, ?, ?)",
                           ("admin", "System Administrator", "Admin", now_str, hashed_pwd))
        else:
            # Force reset admin password to admin123 to guarantee login works
            cursor.execute("UPDATE users SET password = ? WHERE username = 'admin'", (hashed_pwd,))

        # 4. IPAM Subnets Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS ipam_subnets (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            vcenter TEXT, 
            name TEXT, 
            cidr TEXT, 
            gateway TEXT,
            vlan TEXT
        )''')
        cursor.execute("PRAGMA table_info(ipam_subnets)")
        if "vlan" not in [col[1].lower() for col in cursor.fetchall()]:
            cursor.execute("ALTER TABLE ipam_subnets ADD COLUMN vlan TEXT DEFAULT ''")
 
        # 5. IPAM IP Addresses Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS ipam_ips (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            subnet_id INTEGER, 
            ip_address TEXT, 
            status TEXT, 
            is_manual INTEGER DEFAULT 0, 
            reason TEXT, 
            last_scanned TEXT, 
            FOREIGN KEY(subnet_id) REFERENCES ipam_subnets(id) ON DELETE CASCADE
        )''')

        conn.commit()
        conn.close()
        print("[OK] Database Initialized & Admin Password Verified")
    except Exception as e:
        print(f"[CRITICAL ERROR] Database initialization failed: {e}")

init_db()

# ============================================================
# BULK FETCH OPTIMIZATION
# ============================================================
def get_properties(si, obj_type, properties):
    try:
        pc = si.content.propertyCollector
        container = si.content.viewManager.CreateContainerView(si.content.rootFolder, [obj_type], True)
        traversal_spec = vmodl.query.PropertyCollector.TraversalSpec(name="t", type=vim.view.ContainerView, path="view", skip=False)
        obj_spec = vmodl.query.PropertyCollector.ObjectSpec(obj=container, skip=True, selectSet=[traversal_spec])
        prop_spec = vmodl.query.PropertyCollector.PropertySpec(type=obj_type, pathSet=properties)
        filter_spec = vmodl.query.PropertyCollector.FilterSpec(objectSet=[obj_spec], propSet=[prop_spec])
        result = pc.RetrieveProperties([filter_spec])
        container.Destroy()
        parsed = []
        if result:
            for item in result:
                obj_dict = {"obj": item.obj, "id": str(getattr(item.obj, '_moId', ''))}
                if hasattr(item, 'propSet') and item.propSet:
                    for prop in item.propSet:
                        obj_dict[prop.name] = prop.val
                parsed.append(obj_dict)
        return parsed
    except Exception as e:
        return []

# ============================================================
# STORAGE HELPERS & VAULT
# ============================================================
def load_vcenters():
    if not os.path.exists(CONFIG_FILE): return []
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except Exception: return []

def save_vcenters(vcenters):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(vcenters, file, indent=4)

def normalize_host(h):
    if not h: return ""
    s = str(h).strip().lower()
    if s.startswith("https://"): s = s[8:]
    elif s.startswith("http://"): s = s[7:]
    return s.split("/")[0].split(":")[0]

def find_vcenter_record(identifier):
    if not identifier: return None
    ident_raw = str(identifier).strip().lower()
    ident_norm = normalize_host(ident_raw)
    
    vcs = load_vcenters()
    # 1. Exact match on host or name
    for vc in vcs:
        if not isinstance(vc, dict): continue
        h = str(vc.get("host", "")).strip().lower()
        n = str(vc.get("name", "")).strip().lower()
        if ident_raw in [h, n] or ident_norm in [normalize_host(h), n]:
            return vc
            
    # 2. IP / hostname resolution match
    ident_ip = None
    try:
        ident_ip = socket.gethostbyname(ident_norm)
    except Exception:
        ident_ip = None

    for vc in vcs:
        if not isinstance(vc, dict): continue
        vc_host_norm = normalize_host(vc.get("host", ""))
        if ident_ip and vc_host_norm == ident_ip:
            return vc
        try:
            vc_ip = socket.gethostbyname(vc_host_norm)
            if (ident_norm == vc_ip) or (ident_ip and ident_ip == vc_ip):
                return vc
        except Exception:
            pass
            
    # 3. Substring match fallback
    for vc in vcs:
        if not isinstance(vc, dict): continue
        h = str(vc.get("host", "")).strip().lower()
        n = str(vc.get("name", "")).strip().lower()
        if ident_raw and (ident_raw in n or n in ident_raw):
            return vc

    return None

def get_vaulted_password(host):
    vc = find_vcenter_record(host)
    if vc and vc.get("password"):
        try: return base64.b64decode(vc["password"]).decode("utf-8")
        except Exception: return ""
    for vc in load_vcenters():
        if not isinstance(vc, dict): continue
        if str(vc.get("host", "")).lower() == str(host).lower() and vc.get("password"):
            try: return base64.b64decode(vc["password"]).decode("utf-8")
            except Exception: return ""
    return ""

def get_inventory_from_db():
    conn = sqlite3.connect(INVENTORY_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    
    formatted = []
    for row in rows:
        r = dict(row)
        def get_val(key, default=""):
            for k, v in r.items():
                if k.lower() == key.lower(): return v
            return default
        formatted.append({
            "id": get_val("id"), "timestamp": get_val("timestamp"), "vmName": get_val("vmname"),
            "ipAddress": get_val("ipaddress"), "vcenter": get_val("vcenter"), "esxiHost": get_val("esxihost"),
            "datastore": get_val("datastore"), "network": get_val("network"), "cpu": get_val("cpu"),
            "memoryGb": get_val("memorygb"), "diskGb": get_val("diskgb"), "vmOwner": get_val("vmowner"),
            "provisionedBy": get_val("provisionedby"), "templateName": get_val("templatename", "Unknown")
        })
    return formatted

def log_deployment_to_db(record):
    conn = sqlite3.connect(INVENTORY_DB)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO inventory (timestamp, vmName, ipAddress, vcenter, esxiHost, datastore, network, cpu, memoryGb, diskGb, vmOwner, provisionedBy, templateName)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
        record["timestamp"], record["vmName"], record["ipAddress"], record["vcenter"], record["esxiHost"], record["datastore"], record["network"], record["cpu"],
        record["memoryGb"], record["diskGb"], record["vmOwner"], record["provisionedBy"], record.get("templateName", "Unknown")
    ))
    conn.commit()
    conn.close()

# ============================================================
# IMPORT VMWARE FUNCTIONS
# ============================================================
try:
    # We now import clone_vm, generate_vm_name, and vm_exists to handle dynamic loops
    from deploy_vm import connect_vcenter, discover_templates, discover_networks, get_obj, get_best_host, get_best_datastore, deploy_multiple_vms, clone_vm, generate_vm_name, vm_exists
    from pyVim.connect import Disconnect
    VMWARE_IMPORT_ERROR = None
except Exception as exc:
    VMWARE_IMPORT_ERROR = str(exc)

# ============================================================
# IPAM SCANNER & LOGIC
# ============================================================
def scan_all_ipam_subnets():
    conn = sqlite3.connect(INVENTORY_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, vcenter, cidr FROM ipam_subnets")
    subnets = cursor.fetchall()
    
    vc_map = {}
    for s in subnets:
        vc_map.setdefault(s[1], []).append(s)

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for vc_identifier, vc_subnets in vc_map.items():
        vc_known_ips = {} # Map IP -> VM Name
        vc_rec = find_vcenter_record(vc_identifier)
        vc_host = vc_rec.get("host") if vc_rec else vc_identifier
        username = vc_rec.get("username", "") if vc_rec else ""
        pwd = get_vaulted_password(vc_host)
        
        # 1. Gather VMware IPs and VM Names
        if pwd and username and vc_host:
            try:
                si = connect_vcenter(vc_host, username, pwd)
                if si:
                    vm_props = get_properties(si, vim.VirtualMachine, ['name', 'guest.ipAddress', 'guest.net'])
                    for vm in vm_props:
                        vm_name = vm.get('name', 'Unknown VM')
                        if vm.get('guest.ipAddress'): 
                            vc_known_ips[vm['guest.ipAddress']] = vm_name
                        if vm.get('guest.net'):
                            for nic in vm['guest.net']:
                                if hasattr(nic, 'ipConfig') and nic.ipConfig:
                                    for ip in getattr(nic.ipConfig, 'ipAddress', []):
                                        if hasattr(ip, 'ipAddress') and ip.ipAddress:
                                            vc_known_ips[ip.ipAddress] = vm_name
                    Disconnect(si)
            except Exception as e:
                print(f"[IPAM] VC Scan failed for {vc_host}: {e}")

        # 2. Iterate IPs, lock active ones, and free dead ones
        for sub in vc_subnets:
            sub_id = sub[0]
            cursor.execute("SELECT id, ip_address, is_manual, status, reason FROM ipam_ips WHERE subnet_id = ?", (sub_id,))
            ips = cursor.fetchall()
            
            def check_ip(ip_row):
                ip_id, ip_addr, is_manual, current_status = ip_row[0], ip_row[1], ip_row[2], ip_row[3]
                current_reason = ip_row[4] if len(ip_row) > 4 else ""
                if is_manual == 1: return None 
                
                # Check VC first (gets VM Name), then Ping fallback
                if ip_addr in vc_known_ips:
                    new_status = "In Use"
                    reason = f"vCenter VM: {vc_known_ips[ip_addr]}"
                elif ping_ip(ip_addr):
                    new_status = "In Use"
                    reason = "Active (Ping Response)"
                else:
                    new_status = "Free"
                    reason = ""
                
                if new_status != current_status or reason != (current_reason or ""):
                    return (new_status, reason, now_str, ip_id)
                return None

            updates = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
                results = executor.map(check_ip, ips)
                for res in results:
                    if res: updates.append(res)
            
            if updates:
                cursor.executemany("UPDATE ipam_ips SET status = ?, reason = ?, last_scanned = ? WHERE id = ?", updates)

    conn.commit()
    conn.close()
 
def ipam_scanner_loop():
    while True:
        try:
            scan_all_ipam_subnets()
        except Exception as e:
            print(f"[IPAM] Scanner Thread Error: {e}")
        time.sleep(300)  # 5-minute interval
 
# Initialize background task
threading.Thread(target=ipam_scanner_loop, daemon=True).start()

# ============================================================
# API ENDPOINTS: AUTHENTICATION & USERS
# ============================================================
@app.route("/api/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS": return jsonify({}), 200
    try:
        data = request.get_json(silent=True) or {}
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", ""))

        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        conn = sqlite3.connect(INVENTORY_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and user["password"] and check_password_hash(user["password"], password):
            user_dict = dict(user)
            user_dict.pop("password", None)
            return jsonify({"message": "Login successful", "user": user_dict}), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    except Exception as e:
        return jsonify({"error": f"Server Error: {str(e)}"}), 500

@app.route("/api/users", methods=["GET", "POST", "OPTIONS"])
def handle_users():
    if request.method == "OPTIONS": return jsonify({}), 200
    if request.method == "GET":
        try:
            conn = sqlite3.connect(INVENTORY_DB)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY id ASC")
            rows = cursor.fetchall()
            conn.close()
            users_clean = []
            for r in rows:
                u = dict(r)
                u.pop("password", None)
                users_clean.append(u)
            return jsonify(users_clean)
        except Exception as e: return jsonify({"error": str(e)}), 500
    if request.method == "POST":
        try:
            data = request.get_json(silent=True) or {}
            username, fullName, role, password = str(data.get("username", "")).strip(), str(data.get("fullName", "")).strip(), str(data.get("role", "")).strip(), str(data.get("password", ""))
            if not username or not fullName or not password: return jsonify({"error": "Fields missing."}), 400
            hashed_pw = generate_password_hash(password)
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect(INVENTORY_DB)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, fullName, role, createdAt, password) VALUES (?, ?, ?, ?, ?)", (username, fullName, role, now_str, hashed_pw))
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            return jsonify({"id": new_id, "username": username, "fullName": fullName, "role": role, "createdAt": now_str}), 201
        except sqlite3.IntegrityError: return jsonify({"error": "A user with this username already exists."}), 409
        except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/users/<int:user_id>", methods=["PUT", "DELETE", "OPTIONS"])
def edit_user(user_id):
    if request.method == "OPTIONS": return jsonify({}), 200
    if request.method == "PUT":
        try:
            data = request.get_json(silent=True) or {}
            username, fullName, role, password = str(data.get("username", "")).strip(), str(data.get("fullName", "")).strip(), str(data.get("role", "")).strip(), str(data.get("password", ""))
            if not username or not fullName: return jsonify({"error": "Fields missing"}), 400
            conn = sqlite3.connect(INVENTORY_DB)
            cursor = conn.cursor()
            if password:
                cursor.execute("UPDATE users SET username=?, fullName=?, role=?, password=? WHERE id=?", (username, fullName, role, generate_password_hash(password), user_id))
            else:
                cursor.execute("UPDATE users SET username=?, fullName=?, role=? WHERE id=?", (username, fullName, role, user_id))
            conn.commit()
            conn.close()
            return jsonify({"id": user_id, "username": username, "fullName": fullName, "role": role}), 200
        except sqlite3.IntegrityError: return jsonify({"error": "A user with this username already exists."}), 409
        except Exception as e: return jsonify({"error": str(e)}), 500
    if request.method == "DELETE":
        try:
            conn = sqlite3.connect(INVENTORY_DB)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()
            conn.close()
            return jsonify({"message": "Removed"})
        except Exception as e: return jsonify({"error": str(e)}), 500

# ============================================================
# API ENDPOINTS: ROLES
# ============================================================
@app.route("/api/roles", methods=["GET", "POST", "OPTIONS"])
def get_roles():
    if request.method == "OPTIONS": return jsonify({}), 200
    if request.method == "GET":
        conn = sqlite3.connect(INVENTORY_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM roles ORDER BY name ASC")
        rows = cursor.fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    elif request.method == "POST":
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", "")).strip()
        if not name: return jsonify({"error": "Role name required"}), 400
        conn = sqlite3.connect(INVENTORY_DB)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO roles (name) VALUES (?)", (name,))
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            return jsonify({"id": new_id, "name": name}), 201
        except sqlite3.IntegrityError:
            return jsonify({"error": "Role exists"}), 409

@app.route("/api/roles/<int:role_id>", methods=["DELETE", "OPTIONS"])
def delete_role(role_id):
    if request.method == "OPTIONS": return jsonify({}), 200
    conn = sqlite3.connect(INVENTORY_DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM roles WHERE id=?", (role_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Role removed."})

# ============================================================
# API ENDPOINTS: VCENTERS
# ============================================================
@app.route("/api/health", methods=["GET", "OPTIONS"])
def health():
    if request.method == "OPTIONS": return jsonify({}), 200
    return jsonify({"status": "online"})

@app.route("/api/vcenters", methods=["GET", "POST", "OPTIONS"])
def handle_vcenters():
    if request.method == "OPTIONS": return jsonify({}), 200
    if request.method == "GET":
        vcenters = load_vcenters()
        sanitized = []
        for vc in vcenters:
            if not isinstance(vc, dict): continue
            sanitized.append({
                "name": str(vc.get("name") or vc.get("host") or "Unnamed"),
                "host": str(vc.get("host") or ""),
                "username": str(vc.get("username") or ""),
                "hasPassword": bool(vc.get("password"))
            })
        return jsonify(sanitized)
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        name, host, username = str(data.get("name", "")).strip(), str(data.get("host", "")).strip(), str(data.get("username", "")).strip()
        password = str(data.get("password", ""))

        if not name or not host or not username: return jsonify({"error": "Name, IP, and Username are required."}), 400

        vcenters = load_vcenters()
        if any(str(vc.get("host", "")).lower() == host.lower() for vc in vcenters if isinstance(vc, dict)):
            return jsonify({"error": "This vCenter IP is already configured."}), 409

        enc_pwd = base64.b64encode(password.encode('utf-8')).decode('utf-8') if password else ""
        new_vcenter = {"name": name, "host": host, "username": username, "password": enc_pwd}
        vcenters.append(new_vcenter)
        save_vcenters(vcenters)
        return jsonify({"name": name, "host": host, "username": username, "hasPassword": bool(password)}), 201

@app.route("/api/vcenters/<path:old_host>", methods=["PUT", "DELETE", "OPTIONS"])
def edit_vcenter(old_host):
    if request.method == "OPTIONS": return jsonify({}), 200
    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        name, new_host, username = str(data.get("name", "")).strip(), str(data.get("host", "")).strip(), str(data.get("username", "")).strip()
        password = str(data.get("password", ""))

        if not name or not new_host or not username: return jsonify({"error": "Name, IP, and Username are required."}), 400

        vcenters = load_vcenters()
        if old_host.lower() != new_host.lower() and any(str(vc.get("host", "")).lower() == new_host.lower() for vc in vcenters if isinstance(vc, dict)):
            return jsonify({"error": "Another vCenter with this new IP exists."}), 409

        for idx, vc in enumerate(vcenters):
            if isinstance(vc, dict) and str(vc.get("host", "")).lower() == old_host.lower():
                enc_pwd = base64.b64encode(password.encode('utf-8')).decode('utf-8') if password else vc.get("password", "")
                vcenters[idx] = {"name": name, "host": new_host, "username": username, "password": enc_pwd}
                save_vcenters(vcenters)
                return jsonify({"name": name, "host": new_host, "username": username, "hasPassword": bool(enc_pwd)}), 200
        return jsonify({"error": "vCenter not found."}), 404
    if request.method == "DELETE":
        vcenters = load_vcenters()
        updated = [vc for vc in vcenters if isinstance(vc, dict) and str(vc.get("host", "")).lower() != old_host.lower()]
        if len(updated) == len(vcenters): return jsonify({"error": "vCenter not found."}), 404
        save_vcenters(updated)
        return jsonify({"message": "vCenter removed successfully."})

# ============================================================
# API ENDPOINTS: TELEMETRY & VMWARE ACTIONS
# ============================================================
@app.route("/api/inventory", methods=["GET", "OPTIONS"])
def get_inventory():
    if request.method == "OPTIONS": return jsonify({}), 200
    return jsonify({"inventory": get_inventory_from_db()})

@app.route("/api/dashboard/live", methods=["GET", "OPTIONS"])
def get_live_dashboard():
    if request.method == "OPTIONS": return jsonify({}), 200
    if VMWARE_IMPORT_ERROR: return jsonify({"error": "VMware module missing."}), 500
    vcenters = load_vcenters()
    live_stats = []

    for vc in vcenters:
        if not isinstance(vc, dict): continue
        host, name, enc_pwd = vc.get("host", ""), vc.get("name") or vc.get("host", ""), vc.get("password", "")

        if not enc_pwd:
            live_stats.append({
                "host": host, "name": name, "status": "No Password Vaulted", "error": True,
                "vms": {"on": 0, "off": 0, "susp": 0, "total": 0}, "compute": {"cpu_tot": 0, "cpu_used": 0, "mem_tot": 0, "mem_used": 0},
                "storage": {"tot": 0, "free": 0, "used": 0}, "hosts": {"connected": 0, "total": 0, "details": []}, "datastores": {"details": []}
            })
            continue

        try: pwd = base64.b64decode(enc_pwd).decode("utf-8")
        except Exception:
            live_stats.append({
                "host": host, "name": name, "status": "Invalid Vault Password", "error": True,
                "vms": {"on": 0, "off": 0, "susp": 0, "total": 0}, "compute": {"cpu_tot": 0, "cpu_used": 0, "mem_tot": 0, "mem_used": 0},
                "storage": {"tot": 0, "free": 0, "used": 0}, "hosts": {"connected": 0, "total": 0, "details": []}, "datastores": {"details": []}
            })
            continue

        try:
            si = connect_vcenter(host, vc.get("username", ""), pwd)
            if not si: raise Exception("Authentication failed.")

            vms_on = vms_off = vms_susp = cpu_tot = cpu_used = mem_tot = mem_used = disk_tot = disk_free = 0

            for v in get_properties(si, vim.VirtualMachine, ['runtime.powerState']):
                state = v.get('runtime.powerState')
                if state == vim.VirtualMachine.PowerState.poweredOn: vms_on += 1
                elif state == vim.VirtualMachine.PowerState.poweredOff: vms_off += 1
                else: vms_susp += 1

            hosts_detail = []
            hosts_connected = hosts_total = 0
            for h in get_properties(si, vim.HostSystem, ['name', 'runtime.connectionState', 'hardware.cpuInfo', 'hardware.memorySize', 'summary.quickStats']):
                hosts_total += 1
                state = h.get('runtime.connectionState')
                state_str = "connected" if state == vim.HostSystem.ConnectionState.connected else str(state)
                c_tot = c_use = m_tot = m_use = 0
                if state == vim.HostSystem.ConnectionState.connected:
                    hosts_connected += 1
                    cpu_info, quick_stats, mem_size = h.get('hardware.cpuInfo'), h.get('summary.quickStats'), h.get('hardware.memorySize')

                    if cpu_info and hasattr(cpu_info, 'numCpuCores') and hasattr(cpu_info, 'hz'):
                        c_tot = (cpu_info.numCpuCores * cpu_info.hz) / 1_000_000_000
                    if quick_stats and hasattr(quick_stats, 'overallCpuUsage') and quick_stats.overallCpuUsage is not None:
                        c_use = float(quick_stats.overallCpuUsage) / 1000

                    if mem_size: m_tot = float(mem_size) / (1024**3)
                    if quick_stats and hasattr(quick_stats, 'overallMemoryUsage') and quick_stats.overallMemoryUsage is not None:
                        m_use = float(quick_stats.overallMemoryUsage) / 1024

                    cpu_tot += c_tot; cpu_used += c_use; mem_tot += m_tot; mem_used += m_use

                hosts_detail.append({
                    "name": str(h.get('name', 'Unknown')), "state": state_str, "cpu_tot": round(c_tot, 2),
                    "cpu_used": round(c_use, 2), "mem_tot": round(m_tot, 2), "mem_used": round(m_use, 2)
                })

            ds_detail = []
            for d in get_properties(si, vim.Datastore, ['name', 'summary.accessible', 'summary.capacity', 'summary.freeSpace']):
                if d.get('summary.accessible'):
                    cap = float(d.get('summary.capacity', 0)) / (1024**3)
                    fr = float(d.get('summary.freeSpace', 0)) / (1024**3)
                    disk_tot += cap; disk_free += fr
                    ds_detail.append({
                        "name": str(d.get('name', 'Unknown')), "capacity": round(cap, 2),
                        "free": round(fr, 2), "used": round(max(0, cap - fr), 2)
                    })

            Disconnect(si)
            live_stats.append({
                "host": host, "name": name, "status": "Online", "error": False,
                "vms": {"on": vms_on, "off": vms_off, "susp": vms_susp, "total": vms_on + vms_off + vms_susp},
                "compute": {"cpu_tot": round(cpu_tot, 2), "cpu_used": round(cpu_used, 2), "mem_tot": round(mem_tot, 2), "mem_used": round(mem_used, 2)},
                "storage": {"tot": round(disk_tot, 2), "free": round(disk_free, 2), "used": round(max(0, disk_tot - disk_free), 2)},
                "hosts": {"connected": hosts_connected, "total": hosts_total, "details": hosts_detail},
                "datastores": {"details": ds_detail}
            })
        except Exception:
            live_stats.append({
                "host": host, "name": name, "status": "Offline / Auth Error", "error": True,
                "vms": {"on": 0, "off": 0, "susp": 0, "total": 0}, "compute": {"cpu_tot": 0, "cpu_used": 0, "mem_tot": 0, "mem_used": 0},
                "storage": {"tot": 0, "free": 0, "used": 0}, "hosts": {"connected": 0, "total": 0, "details": []}, "datastores": {"details": []}
            })

    return jsonify({"live": live_stats})

def connect_to_requested_vcenter():
    data = request.get_json(silent=True) or {}
    host, username, password = str(data.get("host", "")).strip(), str(data.get("username", "")).strip(), str(data.get("password", ""))
    if not password: password = get_vaulted_password(host)

    if not host or not username or not password: return None, (jsonify({"error": "Host, username, and password are required."}), 400)
    if VMWARE_IMPORT_ERROR: return None, (jsonify({"error": "VMware module missing."}), 500)
    try:
        si = connect_vcenter(host, username, password)
        if si is None: return None, (jsonify({"error": "Unable to connect to vCenter."}), 500)
        return si, None
    except Exception as exc: return None, (jsonify({"error": str(exc)}), 401)

@app.route("/api/vcenters/templates", methods=["POST", "OPTIONS"])
def get_vcenter_templates():
    if request.method == "OPTIONS": return jsonify({}), 200
    si, err = connect_to_requested_vcenter()
    if err: return err
    return jsonify({"templates": [{"name": getattr(t, "name", "")} for t in discover_templates(si.RetrieveContent()) if getattr(t, "name", "")]})

@app.route("/api/vcenters/networks", methods=["POST", "OPTIONS"])
def get_vcenter_networks():
    if request.method == "OPTIONS": return jsonify({}), 200
    si, err = connect_to_requested_vcenter()
    if err: return err
    try:
        host_map = {h['id']: h['name'] for h in get_properties(si, vim.HostSystem, ['name'])}
        res = []
        for n in discover_networks(si.RetrieveContent()):
            n_name = getattr(n, "name", "")
            if not n_name: continue
            host_names = []
            if hasattr(n, 'host') and n.host:
                for h_ref in n.host:
                    try:
                        mo_id = str(getattr(h_ref, '_moId', ''))
                        if mo_id in host_map: host_names.append(host_map[mo_id])
                    except Exception: pass
            res.append({"name": str(n_name), "hosts": host_names})
        res.sort(key=lambda x: x['name'].lower())
        return jsonify({"networks": res})
    except Exception as exc:
        return jsonify({"networks": [{"name": getattr(n, "name", ""), "hosts": []} for n in discover_networks(si.RetrieveContent()) if getattr(n, "name", "")]})

@app.route("/api/vcenters/hosts", methods=["POST", "OPTIONS"])
def get_vcenter_hosts():
    if request.method == "OPTIONS": return jsonify({}), 200
    si, err = connect_to_requested_vcenter()
    if err: return err
    try:
        res = []
        host_items = get_properties(si, vim.HostSystem, ['name', 'hardware.cpuInfo', 'hardware.memorySize', 'summary.quickStats', 'runtime.connectionState'])
        for h in host_items:
            name = h.get('name')
            if not name: continue
            cpu_tot = cpu_free = mem_tot = mem_free = 0.0
            cpu_info, quick_stats, mem_size = h.get('hardware.cpuInfo'), h.get('summary.quickStats'), h.get('hardware.memorySize')

            if cpu_info and hasattr(cpu_info, 'numCpuCores') and hasattr(cpu_info, 'hz'):
                cpu_tot = float(cpu_info.numCpuCores * cpu_info.hz) / 1_000_000_000.0
            if quick_stats and hasattr(quick_stats, 'overallCpuUsage') and quick_stats.overallCpuUsage is not None:
                cpu_used = float(quick_stats.overallCpuUsage) / 1000.0
                cpu_free = max(0.0, cpu_tot - cpu_used)
            else: cpu_free = cpu_tot

            if mem_size: mem_tot = float(mem_size) / (1024.0 ** 3)
            if quick_stats and hasattr(quick_stats, 'overallMemoryUsage') and quick_stats.overallMemoryUsage is not None:
                mem_used = float(quick_stats.overallMemoryUsage) / 1024.0
                mem_free = max(0.0, mem_tot - mem_used)
            else: mem_free = mem_tot

            res.append({"name": str(name), "cpu_free": round(cpu_free, 2), "cpu_tot": round(cpu_tot, 2), "mem_free": round(mem_free, 2), "mem_tot": round(mem_tot, 2)})
        res.sort(key=lambda x: x['name'].lower())
        return jsonify({"hosts": res})
    except Exception as exc: return jsonify({"error": str(exc)}), 500

@app.route("/api/vcenters/datastores", methods=["POST", "OPTIONS"])
def get_vcenter_datastores():
    if request.method == "OPTIONS": return jsonify({}), 200
    si, err = connect_to_requested_vcenter()
    if err: return err
    try:
        host_map = {h['id']: h['name'] for h in get_properties(si, vim.HostSystem, ['name'])}
        res = []
        for d in get_properties(si, vim.Datastore, ['name', 'summary.freeSpace', 'summary.capacity', 'host']):
            if not d.get('name'): continue
            host_names = []
            for m in d.get('host', []):
                try:
                    mo_id = str(getattr(m.key, '_moId', ''))
                    if mo_id in host_map: host_names.append(host_map[mo_id])
                except Exception: pass
            free_gb = float(d.get('summary.freeSpace', 0)) / (1024**3)
            cap_gb = float(d.get('summary.capacity', 0)) / (1024**3)
            res.append({"name": str(d['name']), "free_gb": round(free_gb, 2), "capacity_gb": round(cap_gb, 2), "hosts": host_names})
        res.sort(key=lambda x: x['name'].lower())
        return jsonify({"datastores": res})
    except Exception as exc: return jsonify({"error": str(exc)}), 500

@app.route("/api/deploy", methods=["POST", "OPTIONS"])
def deploy_vms():
    if request.method == "OPTIONS": return jsonify({}), 200
    data = request.get_json(silent=True) or {}
    
    host = str(data.get("vcenter", "")).strip()
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", "")) or get_vaulted_password(host)
    
    template_name = data.get("template")
    network_name = data.get("network")
    target_host_name = data.get("host")
    target_datastore_name = data.get("datastore")
    
    cpu_count = int(data.get("cpu", 2))
    memory_gb = int(data.get("memory", 4))
    disk_size_gb = int(data.get("disk", 40))
    vm_count = int(data.get("vmCount", 1))
    
    naming_context = data.get("namingContext")
    vm_owner = str(data.get("vmOwner", "")).strip()
    local_admin_password = data.get("localAdminPassword")

    # Replace the "New IP Parsing Architecture" block in /api/deploy with this:
    ip_mode = data.get("ipMode", "series")
    ip_list = data.get("ipList", [])  
    starting_ip = data.get("startingIp")  
    subnet_mask = data.get("subnet")
    gateway = data.get("gateway")
    dns_server = data.get("dns")
    ipam_subnet_id = data.get("ipamSubnetId")
 
    if ip_mode == "ipam":
        if not ipam_subnet_id: return jsonify({"error": "IPAM subnet not selected."}), 400
        conn = sqlite3.connect(INVENTORY_DB)
        cursor = conn.cursor()
        # Pull required number of Verified Free IPs
        cursor.execute("SELECT ip_address FROM ipam_ips WHERE subnet_id = ? AND status = 'Free' AND is_manual = 0 LIMIT ?", (ipam_subnet_id, vm_count))
        free_ips = [row[0] for row in cursor.fetchall()]
        if len(free_ips) < vm_count:
            conn.close()
            return jsonify({"error": f"Insufficient free IPs in selected subnet. Found {len(free_ips)}, needed {vm_count}."}), 400
        # Lock IPs immediately as 'Reserved' to prevent collision
        for ip in free_ips:
            cursor.execute("UPDATE ipam_ips SET status = 'Reserved', is_manual = 1, reason = 'Provisioned via VM Studio' WHERE subnet_id = ? AND ip_address = ?", (ipam_subnet_id, ip))
        # Load Subnet Context
        cursor.execute("SELECT cidr, gateway FROM ipam_subnets WHERE id = ?", (ipam_subnet_id,))
        subnet_info = cursor.fetchone()
        conn.commit()
        conn.close()
 
        # Inject IPAM IPs into the deployment pipeline mimicking manual dynamic mode
        ip_mode = "dynamic"
        ip_list = free_ips
        subnet_mask = str(ipaddress.IPv4Network(subnet_info[0], strict=False).netmask)
        gateway = subnet_info[1]

    if not all([host, username, password, template_name, network_name, local_admin_password]): 
        return jsonify({"error": "Missing required fields or password."}), 400

    try:
        subnet_mask_obj = ipaddress.IPv4Address(subnet_mask)
        gateway_obj = ipaddress.IPv4Address(gateway) if gateway else None
        dns_server_obj = ipaddress.IPv4Address(dns_server) if dns_server else None
    except ValueError as exc: 
        return jsonify({"error": f"Invalid network configuration: {exc}"}), 400

    try:
        si = connect_vcenter(host, username, password)
        if si is None: return jsonify({"error": "Unable to connect."}), 500
        content = si.RetrieveContent()

        template_obj = get_obj(content, [vim.VirtualMachine], template_name)
        network_obj = get_obj(content, [vim.Network], network_name)
        host_obj = get_obj(content, [vim.HostSystem], target_host_name) if target_host_name else get_best_host(content, cpu_count, memory_gb)
        datastore_obj = get_obj(content, [vim.Datastore], target_datastore_name) if target_datastore_name else get_best_datastore(content, host_obj, disk_size_gb)

        if not all([template_obj, network_obj, host_obj, datastore_obj]): 
            return jsonify({"error": "One or more target VMware objects could not be resolved."}), 404

        successful = []
        failed = []

        is_esxi = bool(data.get("is_esxi", False))
        if not is_esxi and ("esxi" in str(template_name).lower()):
            is_esxi = True

        if ip_mode == "dynamic":
            # --------------------------------------------------------
            # MANUAL / NON-SEQUENTIAL IP DEPLOYMENT LOOP
            # --------------------------------------------------------
            deployment_plan = []
            for idx, ip_str in enumerate(ip_list):
                try:
                    ip_obj = ipaddress.IPv4Address(ip_str)
                    vm_name = generate_vm_name(naming_context, ip_obj)
                    deployment_plan.append({"name": vm_name, "ip": ip_obj})
                except ValueError:
                    return jsonify({"error": f"Invalid IP address format at Node #{idx+1}: {ip_str}"}), 400

            # Pre-check existence to prevent partial failures
            for item in deployment_plan:
                if vm_exists(content, item["name"]):
                    return jsonify({"error": f"VM '{item['name']}' already exists in vCenter. Deployment aborted."}), 400

            # Execute sequential cloning with non-sequential IPs
            for item in deployment_plan:
                try:
                    vm = clone_vm(
                        content=content, template=template_obj, vm_name=item["name"], ip_address=item["ip"],
                        subnet_mask=subnet_mask_obj, gateway=gateway_obj, dns_server=dns_server_obj,
                        local_admin_password=local_admin_password, host=host_obj, datastore=datastore_obj,
                        network=network_obj, cpu_count=cpu_count, memory_gb=memory_gb, disk_size_gb=disk_size_gb,
                        vm_owner=vm_owner, is_esxi=is_esxi
                    )
                    successful.append({
                        "name": vm.name, "ip": str(item["ip"]), "host": host_obj.name, 
                        "datastore": datastore_obj.name, "network": network_obj.name, "template": template_obj.name
                    })
                except Exception as exc:
                    failed.append({"name": item["name"], "ip": str(item["ip"]), "error": str(exc)})
        else:
            # --------------------------------------------------------
            # AUTO-INCREMENTING SEQUENTIAL IP DEPLOYMENT
            # --------------------------------------------------------
            starting_ip_obj = ipaddress.IPv4Address(starting_ip)
            successful, failed = deploy_multiple_vms(
                content=content, template=template_obj, network=network_obj, host=host_obj, datastore=datastore_obj,
                cpu_count=cpu_count, memory_gb=memory_gb, disk_size_gb=disk_size_gb, vm_count=vm_count,
                naming_context=naming_context, starting_ip=starting_ip_obj, subnet_mask=subnet_mask_obj,
                gateway=gateway_obj, dns_server=dns_server_obj, local_admin_password=local_admin_password, vm_owner=vm_owner,
                is_esxi=is_esxi
            )

        if successful:
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for item in successful:
                log_deployment_to_db({
                    "timestamp": now_str, "vmName": item["name"], "ipAddress": item["ip"], "vcenter": host,
                    "esxiHost": item.get("host", host_obj.name), "datastore": item.get("datastore", datastore_obj.name),
                    "network": item.get("network", network_obj.name), "cpu": cpu_count, "memoryGb": memory_gb,
                    "diskGb": disk_size_gb, "vmOwner": vm_owner or "N/A", "provisionedBy": username, "templateName": item.get("template", template_obj.name)
                })
        APP_CACHE.pop("explorer_data", None)
        return jsonify({"successful": successful, "failed": failed, "message": "Deployment complete."}), 200
    except Exception as exc: 
        return jsonify({"error": str(exc)}), 500

# ============================================================
# API ENDPOINTS: IPAM (IP Address Management)
# ============================================================
@app.route("/api/ipam/subnets", methods=["GET", "POST", "OPTIONS"])
def handle_ipam_subnets():
    if request.method == "OPTIONS": return jsonify({}), 200
    if request.method == "GET":
        conn = sqlite3.connect(INVENTORY_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ipam_subnets ORDER BY name ASC")
        rows = cursor.fetchall()
        subnets = []
        for r in rows:
            sub_dict = dict(r)
            cursor.execute("SELECT count(*) FROM ipam_ips WHERE subnet_id = ? AND status = 'Free'", (r['id'],))
            sub_dict['free_ips'] = cursor.fetchone()[0]
            cursor.execute("SELECT count(*) FROM ipam_ips WHERE subnet_id = ?", (r['id'],))
            sub_dict['total_ips'] = cursor.fetchone()[0]
            subnets.append(sub_dict)
        conn.close()
        return jsonify(subnets)
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        vcenter, name, cidr, gateway = data.get("vcenter"), data.get("name"), data.get("cidr"), data.get("gateway")
        vlan = str(data.get("vlan", "")).strip()
        if not all([vcenter, name, cidr, gateway]):
            return jsonify({"error": "All fields required."}), 400
        try:
            network = ipaddress.IPv4Network(cidr, strict=False)
        except ValueError:
            return jsonify({"error": "Invalid CIDR notation."}), 400
 
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(INVENTORY_DB)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ipam_subnets (vcenter, name, cidr, gateway, vlan) VALUES (?, ?, ?, ?, ?)", (vcenter, name, cidr, gateway, vlan))
        subnet_id = cursor.lastrowid
        # Populate all valid host IPs 
        ips_to_insert = []
        for ip in network.hosts():
            ips_to_insert.append((subnet_id, str(ip), "Free", 0, "", now_str))
        cursor.executemany("INSERT INTO ipam_ips (subnet_id, ip_address, status, is_manual, reason, last_scanned) VALUES (?, ?, ?, ?, ?, ?)", ips_to_insert)
        conn.commit()
        conn.close()
        # Trigger an immediate scan
        threading.Thread(target=scan_all_ipam_subnets, daemon=True).start()
        return jsonify({"message": "Subnet onboarded."}), 201
 
@app.route("/api/ipam/subnets/<int:subnet_id>", methods=["DELETE", "OPTIONS"])
def delete_subnet(subnet_id):
    if request.method == "OPTIONS": return jsonify({}), 200
    conn = sqlite3.connect(INVENTORY_DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ipam_ips WHERE subnet_id = ?", (subnet_id,))
    cursor.execute("DELETE FROM ipam_subnets WHERE id = ?", (subnet_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Subnet deleted."})
 
@app.route("/api/ipam/subnets/<int:subnet_id>/ips", methods=["GET", "OPTIONS"])
def get_subnet_ips(subnet_id):
    if request.method == "OPTIONS": return jsonify({}), 200
    conn = sqlite3.connect(INVENTORY_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ipam_ips WHERE subnet_id = ? ORDER BY id ASC", (subnet_id,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
 
@app.route("/api/ipam/ips/<int:ip_id>", methods=["PUT", "OPTIONS"])
def update_ip_status(ip_id):
    if request.method == "OPTIONS": return jsonify({}), 200
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    reason = data.get("reason", "")
    # Enable manual override flag when modified by an operator
    is_manual = 1 if status in ["Quarantined", "Reserved", "In Use"] else 0
    if status == "Free": is_manual = 0  # Re-enable auto-scanning for this IP
    conn = sqlite3.connect(INVENTORY_DB)
    cursor = conn.cursor()
    cursor.execute("UPDATE ipam_ips SET status = ?, is_manual = ?, reason = ? WHERE id = ?", (status, is_manual, reason, ip_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "IP status updated."})

# ============================================================
# API ENDPOINTS: VCENTER DISCOVERY, EXPLORER, THRESHOLDS & RECLAMATION
# ============================================================
@app.route("/api/vcenters/discover", methods=["POST", "OPTIONS"])
def discover_vcenters_from_subnet():
    if request.method == "OPTIONS": return jsonify({}), 200
    data = request.get_json(silent=True) or {}
    subnet_id = data.get("subnetId")
    if not subnet_id: return jsonify({"error": "Subnet ID required"}), 400
    
    conn = sqlite3.connect(INVENTORY_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT cidr FROM ipam_subnets WHERE id = ?", (subnet_id,))
    subnet = cursor.fetchone()
    conn.close()
    
    if not subnet: return jsonify({"error": "Subnet not found"}), 404
    network = ipaddress.IPv4Network(subnet[0], strict=False)
    
    configured_hosts = [normalize_host(vc.get("host")) for vc in load_vcenters() if isinstance(vc, dict)]
    recognized = []
    
    def probe_vc(ip):
        if ping_ip(ip):
            try:
                resp = requests.get(f"https://{ip}/", verify=False, timeout=2)
                if "VMware vSphere" in resp.text or "ID_VC" in resp.text:
                    return str(ip)
            except: pass
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(probe_vc, network.hosts())
        for res in results:
            if res and normalize_host(res) not in configured_hosts:
                recognized.append(res)
            
    return jsonify({"recognized_vcenters": recognized, "discovered": recognized})

def fetch_explorer_data():
    # Builds the nested VC -> Host -> Datastore/VM hierarchy
    vcenters = load_vcenters()
    explorer_data = []

    for vc in vcenters:
        if not isinstance(vc, dict): continue
        host, username, enc_pwd = vc.get("host"), vc.get("username"), vc.get("password")
        pwd = get_vaulted_password(host)
        if not pwd and enc_pwd:
            try:
                pwd = base64.b64decode(enc_pwd).decode("utf-8")
            except Exception:
                continue
        if not pwd: continue
        
        try:
            si = connect_vcenter(host, username, pwd)
            if not si: continue
            
            vc_node = {"vc": host, "hosts": []}
            
            # Map Datastores
            ds_props = get_properties(si, vim.Datastore, ['name', 'summary.capacity', 'summary.freeSpace', 'host'])
            ds_map = {}
            for d in ds_props:
                d_id = d['id']
                cap = float(d.get('summary.capacity', 0)) / (1024**3)
                free = float(d.get('summary.freeSpace', 0)) / (1024**3)
                ds_map[d_id] = {"name": d.get('name'), "cap": round(cap,2), "free": round(free,2)}

            # Map VMs
            vm_props = get_properties(si, vim.VirtualMachine, ['name', 'runtime.powerState', 'runtime.host'])
            vm_map = {} # host_id -> list of VMs
            for vm in vm_props:
                h_ref = vm.get('runtime.host')
                if h_ref:
                    h_id = getattr(h_ref, '_moId', '')
                    vm_map.setdefault(h_id, []).append({
                        "name": vm.get('name'), 
                        "state": str(vm.get('runtime.powerState')),
                        "moId": vm['id']
                    })
            
            # Map Hosts
            host_props = get_properties(si, vim.HostSystem, ['name', 'hardware.cpuInfo', 'hardware.memorySize', 'datastore', 'summary.quickStats'])
            for h in host_props:
                h_id = h['id']
                cpu_info = h.get('hardware.cpuInfo')
                h_cpu = (cpu_info.numCpuCores * cpu_info.hz) / 1e9 if cpu_info and hasattr(cpu_info, 'numCpuCores') and hasattr(cpu_info, 'hz') else 0
                mem_size = h.get('hardware.memorySize')
                h_mem = mem_size / (1024**3) if mem_size else 0
                
                qs = h.get('summary.quickStats')
                c_used_mhz = getattr(qs, 'overallCpuUsage', 0) or 0
                m_used_mb = getattr(qs, 'overallMemoryUsage', 0) or 0
                h_cpu_used = round(c_used_mhz / 1000.0, 2)
                h_mem_used = round(m_used_mb / 1024.0, 2)

                # Associated Datastores
                connected_ds = []
                if h.get('datastore'):
                    for d_ref in h.get('datastore'):
                        d_mo = getattr(d_ref, '_moId', '')
                        if d_mo in ds_map: connected_ds.append(ds_map[d_mo])
                
                vc_node["hosts"].append({
                    "name": h.get('name'),
                    "cpu_tot": round(h_cpu, 2),
                    "cpu_used": h_cpu_used,
                    "mem_tot": round(h_mem, 2),
                    "mem_used": h_mem_used,
                    "datastores": connected_ds,
                    "vms": vm_map.get(h_id, [])
                })
            
            explorer_data.append(vc_node)
            Disconnect(si)
        except Exception as e:
            print(f"[EXPLORER] Error scanning {host}: {e}")

    return explorer_data

@app.route("/api/explorer", methods=["GET", "OPTIONS"])
def vmware_explorer():
    if request.method == "OPTIONS": return jsonify({}), 200
    # Cache for 300 seconds (5 minutes)
    explorer_data = get_cached_response("explorer_data", 300, fetch_explorer_data)
    return jsonify({"explorer": explorer_data})

@app.route("/api/explorer/vm/action", methods=["POST", "OPTIONS"])
def vm_power_action():
    if request.method == "OPTIONS": return jsonify({}), 200
    data = request.get_json(silent=True) or {}
    vc_host, vm_name, action = data.get('vcenter'), data.get('vm_name'), data.get('action')
    
    pwd = get_vaulted_password(vc_host)
    username = next((v["username"] for v in load_vcenters() if isinstance(v, dict) and (v.get("host") == vc_host or normalize_host(v.get("host")) == normalize_host(vc_host) or v.get("name") == vc_host)), "")
    if not username:
        vc_rec = find_vcenter_record(vc_host)
        if vc_rec:
            username = vc_rec.get("username", "")
            if not pwd: pwd = get_vaulted_password(vc_rec.get("host"))
            vc_host = vc_rec.get("host", vc_host)
    
    si = connect_vcenter(vc_host, username, pwd)
    if not si: return jsonify({"error": "Auth failed"}), 401
    
    try:
        vm = get_obj(si.RetrieveContent(), [vim.VirtualMachine], vm_name)
        if not vm: return jsonify({"error": "VM not found"}), 404
        
        if action == "poweron": vm.PowerOnVM_Task()
        elif action == "poweroff": vm.PowerOffVM_Task()
        elif action == "suspend": vm.SuspendVM_Task()
        elif action == "delete": vm.Destroy_Task()
        elif action == "migrate": return jsonify({"message": f"Migration action noted for {vm_name}"})
        APP_CACHE.pop("explorer_data", None)
        return jsonify({"message": f"Task {action} triggered for {vm_name}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try: Disconnect(si)
        except Exception: pass

@app.route("/api/explorer/vm/manage", methods=["POST", "OPTIONS"])
def manage_vm_advanced():
    if request.method == "OPTIONS": return jsonify({}), 200
    data = request.get_json(silent=True) or {}
    vc_host, vm_name, action = data.get('vcenter'), data.get('vm_name'), data.get('action')
    
    pwd = get_vaulted_password(vc_host)
    username = next((v["username"] for v in load_vcenters() if isinstance(v, dict) and (v.get("host") == vc_host or normalize_host(v.get("host")) == normalize_host(vc_host) or v.get("name") == vc_host)), "")
    if not username:
        vc_rec = find_vcenter_record(vc_host)
        if vc_rec:
            username = vc_rec.get("username", "")
            if not pwd: pwd = get_vaulted_password(vc_rec.get("host"))
            vc_host = vc_rec.get("host", vc_host)

    si = connect_vcenter(vc_host, username, pwd)
    if not si: return jsonify({"error": "Auth failed"}), 401
    
    try:
        vm = get_obj(si.RetrieveContent(), [vim.VirtualMachine], vm_name)
        if not vm: return jsonify({"error": "VM not found"}), 404
        
        if action == "snapshot":
            snap_name = data.get("snapshot_name", "Manual Snapshot")
            snap_desc = data.get("snapshot_desc", "")
            vm.CreateSnapshot_Task(name=snap_name, description=snap_desc, memory=False, quiesce=False)
            APP_CACHE.pop("explorer_data", None)
            return jsonify({"message": f"Snapshot '{snap_name}' created."})
            
        elif action == "rename":
            new_name = data.get("new_name")
            if not new_name: return jsonify({"error": "New name required"}), 400
            vm.Rename_Task(newName=new_name)
            APP_CACHE.pop("explorer_data", None)
            return jsonify({"message": f"VM renamed to {new_name}."})
            
        elif action == "migrate":
            target_host_name = data.get("target_host")
            if not target_host_name: return jsonify({"error": "Target host required"}), 400
            target_host = get_obj(si.RetrieveContent(), [vim.HostSystem], target_host_name)
            if not target_host: return jsonify({"error": f"Target host '{target_host_name}' not found"}), 404
            relocate_spec = vim.vm.RelocateSpec(host=target_host)
            vm.RelocateVM_Task(spec=relocate_spec, priority=vim.VirtualMachine.MovePriority.defaultPriority)
            APP_CACHE.pop("explorer_data", None)
            return jsonify({"message": f"Migration to {target_host_name} initiated."})
        else:
            return jsonify({"error": f"Unsupported action: {action}"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            Disconnect(si)
        except Exception:
            pass

def fetch_threshold_data(cpu_thresh, mem_thresh, disk_thresh):
    data = {"datastores": [], "hosts": [], "vms": []}
    
    for vc in load_vcenters():
        if not isinstance(vc, dict): continue
        pwd = get_vaulted_password(vc.get("host"))
        if not pwd: continue
        try:
            si = connect_vcenter(vc["host"], vc["username"], pwd)
            if not si: continue
            
            # Datastores
            for d in get_properties(si, vim.Datastore, ['name', 'summary.capacity', 'summary.freeSpace']):
                cap = float(d.get('summary.capacity', 1))
                used = cap - float(d.get('summary.freeSpace', 0))
                percent = (used / max(cap, 1)) * 100
                if percent > disk_thresh:
                    data["datastores"].append({"vc": vc["host"], "name": d.get('name'), "usage_percent": round(percent, 1)})
            
            # Hosts
            for h in get_properties(si, vim.HostSystem, ['name', 'summary.quickStats', 'hardware.cpuInfo', 'hardware.memorySize']):
                qs = h.get('summary.quickStats')
                if not qs: continue
                
                c_use = getattr(qs, 'overallCpuUsage', 0) or 0
                cpu_info = h.get('hardware.cpuInfo')
                c_tot = (cpu_info.numCpuCores * cpu_info.hz / 1e6) if cpu_info and hasattr(cpu_info, 'numCpuCores') and hasattr(cpu_info, 'hz') else 1
                cpu_pct = (c_use / max(c_tot, 1)) * 100
                
                m_use = getattr(qs, 'overallMemoryUsage', 0) or 0
                mem_size = h.get('hardware.memorySize')
                m_tot = mem_size / (1024**2) if mem_size else 1
                mem_pct = (m_use / max(m_tot, 1)) * 100
                
                if cpu_pct > cpu_thresh or mem_pct > mem_thresh:
                    data["hosts"].append({"vc": vc["host"], "name": h.get('name'), "cpu_pct": round(cpu_pct, 1), "mem_pct": round(mem_pct, 1)})
            
            Disconnect(si)
        except Exception: pass
    return data

@app.route("/api/thresholds", methods=["GET", "OPTIONS"])
def get_thresholds():
    if request.method == "OPTIONS": return jsonify({}), 200
    cpu = float(request.args.get('cpu', 80))
    mem = float(request.args.get('mem', 80))
    disk = float(request.args.get('disk', 80))
    
    cache_key = f"thresholds_{cpu}_{mem}_{disk}"
    data = get_cached_response(cache_key, 300, fetch_threshold_data, cpu, mem, disk)
    return jsonify(data)

@app.route("/api/reclamation", methods=["GET", "OPTIONS"])
def get_reclamation_data():
    if request.method == "OPTIONS": return jsonify({}), 200
    stale_days = int(request.args.get('days', 15))
    zombie_cpu_pct = float(request.args.get('cpu', 5))
    
    data = {"stale": [], "zombies": []}
    cutoff_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=stale_days)

    for vc in load_vcenters():
        if not isinstance(vc, dict): continue
        pwd = get_vaulted_password(vc.get("host"))
        if not pwd: continue
        try:
            si = connect_vcenter(vc["host"], vc["username"], pwd)
            if not si: continue
            
            for vm in get_properties(si, vim.VirtualMachine, ['name', 'runtime.powerState', 'summary.quickStats', 'config.hardware.numCPU']):
                state = vm.get('runtime.powerState')
                
                # Stale logic (simplified: relying on quickStats uptime/boot time tracking or simple off state)
                if state == vim.VirtualMachine.PowerState.poweredOff or str(state) == "poweredOff" or str(state).endswith("poweredOff"):
                    data["stale"].append({"vc": vc["host"], "name": vm.get('name')})
                
                # Zombie logic (powered on, CPU < threshold, low net)
                if state == vim.VirtualMachine.PowerState.poweredOn or str(state) == "poweredOn" or str(state).endswith("poweredOn"):
                    qs = vm.get('summary.quickStats')
                    cores = vm.get('config.hardware.numCPU', 1) or 1
                    if qs:
                        c_use = getattr(qs, 'overallCpuUsage', 0) or 0
                        # Assuming average 2GHz per core for rough zombie math if max isn't available
                        c_tot = cores * 2000 
                        calc_pct = (c_use / max(c_tot, 1)) * 100
                        if calc_pct < zombie_cpu_pct:
                            data["zombies"].append({"vc": vc["host"], "name": vm.get('name'), "cpu_usage": round(calc_pct, 2)})
            
            Disconnect(si)
        except Exception: pass
    
    return jsonify(data)

# Temporary in-memory session store for chatbot context
chat_sessions = {}

@app.route("/api/chatbot", methods=["POST", "OPTIONS"])
def internal_chatbot():
    if request.method == "OPTIONS": return jsonify({}), 200
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "default")
    prompt = data.get("prompt", "").lower().strip()
    
    if session_id not in chat_sessions or prompt in ["reset", "clear", "start over", "new session"]:
        chat_sessions[session_id] = {"intent": "deploy", "params": {}}
        if prompt in ["reset", "clear", "start over"]:
            return jsonify({"reply": "Session reset. Let's build some VMs. What template and vCenter are we using?", "ready": False, "params": {}})
        
    session = chat_sessions[session_id]
    params = session["params"]

    # Keyword Extraction
    count_match = re.search(r'(\d+)\s+(?:vms?|virtual machines?|nodes?|instances?)', prompt)
    if not count_match: count_match = re.search(r'count(?:\s+is)?\s+(\d+)', prompt)
    if count_match: params["vmCount"] = int(count_match.group(1))
        
    if "vcenter" in prompt:
        vc_match = re.search(r'vcenter\s+(?:is\s+)?([a-zA-Z0-9.-]+)', prompt)
        if vc_match: params["vcenter"] = vc_match.group(1)
    else:
        for vc in load_vcenters():
            if isinstance(vc, dict) and (str(vc.get("host", "")).lower() in prompt or str(vc.get("name", "")).lower() in prompt):
                params["vcenter"] = vc.get("host")
                break
        
    if "template" in prompt:
        tmpl_match = re.search(r'template\s+(?:is\s+)?([a-zA-Z0-9._-]+)', prompt)
        if tmpl_match: params["template"] = tmpl_match.group(1)
        
    required = ["vcenter", "template", "vmCount"]
    missing = [req for req in required if req not in params]
    
    if missing:
        return jsonify({"reply": f"Got it. I have {params}. To proceed, I still need: {', '.join(missing)}.", "ready": False, "params": params})
    
    def background_chatbot_deploy(deploy_params):
        try:
            vc_target = deploy_params["vcenter"]
            vc_rec = find_vcenter_record(vc_target)
            actual_host = vc_rec.get("host") if vc_rec else vc_target
            actual_user = vc_rec.get("username", "administrator@vsphere.local") if vc_rec else "administrator@vsphere.local"
            actual_pwd = get_vaulted_password(actual_host)
            
            # Fetch corresponding IPAM subnet to avoid hardcoded IPs
            conn = sqlite3.connect(INVENTORY_DB)
            c = conn.cursor()
            c.execute("SELECT id FROM ipam_subnets WHERE vcenter = ? LIMIT 1", (actual_host,))
            row = c.fetchone()
            if not row:
                c.execute("SELECT id FROM ipam_subnets WHERE vcenter = ? LIMIT 1", (vc_target,))
                row = c.fetchone()
            if not row:
                c.execute("SELECT id FROM ipam_subnets LIMIT 1")
                row = c.fetchone()
            ipam_sub_id = row[0] if row else None
            conn.close()

            if not ipam_sub_id:
                print(f"[CHATBOT] Error: No IPAM subnet onboarded for vCenter {actual_host}")
                return

            payload = {
                "vcenter": actual_host,
                "template": deploy_params["template"],
                "vmCount": deploy_params["vmCount"],
                "username": actual_user,
                "password": actual_pwd,
                "ipMode": "ipam",
                "ipamSubnetId": ipam_sub_id,
                "namingContext": "BOT-VM-",
                "cpu": 2, "memory": 4, "disk": 40,
                "localAdminPassword": "Password@123"
            }
            requests.post("http://127.0.0.1:5052/api/deploy", json=payload, timeout=600)
            APP_CACHE.pop("explorer_data", None)
        except Exception as e:
            print(f"[CHATBOT DEPLOY ERROR] {e}")

    threading.Thread(target=background_chatbot_deploy, args=(params,), daemon=True).start()
    chat_sessions[session_id] = {"intent": "deploy", "params": {}}
    
    return jsonify({
        "reply": f"All set. I'm dynamically pulling available IPs from IPAM and provisioning {params['vmCount']} VMs from '{params['template']}' on '{params['vcenter']}'.",
        "ready": True,
        "params": {}
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5052, debug=True)