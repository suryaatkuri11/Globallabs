import { useEffect, useState } from "react";

const API_BASE = typeof window !== "undefined" && window.location.protocol.startsWith("http")
  ? `http://${window.location.hostname}:5052/api`
  : "http://10.131.50.68:5052/api";

// --- Minimal Lucide Icon Helper ---
const Icon = ({ name, className = "w-4 h-4" }) => {
  const icons = {
    server: <><path d="M2 4a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V4zm0 10a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-4zM6 6h.01M6 16h.01" /></>,
    mail: <><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2zM22 6l-10 7L2 6" /></>,
    lock: <><path d="M19 11H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7a2 2 0 0 0-2-2zm-7-3V7a5 5 0 0 1 10 0v4" /></>,
    arrowRight: <g><path d="M5 12h14" /><path d="M12 5l7 7-7 7" /></g>,
    cpu: <g><rect x="4" y="4" width="16" height="16" rx="2" ry="2" /><path d="M9 9h6v6H9zM9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3" /></g>,
    layoutDashboard: <g><rect x="3" y="3" width="7" height="9" rx="1" /><rect x="14" y="3" width="7" height="5" rx="1" /><rect x="14" y="12" width="7" height="9" rx="1" /><rect x="3" y="16" width="7" height="5" rx="1" /></g>,
    plusCircle: <g><circle cx="12" cy="12" r="10" /><path d="M12 8v8M8 12h8" /></g>,
    activity: <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />,
    layers: <g><polygon points="12 2 2 7 12 12 22 7 12 2" /><polyline points="2 17 12 22 22 17" /><polyline points="2 12 12 17 22 12" /></g>,
    shieldCheck: <g><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="m9 12 2 2 4-4" /></g>,
    logOut: <g><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="M16 17l5-5-5-5" /><path d="M21 12H9" /></g>,
    bell: <g><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" /></g>,
    search: <g><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></g>,
    filter: <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />,
    plus: <g><path d="M12 5v14" /><path d="M5 12h14" /></g>,
    hardDrive: <path d="M22 12H2M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11zM6 16h.01M10 16h.01" />,
    x: <g><path d="M18 6L6 18" /><path d="M6 6l12 12" /></g>,
    cloud: <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" />,
    users: <g><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /><path d="M9 7a4 4 0 1 1 0-8 4 4 0 0 1 0 8Z" /></g>,
    network: <g><rect x="16" y="16" width="6" height="6" rx="1" /><rect x="2" y="16" width="6" height="6" rx="1" /><rect x="9" y="2" width="6" height="6" rx="1" /><path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3" /><path d="M12 12V8" /></g>,
    folderTree: <g><path d="M3 7v10a2 2 0 0 0 2 2h14" /><path d="M12 11h6" /><path d="M12 15h6" /><path d="M12 7h6" /><path d="M3 3h3l2 2h6a2 2 0 0 1 2 2v2H3z" /></g>,
    alertTriangle: <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3ZM12 9v4m0 4h.01" />,
    trash2: <g><path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" /><line x1="10" y1="11" x2="10" y2="17" /><line x1="14" y1="11" x2="14" y2="17" /></g>,
    zap: <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />,
    pause: <g><rect x="6" y="4" width="4" height="16" /><rect x="14" y="4" width="4" height="16" /></g>,
    bot: <g><rect x="3" y="11" width="18" height="10" rx="2" /><circle cx="12" cy="5" r="2" /><path d="M12 7v4M8 16h.01M16 16h.01" /></g>,
    camera: <g><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" /><circle cx="12" cy="13" r="3" /></g>,
    edit: <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />,
    send: <path d="m22 2-7 20-4-9-9-4Z" />
  };
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      {icons[name]}
    </svg>
  );
};

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [loginCreds, setLoginCreds] = useState({ username: "", password: "" });
  const [loginError, setLoginError] = useState("");
  
  const [activeView, setActiveView] = useState("dashboard");

  const [vcenters, setVcenters] = useState([]);
  const [selectedVcenter, setSelectedVcenter] = useState(null);
  const [showVcenterModal, setShowVcenterModal] = useState(false);
  const [vcenterForm, setVcenterForm] = useState({ name: "", host: "", username: "", password: "", isEdit: false, oldHost: "" });
  const [loadingVcenters, setLoadingVcenters] = useState(false);
  const [vcenterError, setVcenterError] = useState("");

  const [form, setForm] = useState({
    username: "", password: "", template: "", network: "", cpu: 2, memory: 4, disk: 40, 
    vmCount: 1, namingContext: "", vmOwner: "", startingIp: "", subnet: "255.255.255.0", 
    gateway: "", dns: "208.67.222.222", localAdminPassword: "", host: "", datastore: "", autoPlacement: true,
    ipamSubnetId: "", isEsxi: false
  });

  const [ipamSubnets, setIpamSubnets] = useState([]);
  const [selectedIpamSubnet, setSelectedIpamSubnet] = useState(null);
  const [subnetIps, setSubnetIps] = useState([]);
  const [showSubnetModal, setShowSubnetModal] = useState(false);
  const [subnetForm, setSubnetForm] = useState({ vcenter: "", name: "", cidr: "", gateway: "", vlan: "" });
  const [showIpEditModal, setShowIpEditModal] = useState(false);
  const [editingIp, setEditingIp] = useState(null);

  // New Features State
  const [explorerData, setExplorerData] = useState([]);
  const [loadingExplorer, setLoadingExplorer] = useState(false);
  const [explorerSearch, setExplorerSearch] = useState("");
  const [explorerHostFilter, setExplorerHostFilter] = useState("");
  const [filterVC, setFilterVC] = useState("All");
  const [filterState, setFilterState] = useState("All"); // All, poweredOn, poweredOff
  const [expandedVCs, setExpandedVCs] = useState({});
  const [expandedHosts, setExpandedHosts] = useState({});

  const [thresholdData, setThresholdData] = useState({ datastores: [], hosts: [], vms: [] });
  const [loadingThreshold, setLoadingThreshold] = useState(false);
  const [thresholdSearch, setThresholdSearch] = useState("");
  const [cpuThreshold, setCpuThreshold] = useState(80);
  const [memThreshold, setMemThreshold] = useState(80);
  const [diskThreshold, setDiskThreshold] = useState(80);
  const [thresholdFilters, setThresholdFilters] = useState({ vcenter: "all", host: "all" });
  const [showAlertsModal, setShowAlertsModal] = useState(false);
  const [recentProcesses, setRecentProcesses] = useState([]);

  const [reclamationData, setReclamationData] = useState({ stale: [], zombies: [] });
  const [loadingReclamation, setLoadingReclamation] = useState(false);
  const [reclamationTab, setReclamationTab] = useState("zombies");
  const [staleDays, setStaleDays] = useState(15);
  const [zombieCpu, setZombieCpu] = useState(5);
  const [reclamationSearch, setReclamationSearch] = useState("");

  // Chatbot State
  const [chatSessionId] = useState(() => "sess_" + Math.random().toString(36).substring(2, 9));
  const [chatMessages, setChatMessages] = useState([
    { sender: "bot", text: "Hello! I am your AI Deployment Assistant. Tell me what you want to deploy, e.g.: 'Deploy 2 VMs on vcenter 10.131.33.19 with template win2022-base'." }
  ]);
  const [chatPrompt, setChatPrompt] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatParams, setChatParams] = useState({});
  const [chatReady, setChatReady] = useState(false);

  const [ipMode, setIpMode] = useState("series");
  const [dynamicIps, setDynamicIps] = useState([""]); 
  const [dynamicSubnet, setDynamicSubnet] = useState("255.255.255.0");
  const [dynamicGateway, setDynamicGateway] = useState("");
  const [dynamicDns, setDynamicDns] = useState("208.67.222.222");

  const [inventoryLogs, setInventoryLogs] = useState([]);
  const [loadingInventoryLogs, setLoadingInventoryLogs] = useState(false);
  const [searchTerm, setSearchTerm] = useState(""); 
  const [colFilters, setColFilters] = useState({
    timestamp: "", vmName: "", ipAddress: "", templateName: "", vmOwner: "", vcenter: "", esxiHost: "", provisionedBy: ""
  });
  
  const [liveStats, setLiveStats] = useState([]);
  const [loadingLiveStats, setLoadingLiveStats] = useState(false);
  const [selectedLiveVcenter, setSelectedLiveVcenter] = useState(null);

  const [usersList, setUsersList] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);
  const [userForm, setUserForm] = useState({ id: null, username: "", fullName: "", role: "", password: "", isEdit: false });
  
  const [rolesList, setRolesList] = useState([]);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [roleFormName, setRoleFormName] = useState("");

  const [templates, setTemplates] = useState([]);
  const [networks, setNetworks] = useState([]);
  const [hosts, setHosts] = useState([]);
  const [datastores, setDatastores] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [loadingNetworks, setLoadingNetworks] = useState(false);
  const [loadingHosts, setLoadingHosts] = useState(false);
  const [loadingDatastores, setLoadingDatastores] = useState(false);
  const [inventoryError, setInventoryError] = useState("");

  const [isDeploying, setIsDeploying] = useState(false);
  const [progress, setProgress] = useState(0); 
  const [deploymentMessage, setDeploymentMessage] = useState("");
  const [deploymentError, setDeploymentError] = useState("");

  useEffect(() => {
    let interval;
    if (isDeploying) {
      setProgress(0);
      interval = setInterval(() => { setProgress((prev) => (prev >= 95 ? 95 : prev + Math.max(0.1, (95 - prev) / 40))); }, 500);
    } else { setProgress(100); }
    return () => clearInterval(interval);
  }, [isDeploying]);

  useEffect(() => { 
    if (currentUser) {
      loadVcenters(); 
      fetchIpamSubnets();
      fetchLiveStats();
      fetchInventoryLogs();
      fetchUsers();
      fetchRoles();
    }
  }, [currentUser]);

  useEffect(() => {
    if (activeView === "vmware_explorer") fetchExplorerData();
    else if (activeView === "threshold_director") {
      fetchThresholdData();
      const interval = setInterval(fetchThresholdData, 300000);
      return () => clearInterval(interval);
    }
    else if (activeView === "resource_reclamation") fetchReclamationData();
  }, [activeView, cpuThreshold, memThreshold, diskThreshold]);

  useEffect(() => {
    const count = parseInt(form.vmCount) || 1;
    setDynamicIps(prev => {
      const newIps = [...prev];
      while (newIps.length < count) newIps.push("");
      if (newIps.length > count) newIps.length = count;
      return newIps;
    });
  }, [form.vmCount]);

  const handleDynamicIpChange = (index, value) => {
    const newIps = [...dynamicIps];
    newIps[index] = value;
    setDynamicIps(newIps);
  };

  const getIncrementedIp = (baseIp, increment) => {
    try {
      const parts = baseIp.split(".");
      if (parts.length !== 4) return baseIp;
      parts[3] = String(parseInt(parts[3], 10) + increment);
      return parts.join(".");
    } catch {
      return baseIp;
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError("");
    try {
      const response = await fetch(`${API_BASE}/login`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loginCreds)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Login Failed");
      setCurrentUser(data.user);
      setLoginCreds({ username: "", password: "" });
    } catch (err) {
      setLoginError(err.message);
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setActiveView("dashboard");
  };

  if (!currentUser) {
    return (
      <div className="bg-dark-900 text-gray-100 min-h-screen flex flex-col antialiased font-sans selection:bg-brand selection:text-white">
        <div className="flex-1 flex items-center justify-center p-4 relative overflow-hidden">
            <div className="absolute -top-40 -left-40 w-96 h-96 bg-brand/20 rounded-full blur-3xl pointer-events-none"></div>
            <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl pointer-events-none"></div>

            <div className="w-full max-w-md bg-dark-800/80 backdrop-blur-xl border border-gray-800 p-8 rounded-2xl shadow-2xl relative z-10">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-14 h-14 bg-brand/10 border border-brand/30 rounded-xl mb-4 text-blue-400">
                        <Icon name="server" className="w-7 h-7" />
                    </div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">Global Labs VM Studio</h1>
                    <p className="text-sm text-gray-400 mt-1">Enterprise Virtualization Management</p>
                </div>

                {loginError && <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg text-sm text-center">{loginError}</div>}

                <form onSubmit={handleLogin} className="space-y-5">
                    <div>
                        <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">Username</label>
                        <div className="relative">
                            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                                <Icon name="mail" />
                            </span>
                            <input type="text" value={loginCreds.username} onChange={e => setLoginCreds({...loginCreds, username: e.target.value})} required autoFocus
                                className="w-full pl-10 pr-4 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-all" />
                        </div>
                    </div>

                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400">Password</label>
                        </div>
                        <div className="relative">
                            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                                <Icon name="lock" />
                            </span>
                            <input type="password" value={loginCreds.password} onChange={e => setLoginCreds({...loginCreds, password: e.target.value})} required 
                                className="w-full pl-10 pr-4 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-all" />
                        </div>
                    </div>

                    <button type="submit" className="w-full py-3 bg-brand hover:bg-brand-hover text-white font-medium rounded-lg shadow-lg shadow-brand/30 transition-all flex items-center justify-center gap-2">
                        <span>Authenticate & Access Portal</span>
                        <Icon name="arrowRight" />
                    </button>
                </form>

                <div className="mt-6 pt-6 border-t border-gray-800 text-center text-xs text-gray-500">
                    Secure 256-bit TLS Encryption • Node: US-East-Cluster-01
                </div>
            </div>
        </div>
      </div>
    );
  }

  // --- API / Logic Functions ---
  const fetchExplorerData = async () => {
    setLoadingExplorer(true);
    try {
      const res = await fetch(`${API_BASE}/explorer`);
      const data = await res.json();
      setExplorerData(data.explorer || []);
    } catch (err) { console.error(err); }
    setLoadingExplorer(false);
  };

  const fetchThresholdData = async () => {
    setLoadingThreshold(true);
    try {
      const res = await fetch(`${API_BASE}/thresholds?cpu=${cpuThreshold}&mem=${memThreshold}&disk=${diskThreshold}`);
      setThresholdData(await res.json());
    } catch (err) { console.error(err); }
    setLoadingThreshold(false);
  };

  const fetchReclamationData = async () => {
    setLoadingReclamation(true);
    try {
      const res = await fetch(`${API_BASE}/reclamation?days=${staleDays}&cpu=${zombieCpu}`);
      setReclamationData(await res.json());
    } catch (err) { console.error(err); }
    setLoadingReclamation(false);
  };

  const handleVmAction = async (vcHost, vmName, action) => {
    if (!window.confirm(`Execute ${action} on ${vmName}?`)) return;
    try {
      const res = await fetch(`${API_BASE}/explorer/vm/action`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vcenter: vcHost, vm_name: vmName, action })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      alert(`Success: ${data.message}`);
      fetchExplorerData();
    } catch (err) { alert(`Action failed: ${err.message}`); }
  };

  const handleVmManage = async (vcHost, vmName, action, params = {}) => {
    try {
      const res = await fetch(`${API_BASE}/explorer/vm/manage`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vcenter: vcHost, vm_name: vmName, action, ...params })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      alert(`Success: ${data.message}`);
      fetchExplorerData();
    } catch (err) { alert(`Action failed: ${err.message}`); }
  };

  const sendChatMessage = async (overridePrompt) => {
    const textToSend = overridePrompt !== undefined ? overridePrompt : chatPrompt;
    if (!textToSend.trim()) return;
    const userMsg = { sender: "user", text: textToSend };
    setChatMessages(prev => [...prev, userMsg]);
    setChatPrompt("");
    setChatLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chatbot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: chatSessionId, prompt: textToSend })
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, { sender: "bot", text: data.reply, ready: data.ready, payload: data.payload }]);
      if (data.params) setChatParams(data.params);
      if (data.payload) {
        setChatParams(data.payload);
        setChatReady(true);
      } else {
        setChatReady(false);
      }
    } catch (err) {
      setChatMessages(prev => [...prev, { sender: "bot", text: `Error connecting to chatbot: ${err.message}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  const applyChatbotToDeploy = (payload) => {
    if (!payload) return;
    setForm(prev => ({
      ...prev,
      vmCount: payload.vmCount || prev.vmCount,
      template: payload.template || prev.template,
      vcenter: payload.vcenter || prev.vcenter
    }));
    if (payload.vcenter) {
      const vcObj = vcenters.find(v => v.host === payload.vcenter || v.name === payload.vcenter);
      if (vcObj) setSelectedVcenter(vcObj);
    }
    setActiveView("vm_studio");
  };

  const fetchIpamSubnets = async () => {
    try {
      const response = await fetch(`${API_BASE}/ipam/subnets`);
      const data = await response.json();
      setIpamSubnets(Array.isArray(data) ? data : []);
    } catch (err) { console.error("Failed to load IPAM subnets"); }
  };

  const loadVcenters = async () => {
    setLoadingVcenters(true); setVcenterError("");
    try {
      const response = await fetch(`${API_BASE}/vcenters`);
      const data = await response.json();
      setVcenters(Array.isArray(data) ? data : []);
    } catch (error) { setVcenterError("Backend offline. Verify app.py status."); } 
    finally { setLoadingVcenters(false); }
  };

  const fetchInventoryLogs = async () => {
    setLoadingInventoryLogs(true);
    try {
      const response = await fetch(`${API_BASE}/inventory`, { cache: "no-store" });
      const data = await response.json();
      setInventoryLogs(Array.isArray(data.inventory) ? data.inventory : []);
    } catch (error) { console.error("Failed inventory load", error); } 
    finally { setLoadingInventoryLogs(false); }
  };

  const fetchLiveStats = async () => {
    setLoadingLiveStats(true);
    try {
      const response = await fetch(`${API_BASE}/dashboard/live`, { cache: "no-store" });
      const data = await response.json();
      if (response.ok && Array.isArray(data.live)) setLiveStats(data.live);
    } catch (error) { console.error("Failed telemetry load", error); } 
    finally { setLoadingLiveStats(false); }
  };

  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      const response = await fetch(`${API_BASE}/users`, { cache: "no-store" });
      const data = await response.json();
      setUsersList(Array.isArray(data) ? data : []);
    } catch (error) { console.error("Failed users load", error); } 
    finally { setLoadingUsers(false); }
  };

  const fetchRoles = async () => {
    try {
      const response = await fetch(`${API_BASE}/roles`, { cache: "no-store" });
      const data = await response.json();
      setRolesList(Array.isArray(data) ? data : []);
    } catch (error) { console.error("Failed roles load", error); }
  };

  const saveVcenterConfig = async (event) => {
    event.preventDefault();
    const { name, host, username, password, isEdit, oldHost } = vcenterForm;
    if (!name || !host || !username) return alert("All node parameters required.");
    try {
      const url = isEdit ? `${API_BASE}/vcenters/${encodeURIComponent(oldHost)}` : `${API_BASE}/vcenters`;
      const method = isEdit ? "PUT" : "POST";
      const response = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name, host, username, password }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Operation failed.");
      await loadVcenters(); setShowVcenterModal(false);
      if (selectedVcenter && selectedVcenter.host === oldHost) { setSelectedVcenter(data); setForm((prev) => ({ ...prev, username: data.username })); }
    } catch (error) { alert(error.message); }
  };

  const removeVcenter = async (host) => {
    if (!window.confirm(`Purge cluster endpoint ${host}?`)) return;
    try {
      const response = await fetch(`${API_BASE}/vcenters/${encodeURIComponent(host)}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Purge failed.");
      await loadVcenters();
      if (selectedVcenter && selectedVcenter.host === host) { setSelectedVcenter(null); clearInventory(); setForm((prev) => ({ ...prev, username: "", password: "" })); }
    } catch (error) { alert(error.message); }
  };

  const saveUserConfig = async (event) => {
    event.preventDefault();
    const { id, username, fullName, role, password, isEdit } = userForm;
    if (!username || !fullName) return alert("Credentials incomplete.");
    if (!isEdit && !password) return alert("Password mandatory.");

    try {
      const url = isEdit ? `${API_BASE}/users/${id}` : `${API_BASE}/users`;
      const method = isEdit ? "PUT" : "POST";
      const response = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username, fullName, role, password }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "User operation failed.");
      await fetchUsers(); setShowUserModal(false);
    } catch (error) { alert(error.message); }
  };

  const removeUser = async (id, username) => {
    if (!window.confirm(`Revoke profile ${username}?`)) return;
    try {
      const response = await fetch(`${API_BASE}/users/${id}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Revocation failed.");
      await fetchUsers();
    } catch (error) { alert(error.message); }
  };

  const saveRoleConfig = async (event) => {
    event.preventDefault();
    if (!roleFormName) return alert("Role title required.");
    try {
      const response = await fetch(`${API_BASE}/roles`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: roleFormName }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Role creation failed.");
      await fetchRoles(); setShowRoleModal(false); setRoleFormName("");
    } catch (error) { alert(error.message); }
  };

  const removeRole = async (id, name) => {
    if (!window.confirm(`Delete privilege group ${name}?`)) return;
    try {
      const response = await fetch(`${API_BASE}/roles/${id}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Deletion failed.");
      await fetchRoles();
    } catch (error) { alert(error.message); }
  };

  const updateForm = (field, value) => { setForm((prev) => ({ ...prev, [field]: value })); };
  const clearInventory = () => {
    setTemplates([]); setNetworks([]); setHosts([]); setDatastores([]);
    setForm((prev) => ({ ...prev, template: "", network: "", host: "", datastore: "", autoPlacement: true }));
  };

  const handleVcenterChange = (event) => {
    const host = event.target.value;
    const vc = vcenters.find((item) => String(item.host).toLowerCase() === String(host).toLowerCase());
    setSelectedVcenter(vc || null);
    setInventoryError(""); setDeploymentError(""); setDeploymentMessage(""); setProgress(0);
    clearInventory();
    setForm((prev) => ({ ...prev, username: vc?.username || "", password: "" }));
  };

  const loadInventory = async () => {
    if (!selectedVcenter) return setInventoryError("Select target vCenter endpoint first.");
    if (!form.password && !selectedVcenter.hasPassword) return setInventoryError("Vault password verification required.");

    setInventoryError(""); setDeploymentError(""); setDeploymentMessage("");
    setLoadingTemplates(true); setLoadingNetworks(true); setLoadingHosts(true); setLoadingDatastores(true);
    clearInventory();

    const credentials = { host: selectedVcenter.host, username: selectedVcenter.username, password: form.password };
    try {
      const [templateRes, networkRes, hostRes, datastoreRes] = await Promise.all([
        fetch(`${API_BASE}/vcenters/templates`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(credentials) }),
        fetch(`${API_BASE}/vcenters/networks`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(credentials) }),
        fetch(`${API_BASE}/vcenters/hosts`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(credentials) }),
        fetch(`${API_BASE}/vcenters/datastores`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(credentials) }),
      ]);
      const templateData = await templateRes.json(); const networkData = await networkRes.json();
      const hostData = await hostRes.json(); const datastoreData = await datastoreRes.json();

      if (!templateRes.ok) throw new Error(templateData.error || "Template discovery failure.");
      if (!networkRes.ok) throw new Error(networkData.error || "Network discovery failure.");

      setTemplates(Array.isArray(templateData.templates) ? templateData.templates : []);
      setNetworks(Array.isArray(networkData.networks) ? networkData.networks : []);
      setHosts(Array.isArray(hostData.hosts) ? hostData.hosts : []);
      setDatastores(Array.isArray(datastoreData.datastores) ? datastoreData.datastores : []);
    } catch (error) { setInventoryError(error.message); } 
    finally { setLoadingTemplates(false); setLoadingNetworks(false); setLoadingHosts(false); setLoadingDatastores(false); }
  };

  const startDeployment = async () => {
    setDeploymentError(""); setDeploymentMessage("");
    if (!selectedVcenter) return setDeploymentError("Select an operational cluster.");
    if (!form.password && !selectedVcenter.hasPassword) return setDeploymentError("Authentication key mandatory.");
    if (!form.template || !form.network) return setDeploymentError("Template and network parameters required.");
    if (!form.localAdminPassword) return setDeploymentError("Guest OS administrator password mandatory.");

    if (ipMode === "dynamic") {
      const emptyIps = dynamicIps.filter(ip => !ip.trim());
      if (emptyIps.length > 0) return setDeploymentError("Please provide an IP address for every manual node.");
    }
    if (ipMode === "ipam") {
      if (!form.ipamSubnetId) return setDeploymentError("Please select an onboarded IPAM subnet.");
    }

    const deploymentConfiguration = { 
      ...form, 
      is_esxi: form.isEsxi || false,
      host: form.autoPlacement ? "" : form.host,
      datastore: form.autoPlacement ? "" : form.datastore,
      vcenter: selectedVcenter.host, 
      ipMode, 
      ipamSubnetId: form.ipamSubnetId,
      startingIp: ipMode === "series" ? form.startingIp : undefined,
      ipList: ipMode === "dynamic" ? dynamicIps : undefined,
      subnet: ipMode === "series" ? form.subnet : dynamicSubnet,
      gateway: ipMode === "series" ? form.gateway : dynamicGateway,
      dns: ipMode === "series" ? form.dns : (ipMode === "dynamic" ? dynamicDns : form.dns)
    };
    
    setIsDeploying(true); setDeploymentMessage("");

    try {
      const response = await fetch(`${API_BASE}/deploy`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(deploymentConfiguration) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Deployment pipeline failed.");

      setProgress(100);
      setTimeout(() => {
        if (data.failed && data.failed.length > 0) setDeploymentError(`Partial completion. ${data.successful.length} built, ${data.failed.length} aborted.`);
        else setDeploymentMessage(`Pipeline Complete! ${data.successful.length} Autonomous Virtual Node(s) active.`);
        setIsDeploying(false); fetchInventoryLogs();
      }, 800);
    } catch (error) { setProgress(100); setTimeout(() => { setDeploymentError(error.message); setIsDeploying(false); }, 800); }
  };

  const filteredLogs = inventoryLogs.filter((log) => {
    const term = searchTerm.toLowerCase();
    const matchesSearch = !term || (
      (log.vmName || log.vmname || "").toLowerCase().includes(term) ||
      (log.ipAddress || log.ipaddress || "").toLowerCase().includes(term) ||
      (log.vmOwner || log.vmowner || "").toLowerCase().includes(term) ||
      (log.templateName || log.templatename || "").toLowerCase().includes(term) ||
      (log.provisionedBy || log.provisionedby || "").toLowerCase().includes(term)
    );
    if (!matchesSearch) return false;
    const matchCol = (val, filter) => !filter || String(val || "").toLowerCase().includes(filter.toLowerCase());
    
    if (!matchCol(log.timestamp, colFilters.timestamp)) return false;
    if (!matchCol(log.vmName || log.vmname, colFilters.vmName)) return false;
    if (!matchCol(log.ipAddress || log.ipaddress, colFilters.ipAddress)) return false;
    if (!matchCol(log.templateName || log.templatename, colFilters.templateName)) return false;
    if (!matchCol(log.vmOwner || log.vmowner, colFilters.vmOwner)) return false;
    if (!matchCol(log.vcenter, colFilters.vcenter)) return false;
    if (!matchCol(log.esxiHost || log.esxihost, colFilters.esxiHost)) return false;
    if (!matchCol(log.provisionedBy || log.provisionedby, colFilters.provisionedBy)) return false;

    return true;
  });

  const downloadCSV = () => {
    const headers = [ "Timestamp", "VM Name", "IP Address", "Template", "vCenter", "ESXi Host / IP", "Owner", "Provisioned By" ];
    const rows = filteredLogs.map(row => [
      `"${row.timestamp || ""}"`, `"${row.vmName || row.vmname || ""}"`, `"${row.ipAddress || row.ipaddress || ""}"`, `"${row.templateName || row.templatename || ""}"`, `"${row.vcenter || ""}"`, `"${row.esxiHost || row.esxihost || ""}"`, 
      `"${row.vmOwner || row.vmowner || ""}"`, `"${row.provisionedBy || row.provisionedby || ""}"`
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a"); link.setAttribute("href", encodedUri); link.setAttribute("download", `VM_Inventory_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link); link.click(); document.body.removeChild(link);
  };

  const totalVMs = inventoryLogs.length;
  const totalCPU = inventoryLogs.reduce((acc, log) => acc + Number(log.cpu || 0), 0);
  const totalRAM = inventoryLogs.reduce((acc, log) => acc + Number(log.memoryGb || log.memorygb || 0), 0);
  const disconnectedHosts = liveStats.reduce((acc, vc) => acc + (vc.hosts ? (Number(vc.hosts.total || 0) - Number(vc.hosts.connected || 0)) : 0), 0);
  const fullDatastoresCount = liveStats.filter(vc => vc.storage && (Number(vc.storage.used || 0) / Math.max(1, Number(vc.storage.tot || 1))) > 0.90).length;
  const formatPercentage = (used, tot) => (tot > 0 ? ((Number(used) / Number(tot)) * 100).toFixed(1) : 0);
  const getBarColor = (percent) => (percent > 90 ? "#ef4444" : percent > 75 ? "#f59e0b" : "#3b82f6");
  const inventoryLoading = loadingTemplates || loadingNetworks || loadingHosts || loadingDatastores;

  // --- Rendering Helpers ---
  const NavButton = ({ id, icon, label }) => (
    <button onClick={() => setActiveView(id)} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${activeView === id || (id === 'dashboard' && activeView === 'infrastructure_details') ? 'bg-brand/10 text-blue-400 border border-brand/20' : 'text-gray-300 hover:bg-dark-700/60 hover:text-white'}`}>
        <Icon name={icon} className="w-4 h-4" />
        <span>{label}</span>
    </button>
  );

  return (
    <div className="bg-dark-900 text-gray-100 min-h-screen flex flex-col antialiased font-sans selection:bg-brand selection:text-white">
      <div className="flex-1 flex">
        
        {/* SIDEBAR */}
        <aside className="w-64 bg-dark-800 border-r border-gray-800 flex flex-col z-20">
            <div className="p-5 border-b border-gray-800 flex items-center gap-3">
                <div className="w-9 h-9 bg-brand/20 border border-brand/40 rounded-lg flex items-center justify-center text-blue-400 font-bold">
                    <Icon name="cpu" className="w-5 h-5" />
                </div>
                <div>
                    <h2 className="font-bold text-sm text-white tracking-wide">Global Labs</h2>
                    <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">VM Studio</span>
                </div>
            </div>

            <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                <p className="px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2">Virtual Machines</p>
                <NavButton id="dashboard" icon="layoutDashboard" label="Dashboard" />
                <NavButton id="vm_studio" icon="plusCircle" label="VM Studio" />
                <NavButton id="chatbot" icon="bot" label="Deploy Assistant" />
                <NavButton id="ipam" icon="network" label="IPAM / DNS" />
                <NavButton id="inventory" icon="layers" label="Inventory Logs" />
                <NavButton id="vcenters" icon="cloud" label="vCenters" />
                <NavButton id="vmware_explorer" icon="folderTree" label="VMware Explorer" />
                <NavButton id="threshold_director" icon="alertTriangle" label="Threshold Director" />
                <NavButton id="resource_reclamation" icon="trash2" label="Resource Reclamation" />

                {currentUser?.role === "Admin" && (
                  <>
                    <p className="px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider mt-6 mb-2">Administration</p>
                    <NavButton id="users" icon="shieldCheck" label="Access & Security" />
                  </>
                )}
            </nav>

            <div className="p-4 border-t border-gray-800 space-y-3">
                {/* Sidebar Footer Alert Click Handler */}
                <div 
                  className="p-2.5 rounded-lg bg-dark-900 border border-gray-700/60 hover:border-amber-500/50 hover:bg-amber-500/5 transition-all cursor-pointer flex items-center gap-3 group" 
                  onClick={() => setShowAlertsModal(true)}
                  title="Click to view infrastructure alerts and active processes"
                >
                  <div className="relative flex items-center justify-center">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse"></span>
                    <span className="absolute w-2.5 h-2.5 rounded-full bg-amber-400 opacity-75"></span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-gray-200 group-hover:text-amber-400 flex items-center justify-between">
                      <span>System Alerts</span>
                      {disconnectedHosts > 0 && (
                        <span className="text-[10px] bg-red-500/20 text-red-400 px-1.5 py-0.2 rounded font-semibold border border-red-500/30">
                          {disconnectedHosts} Offline
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-gray-500 block truncate">Click to view active processes</span>
                  </div>
                </div>

                <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-semibold text-xs">
                            {currentUser?.fullName?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        <div className="overflow-hidden">
                            <p className="text-xs font-medium text-white truncate">{currentUser?.fullName}</p>
                            <p className="text-[10px] text-gray-400 truncate">{currentUser?.role}</p>
                        </div>
                    </div>
                </div>
                <button onClick={handleLogout} className="w-full flex items-center justify-center gap-2 py-2 bg-dark-700 hover:bg-red-500/20 hover:text-red-400 text-gray-300 rounded-lg text-xs font-medium transition-all border border-gray-700 hover:border-red-500/30">
                    <Icon name="logOut" className="w-3.5 h-3.5" />
                    <span>Sign Out</span>
                </button>
            </div>
        </aside>

        {/* MAIN CONTENT */}
        <div className="flex-1 flex flex-col min-w-0 bg-dark-900">
            
            {/* TOP HEADER */}
            <header className="h-16 bg-dark-800/50 backdrop-blur border-b border-gray-800 px-6 flex items-center justify-between sticky top-0 z-10">
                <div className="flex items-center gap-4">
                    <div className="text-sm font-semibold text-white tracking-wide uppercase">
                      {activeView === 'dashboard' && 'Dashboard'}
                      {activeView === 'infrastructure_details' && 'Infrastructure Monitor'}
                      {activeView === 'vm_studio' && 'VM Studio'}
                      {activeView === 'chatbot' && 'AI Deployment Assistant'}
                      {activeView === 'ipam' && 'IP Address Management'}
                      {activeView === 'inventory' && 'Historical Logs'}
                      {activeView === 'vcenters' && 'vCenters'}
                      {activeView === 'users' && 'Access & Security'}
                      {activeView === 'vmware_explorer' && 'VMware Explorer'}
                      {activeView === 'threshold_director' && 'Threshold Director'}
                      {activeView === 'resource_reclamation' && 'Resource Reclamation'}
                    </div>
                    <span className="text-xs bg-dark-700 text-gray-300 px-2.5 py-1 rounded-md border border-gray-700 hidden sm:inline-block">System Operational</span>
                </div>
                
                <div className="flex items-center gap-3">
                    <button onClick={() => setShowAlertsModal(true)} title="System Alerts" className="p-2 text-gray-400 hover:text-white bg-dark-700/50 hover:bg-dark-700 rounded-lg border border-gray-700 transition-all relative">
                        <Icon name="bell" />
                        {(disconnectedHosts > 0 || fullDatastoresCount > 0) && <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>}
                    </button>
                    <div className="h-5 w-px bg-gray-800"></div>
                    <div className="flex items-center gap-2 text-xs text-gray-300">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
                        <span>Connected</span>
                    </div>
                </div>
            </header>

            {/* SCROLLABLE VIEWPORT */}
            <main className="flex-1 p-6 overflow-y-auto">

              {/* ================= DASHBOARD ================= */}
              {activeView === "dashboard" && (
                <div className="space-y-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div>
                            <h2 className="text-xl font-bold text-white tracking-tight">Dashboard</h2>
                            <p className="text-sm text-gray-400">Monitor active workloads, statuses, and performance specs.</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <button onClick={() => { fetchLiveStats(); fetchInventoryLogs(); }} className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-gray-300 text-xs font-semibold rounded-lg border border-gray-700 transition-all flex items-center gap-2">
                                <span>↻ Refresh</span>
                            </button>
                            {currentUser.role !== "Viewer" && (
                              <button onClick={() => setActiveView('vm_studio')} className="px-4 py-2 bg-brand hover:bg-brand-hover text-white text-xs font-semibold rounded-lg shadow-lg shadow-brand/20 transition-all flex items-center gap-2">
                                  <Icon name="plus" />
                                  <span>Deploy New VM</span>
                              </button>
                            )}
                        </div>
                    </div>

                    {(disconnectedHosts > 0 || fullDatastoresCount > 0) && (
                      <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex gap-4">
                        <div className="text-amber-400"><Icon name="activity" className="w-6 h-6" /></div>
                        <div>
                          <h4 className="text-sm font-bold text-amber-400">Infrastructure Alerts</h4>
                          <ul className="text-xs text-gray-300 mt-1 list-disc pl-4">
                            {disconnectedHosts > 0 && <li>{disconnectedHosts} ESXi host(s) disconnected.</li>}
                            {fullDatastoresCount > 0 && <li>{fullDatastoresCount} datastore(s) exceeding 90% capacity.</li>}
                          </ul>
                        </div>
                      </div>
                    )}

                    {/* Stats Row */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="bg-dark-800/80 border border-gray-800 p-5 rounded-xl shadow-lg">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-gray-400">Total Provisioned VMs</span>
                                <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg border border-blue-500/20"><Icon name="server" /></div>
                            </div>
                            <div className="mt-4 flex items-baseline justify-between">
                                <span className="text-2xl font-bold text-white">{totalVMs}</span>
                                <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Active</span>
                            </div>
                        </div>
                        <div className="bg-dark-800/80 border border-gray-800 p-5 rounded-xl shadow-lg">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-gray-400">Allocated vCPUs</span>
                                <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg border border-purple-500/20"><Icon name="cpu" /></div>
                            </div>
                            <div className="mt-4 flex items-baseline justify-between">
                                <span className="text-2xl font-bold text-white">{totalCPU} Cores</span>
                            </div>
                        </div>
                        <div className="bg-dark-800/80 border border-gray-800 p-5 rounded-xl shadow-lg">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-gray-400">Total RAM Allocated</span>
                                <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20"><Icon name="hardDrive" /></div>
                            </div>
                            <div className="mt-4 flex items-baseline justify-between">
                                <span className="text-2xl font-bold text-white">{totalRAM} GB</span>
                            </div>
                        </div>
                        <div className="bg-dark-800/80 border border-gray-800 p-5 rounded-xl shadow-lg">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-gray-400">Cloud Endpoints</span>
                                <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg border border-amber-500/20"><Icon name="cloud" /></div>
                            </div>
                            <div className="mt-4 flex items-baseline justify-between">
                                <span className="text-2xl font-bold text-white">{vcenters.length}</span>
                                <span className="text-xs text-blue-400">Linked</span>
                            </div>
                        </div>
                    </div>

                    {/* Live Cluster Status Cards */}
                    <h3 className="text-sm font-bold text-gray-300 mt-8 mb-4 uppercase tracking-wider">Live Cluster Health</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                      {loadingLiveStats ? (
                        <div className="col-span-full py-8 text-center text-sm text-gray-500">Polling vCenter Endpoints...</div>
                      ) : liveStats.length === 0 ? (
                        <div className="col-span-full py-8 text-center text-sm text-gray-500 bg-dark-800/50 rounded-xl border border-gray-800">No active clusters registered.</div>
                      ) : (
                        liveStats.map((stat, i) => (
                          <div key={i} onClick={() => { setSelectedLiveVcenter(stat); setActiveView("infrastructure_details"); }} 
                               className="bg-dark-800/80 border border-gray-800 p-5 rounded-xl shadow-lg cursor-pointer hover:border-brand/50 hover:bg-dark-800 transition-all group">
                            
                            <div className="flex justify-between items-start mb-4 border-b border-gray-800/80 pb-3">
                              <div>
                                <h4 className="font-bold text-gray-100">{stat.name || stat.host}</h4>
                                <span className="text-xs text-gray-500">{stat.host}</span>
                              </div>
                              <span className={`text-[10px] px-2 py-0.5 rounded border font-semibold ${stat.error ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'}`}>
                                {stat.status}
                              </span>
                            </div>

                            {!stat.error ? (
                              <div className="space-y-4">
                                <div className="grid grid-cols-3 gap-2 bg-dark-900 p-3 rounded-lg border border-gray-800">
                                  <div className="text-center"><div className="text-lg font-bold text-emerald-400">{stat.vms?.on || 0}</div><div className="text-[9px] font-bold text-gray-500 uppercase tracking-wide">Online</div></div>
                                  <div className="text-center"><div className="text-lg font-bold text-red-400">{stat.vms?.off || 0}</div><div className="text-[9px] font-bold text-gray-500 uppercase tracking-wide">Offline</div></div>
                                  <div className="text-center"><div className="text-lg font-bold text-amber-400">{stat.vms?.susp || 0}</div><div className="text-[9px] font-bold text-gray-500 uppercase tracking-wide">Suspended</div></div>
                                </div>

                                <div>
                                  <div className="flex justify-between text-xs font-semibold text-gray-400 mb-1"><span>CPU Usage</span><span>{formatPercentage(stat.compute?.cpu_used, stat.compute?.cpu_tot)}%</span></div>
                                  <div className="w-full bg-dark-900 h-1.5 rounded-full overflow-hidden"><div className="h-full bg-blue-500" style={{width: `${formatPercentage(stat.compute?.cpu_used, stat.compute?.cpu_tot)}%`}}></div></div>
                                </div>
                                <div>
                                  <div className="flex justify-between text-xs font-semibold text-gray-400 mb-1"><span>RAM Usage</span><span>{formatPercentage(stat.compute?.mem_used, stat.compute?.mem_tot)}%</span></div>
                                  <div className="w-full bg-dark-900 h-1.5 rounded-full overflow-hidden"><div className="h-full bg-purple-500" style={{width: `${formatPercentage(stat.compute?.mem_used, stat.compute?.mem_tot)}%`}}></div></div>
                                </div>

                                {/* Datastores Live Metrics */}
                                <div className="space-y-1.5 pt-2 border-t border-gray-800/60">
                                  <div className="flex justify-between items-center text-[11px] font-semibold text-gray-400">
                                    <span>Datastores</span>
                                    <span className="text-[10px] text-gray-500">{stat.datastores?.details?.length || 0} Volumes</span>
                                  </div>
                                  {stat.datastores?.details?.length > 0 ? (
                                    <div className="space-y-1.5 max-h-24 overflow-y-auto pr-1">
                                      {stat.datastores.details.map(ds => {
                                        const cap = Number(ds.capacity || 0);
                                        const used = Number(ds.used || 0);
                                        const free = Number(ds.free || 0);
                                        const pct = cap > 0 ? Math.min(100, Math.max(0, (used / cap) * 100)) : 0;
                                        return (
                                          <div key={ds.name} className="text-xs space-y-1 bg-dark-900/60 p-1.5 rounded border border-gray-800">
                                            <div className="flex justify-between items-center text-[10px]">
                                              <span className="font-medium text-gray-200 truncate max-w-[120px]">{ds.name}</span>
                                              <span className="text-gray-400 font-mono">{free.toFixed(1)} GB Free / {cap.toFixed(1)} GB</span>
                                            </div>
                                            <div className="w-full bg-dark-950 h-1.5 rounded-full overflow-hidden">
                                              <div 
                                                className="h-full transition-all" 
                                                style={{ width: `${pct}%`, backgroundColor: getBarColor(pct) }}
                                              />
                                            </div>
                                          </div>
                                        );
                                      })}
                                    </div>
                                  ) : (
                                    <span className="text-[10px] text-gray-500 italic">No datastore metrics available</span>
                                  )}
                                </div>
                                
                                <div className="pt-2 border-t border-gray-800/80 flex justify-between items-center text-xs text-gray-400">
                                  <span>Hosts: <span className="font-bold text-gray-200">{stat.hosts?.connected || 0} / {stat.hosts?.total || 0}</span></span>
                                  <span className="text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">Details <Icon name="arrowRight" className="w-3 h-3"/></span>
                                </div>
                              </div>
                            ) : (
                              <div className="py-4 text-xs text-gray-500">Connection failed. Check credentials in Endpoints.</div>
                            )}
                          </div>
                        ))
                      )}
                    </div>

                    {/* VM Table Card */}
                    <div className="bg-dark-800/80 border border-gray-800 rounded-xl overflow-hidden shadow-xl mt-8">
                        <div className="p-4 border-b border-gray-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                            <h3 className="text-sm font-bold text-white">Recent Deployments</h3>
                            <div className="relative flex-1 max-w-sm">
                                <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500"><Icon name="search" /></span>
                                <input type="text" placeholder="Search logs..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} 
                                  className="w-full pl-9 pr-4 py-2 bg-dark-900 border border-gray-700 rounded-lg text-xs text-gray-200 focus:outline-none focus:border-brand transition-all" />
                            </div>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="border-b border-gray-800 bg-dark-900/50 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                                        <th className="py-3 px-4">VM Name</th>
                                        <th className="py-3 px-4">IP Address</th>
                                        <th className="py-3 px-4">Owner</th>
                                        <th className="py-3 px-4">Template</th>
                                        <th className="py-3 px-4">Date</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-800 text-xs text-gray-300">
                                  {filteredLogs.length === 0 ? (
                                    <tr><td colSpan="5" className="py-8 text-center text-gray-500">No records found.</td></tr>
                                  ) : (
                                    filteredLogs.slice(0, 5).map((log, i) => (
                                      <tr key={i} className="hover:bg-dark-700/30 transition-colors">
                                          <td className="py-3 px-4 font-semibold text-blue-400">{log.vmName || log.vmname}</td>
                                          <td className="py-3 px-4">{log.ipAddress || log.ipaddress || "N/A"}</td>
                                          <td className="py-3 px-4">{log.vmOwner || log.vmowner}</td>
                                          <td className="py-3 px-4">{log.templateName || log.templatename || "Unknown"}</td>
                                          <td className="py-3 px-4 text-gray-500">{String(log.timestamp || "").split(" ")[0]}</td>
                                      </tr>
                                    ))
                                  )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
              )}

              {/* ================= IPAM (IP Address Management) ================= */}
              {activeView === "ipam" && (() => {
                const groupedSubnets = ipamSubnets.reduce((acc, subnet) => {
                  const vcKey = subnet.vcenter || "Unassigned";
                  acc[vcKey] = acc[vcKey] || [];
                  acc[vcKey].push(subnet);
                  return acc;
                }, {});

                return (
                  <div className="space-y-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div>
                        <h2 className="text-xl font-bold text-white tracking-tight">IP Address Management</h2>
                        <p className="text-sm text-gray-400">Automated subnet tracking and capacity planning.</p>
                      </div>
                      <div className="flex gap-2">
                        <button onClick={fetchIpamSubnets} className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-gray-300 text-xs font-semibold rounded-lg border border-gray-700 transition-all">↻ Refresh</button>
                        <button onClick={() => { setSubnetForm({vcenter: vcenters[0]?.host||"", name: "", cidr: "", gateway: "", vlan: ""}); setShowSubnetModal(true); }} className="px-4 py-2 bg-brand hover:bg-brand-hover text-white text-xs font-semibold rounded-lg transition-all flex items-center gap-2">
                          <Icon name="plus" /><span>Onboard Subnet</span>
                        </button>
                      </div>
                    </div>

                    {!selectedIpamSubnet ? (
                      <div className="space-y-6">
                        {Object.keys(groupedSubnets).length === 0 ? (
                          <div className="col-span-full py-12 text-center text-sm text-gray-500 bg-[#111827]/80 rounded-xl border border-gray-800">No subnets onboarded.</div>
                        ) : (
                          Object.entries(groupedSubnets).map(([vcHost, subnetsList]) => (
                            <div key={vcHost} className="bg-[#111827]/80 border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
                              <div className="flex items-center justify-between border-b border-gray-800 pb-3">
                                <div className="flex items-center gap-3">
                                  <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg border border-blue-500/20">
                                    <Icon name="cloud" className="w-5 h-5" />
                                  </div>
                                  <div>
                                    <h3 className="font-bold text-white text-base">{vcHost}</h3>
                                    <span className="text-xs text-gray-400">{subnetsList.length} Subnet{subnetsList.length > 1 ? "s" : ""} Linked</span>
                                  </div>
                                </div>
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                                {subnetsList.map((sub) => (
                                  <div key={sub.id} onClick={async () => {
                                      setSelectedIpamSubnet(sub);
                                      const res = await fetch(`${API_BASE}/ipam/subnets/${sub.id}/ips`);
                                      setSubnetIps(await res.json());
                                    }} className="bg-dark-900/90 border border-gray-700/60 p-4 rounded-xl shadow cursor-pointer hover:border-brand/60 hover:bg-dark-800 transition-all group">
                                    <div className="flex justify-between items-start mb-2">
                                      <div>
                                        <div className="flex items-center gap-2">
                                          <h4 className="font-bold text-gray-100 group-hover:text-blue-400 transition-colors">{sub.name}</h4>
                                          {sub.vlan && <span className="text-[10px] font-mono text-purple-300 bg-purple-500/10 px-1.5 py-0.5 rounded border border-purple-500/20">VLAN {sub.vlan}</span>}
                                        </div>
                                      </div>
                                      <span className="text-[11px] font-mono text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">{sub.cidr}</span>
                                    </div>
                                    <div className="flex justify-between items-center text-xs font-semibold text-gray-400 mt-4">
                                      <span>Gateway: {sub.gateway}</span>
                                      <span className="text-emerald-400">{sub.free_ips} / {sub.total_ips} Free</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    ) : (
                      <div className="bg-[#111827]/80 border border-gray-800 rounded-xl overflow-hidden shadow-xl p-6">
                        <div className="flex justify-between items-center mb-6 border-b border-gray-800 pb-4">
                          <div>
                            <div className="flex items-center gap-2">
                              <h3 className="text-lg font-bold text-white">{selectedIpamSubnet.name}</h3>
                              {selectedIpamSubnet.vlan && <span className="text-xs font-mono text-purple-300 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">VLAN {selectedIpamSubnet.vlan}</span>}
                            </div>
                            <div className="flex items-center gap-3 mt-1 flex-wrap">
                              <span className="text-xs font-mono text-blue-400">{selectedIpamSubnet.cidr}</span>
                              <span className="text-xs text-gray-500">• vCenter: {selectedIpamSubnet.vcenter}</span>
                              <span className="text-xs text-gray-500">• Gateway: {selectedIpamSubnet.gateway}</span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <button onClick={async () => {
                              if (window.confirm(`Delete subnet ${selectedIpamSubnet.name} (${selectedIpamSubnet.cidr})?`)) {
                                await fetch(`${API_BASE}/ipam/subnets/${selectedIpamSubnet.id}`, { method: "DELETE" });
                                setSelectedIpamSubnet(null);
                                setSubnetIps([]);
                                fetchIpamSubnets();
                              }
                            }} className="px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-xs text-red-400 border border-red-500/30 rounded transition-all">Delete Subnet</button>
                            <button onClick={() => { setSelectedIpamSubnet(null); setSubnetIps([]); fetchIpamSubnets(); }} className="px-3 py-1.5 bg-[#1f2937] hover:bg-[#374151] text-xs text-white rounded transition-all">Back to Subnets</button>
                          </div>
                        </div>

                        {/* Horizontal Table for IPs */}
                        <div className="overflow-x-auto rounded-lg border border-gray-800">
                          <table className="ipam-table">
                            <thead>
                              <tr>
                                <th>IP Address</th>
                                <th>Status</th>
                                <th>Is Manual</th>
                                <th>Reason</th>
                                <th>Last Scanned</th>
                                <th className="text-right">Action</th>
                              </tr>
                            </thead>
                            <tbody>
                              {subnetIps.map(ip => (
                                <tr key={ip.id}>
                                  <td className="font-mono font-medium text-white">{ip.ip_address}</td>
                                  <td><span className={`badge ${ip.status.toLowerCase().replace(/\s+/g, '-')}`}>{ip.status}</span></td>
                                  <td>{ip.is_manual ? "Yes" : "No"}</td>
                                  <td className="text-gray-400">{ip.reason || "-"}</td>
                                  <td className="text-gray-400 text-xs">{ip.last_scanned || "-"}</td>
                                  <td className="text-right">
                                    <button
                                      onClick={() => { setEditingIp(ip); setShowIpEditModal(true); }}
                                      className="px-2.5 py-1 text-xs font-semibold text-blue-400 hover:text-white bg-blue-500/10 hover:bg-blue-600 rounded transition-all"
                                    >
                                      Edit
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>

                        <div className="flex gap-4 mt-6 text-[10px] text-gray-400">
                          <span className="flex items-center gap-1"><div className="w-2 h-2 bg-emerald-500 rounded"></div>Free</span>
                          <span className="flex items-center gap-1"><div className="w-2 h-2 bg-red-500 rounded"></div>In Use</span>
                          <span className="flex items-center gap-1"><div className="w-2 h-2 bg-amber-500 rounded"></div>Quarantined</span>
                          <span className="flex items-center gap-1"><div className="w-2 h-2 bg-blue-500 rounded"></div>Reserved</span>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* ================= VM STUDIO (CREATE) ================= */}
              {activeView === "vm_studio" && (
                <div className="max-w-4xl mx-auto space-y-6 pb-12">
                  <div className="mb-8">
                      <h2 className="text-xl font-bold text-white tracking-tight">VM Studio</h2>
                      <p className="text-sm text-gray-400">Automated provisioning across linked vCenter endpoints.</p>
                  </div>

                  {/* Step 1 */}
                  <div className="bg-dark-800/80 backdrop-blur border border-gray-800 rounded-xl shadow-xl overflow-hidden">
                    <div className="bg-blue-600/10 border-b border-gray-800 px-6 py-4 flex items-center gap-3">
                      <div className="w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs font-bold shadow-[0_0_10px_rgba(59,130,246,0.5)]">1</div>
                      <h3 className="font-semibold text-white">Target Environment</h3>
                    </div>
                    <div className="p-6 space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="col-span-1 md:col-span-2">
                          <label className="block text-xs font-semibold text-gray-400 mb-1">Select vCenter Endpoint</label>
                          <select className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand"
                                  value={selectedVcenter?.host || ""} onChange={handleVcenterChange}>
                            <option value="">{loadingVcenters ? "Loading..." : "Choose Endpoint"}</option>
                            {vcenters.map((vc) => (<option key={vc.host} value={vc.host}>{vc.name ? `${vc.name} (${vc.host})` : vc.host}</option>))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-gray-400 mb-1">Service Account</label>
                          <input type="text" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" 
                                 placeholder="administrator@vsphere.local" value={form.username} onChange={e => updateForm("username", e.target.value)} />
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-gray-400 mb-1">Password {selectedVcenter?.hasPassword ? "(Vaulted)" : ""}</label>
                          <input type="password" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" 
                                 placeholder={selectedVcenter?.hasPassword ? "••••••••" : "Enter Password"} value={form.password} onChange={e => updateForm("password", e.target.value)} />
                        </div>
                      </div>
                      
                      {vcenterError && <div className="text-xs text-red-400 p-2 bg-red-500/10 rounded">{vcenterError}</div>}
                      {inventoryError && <div className="text-xs text-red-400 p-2 bg-red-500/10 rounded">{inventoryError}</div>}

                      {selectedVcenter && (
                        <div className="pt-2">
                          <button onClick={loadInventory} disabled={inventoryLoading} className="px-4 py-2.5 bg-dark-700 hover:bg-dark-600 text-white text-xs font-semibold rounded-lg border border-gray-700 transition-all flex items-center gap-2">
                            <Icon name="search" />
                            <span>{inventoryLoading ? "Querying Object Tree..." : "Load Inventory"}</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Step 2 */}
                  <div className="bg-dark-800/80 backdrop-blur border border-gray-800 rounded-xl shadow-xl overflow-hidden">
                    <div className="bg-purple-600/10 border-b border-gray-800 px-6 py-4 flex items-center gap-3">
                      <div className="w-6 h-6 rounded-full bg-purple-500 text-white flex items-center justify-center text-xs font-bold shadow-[0_0_10px_rgba(168,85,247,0.5)]">2</div>
                      <h3 className="font-semibold text-white">Compute & Configuration</h3>
                    </div>
                    <div className="p-6 space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        
                        {/* Auto-Placement Toggle */}
                        <div className="col-span-1 md:col-span-2 mb-2 pb-4 border-b border-gray-800/50">
                          <label className="flex items-center gap-3 cursor-pointer text-sm text-gray-300 w-fit">
                            <input type="checkbox" className="w-4 h-4 bg-dark-900 border-gray-700 text-blue-500 focus:ring-blue-500 rounded" 
                                   checked={form.autoPlacement} 
                                   onChange={(e) => { 
                                     updateForm("autoPlacement", e.target.checked); 
                                     if(e.target.checked){ updateForm("host", ""); updateForm("datastore", ""); } 
                                   }} />
                            <span className="font-semibold text-white">Enable Auto-Placement</span>
                            <span className="text-xs text-gray-500 hidden sm:inline">(Let the system find the best Host & Datastore automatically)</span>
                          </label>
                        </div>

                        {/* Manual Selection Dropdowns */}
                        {!form.autoPlacement && (
                          <>
                            <div className="col-span-1 md:col-span-2">
                              <label className="block text-xs font-semibold text-gray-400 mb-1">ESXi Host Node (Manual Selection)</label>
                              <select className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand"
                                      value={form.host} onChange={(e) => { updateForm("host", e.target.value); updateForm("datastore", ""); updateForm("network", ""); }} disabled={!selectedVcenter || loadingHosts}>
                                <option value="">{loadingHosts ? "Scanning..." : "Select Host Node"}</option>
                                {hosts.map((h) => (<option key={h.name} value={h.name}>{h.name} (CPU Free: {Number(h.cpu_free||0).toFixed(1)} / {Number(h.cpu_tot||0).toFixed(1)} GHz | RAM Free: {Number(h.mem_free||0).toFixed(1)} / {Number(h.mem_tot||0).toFixed(1)} GB)</option>))}
                              </select>
                            </div>
                            <div className="col-span-1 md:col-span-2">
                              <label className="block text-xs font-semibold text-gray-400 mb-1">Datastore (Manual Selection)</label>
                              <select className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand"
                                      value={form.datastore} onChange={e => updateForm("datastore", e.target.value)} disabled={!selectedVcenter || loadingDatastores || !form.host}>
                                <option value="">{loadingDatastores ? "Scanning..." : (!form.host ? "Select Host First" : "Select Datastore")}</option>
                                {datastores.filter(d => form.host && d.hosts && d.hosts.includes(form.host)).map((d) => (<option key={d.name} value={d.name}>{d.name} (Available: {Number(d.free_gb||0).toFixed(2)} / {Number(d.capacity_gb||0).toFixed(2)} GB)</option>))}
                              </select>
                            </div>
                          </>
                        )}

                        <div className="col-span-1 md:col-span-2">
                          <label className="block text-xs font-semibold text-gray-400 mb-1">Base Template</label>
                          <select className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand"
                                  value={form.template} onChange={e => {
                                    const tmpl = e.target.value;
                                    updateForm("template", tmpl);
                                    if (tmpl.toLowerCase().includes("esxi")) {
                                      updateForm("isEsxi", true);
                                    }
                                  }} disabled={!selectedVcenter || loadingTemplates}>
                            <option value="">{loadingTemplates ? "Scanning..." : "Select Template"}</option>
                            {templates.map((t) => (<option key={t.name} value={t.name}>{t.name}</option>))}
                          </select>
                        </div>
                        <div className="col-span-1 md:col-span-2">
                          <label className="block text-xs font-semibold text-gray-400 mb-1">Network Port Group</label>
                          <select className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand"
                                  value={form.network} onChange={e => updateForm("network", e.target.value)} disabled={!selectedVcenter || loadingNetworks}>
                            <option value="">{loadingNetworks ? "Scanning..." : (!form.autoPlacement && !form.host ? "Select Host First" : "Select Network")}</option>
                            {networks
                              .filter(n => form.autoPlacement || !form.host || (n.hosts && n.hosts.includes(form.host)))
                              .map((n) => (<option key={n.name} value={n.name}>{n.name}</option>))}
                          </select>
                        </div>
                        
                        <div><label className="block text-xs font-semibold text-gray-400 mb-1">vCPU Cores</label><input type="number" min="1" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={form.cpu} onChange={e => updateForm("cpu", e.target.value)} /></div>
                        <div><label className="block text-xs font-semibold text-gray-400 mb-1">Memory (GB)</label><input type="number" min="1" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={form.memory} onChange={e => updateForm("memory", e.target.value)} /></div>
                        <div><label className="block text-xs font-semibold text-gray-400 mb-1">Disk Size (GB)</label><input type="number" min="1" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={form.disk} onChange={e => updateForm("disk", e.target.value)} /></div>
                        <div><label className="block text-xs font-semibold text-gray-400 mb-1">Instances to Spawn</label><input type="number" min="1" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={form.vmCount} onChange={e => updateForm("vmCount", e.target.value)} /></div>
                        
                        <div><label className="block text-xs font-semibold text-gray-400 mb-1">VM Naming Prefix</label><input type="text" placeholder="SRV-PROD-" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={form.namingContext} onChange={e => updateForm("namingContext", e.target.value)} /></div>
                        <div><label className="block text-xs font-semibold text-gray-400 mb-1">Owner / Department</label><input type="text" placeholder="DevOps Team" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={form.vmOwner} onChange={e => updateForm("vmOwner", e.target.value)} /></div>
                        <div className="col-span-1 md:col-span-2"><label className="block text-xs font-semibold text-gray-400 mb-1">Guest OS Admin Password {form.isEsxi ? "(Root Password)" : "(Sysprep)"}</label><input type="password" placeholder="••••••••" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={form.localAdminPassword} onChange={e => updateForm("localAdminPassword", e.target.value)} /></div>
                        
                        {/* Nested ESXi Appliance Toggle */}
                        <div className="col-span-1 md:col-span-2">
                          <div className="flex items-center justify-between p-3.5 bg-dark-900 rounded-xl border border-gray-700">
                            <div>
                              <div className="text-xs font-semibold text-white flex items-center gap-2">
                                <Icon name="server" className="w-4 h-4 text-emerald-400" />
                                <span>Nested ESXi Appliance</span>
                                {form.isEsxi && <span className="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded font-mono">OVF guestinfo mode</span>}
                              </div>
                              <p className="text-[11px] text-gray-400 mt-0.5">
                                Injects networking & password via OVF extraConfig (guestinfo) instead of Windows Sysprep.
                              </p>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={form.isEsxi || false}
                                onChange={(e) => updateForm("isEsxi", e.target.checked)}
                                className="w-4 h-4 bg-dark-900 border-gray-700 text-blue-500 rounded focus:ring-blue-500"
                              />
                            </label>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Step 3 */}
                  <div className="bg-dark-800/80 backdrop-blur border border-gray-800 rounded-xl shadow-xl overflow-hidden">
                    <div className="bg-emerald-600/10 border-b border-gray-800 px-6 py-4 flex items-center gap-3">
                      <div className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs font-bold shadow-[0_0_10px_rgba(16,185,129,0.5)]">3</div>
                      <h3 className="font-semibold text-white">Network Topology</h3>
                    </div>
                    <div className="p-6 space-y-4">
                      
                      <div className="flex flex-wrap gap-6 mb-2">
                        <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-300">
                          <input type="radio" className="bg-dark-900 border-gray-700 text-blue-500 focus:ring-blue-500" name="ipMode" value="series" checked={ipMode === "series"} onChange={() => setIpMode("series")} />
                          Sequential IP Increment
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-300">
                          <input type="radio" className="bg-dark-900 border-gray-700 text-blue-500 focus:ring-blue-500" name="ipMode" value="dynamic" checked={ipMode === "dynamic"} onChange={() => setIpMode("dynamic")} />
                          Dynamic Pattern (Manual IPs)
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-300">
                          <input type="radio" className="bg-dark-900 border-gray-700 text-blue-500 focus:ring-blue-500" name="ipMode" value="ipam" checked={ipMode === "ipam"} onChange={() => { setIpMode("ipam"); fetchIpamSubnets(); }} />
                          IPAM Auto-Assign
                        </label>
                      </div>

                      {ipMode === "series" && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div><label className="block text-xs font-semibold text-gray-400 mb-1">Starting IP Address</label><input type="text" placeholder="10.0.0.50" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={form.startingIp} onChange={e => updateForm("startingIp", e.target.value)} /></div>
                          <div><label className="block text-xs font-semibold text-gray-400 mb-1">Subnet Mask</label><input type="text" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={form.subnet} onChange={e => updateForm("subnet", e.target.value)} /></div>
                          <div><label className="block text-xs font-semibold text-gray-400 mb-1">Gateway</label><input type="text" placeholder="10.0.0.1" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={form.gateway} onChange={e => updateForm("gateway", e.target.value)} /></div>
                          <div><label className="block text-xs font-semibold text-gray-400 mb-1">DNS Server</label><input type="text" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={form.dns} onChange={e => updateForm("dns", e.target.value)} /></div>
                        </div>
                      )}

                      {ipMode === "dynamic" && (
                        <div className="space-y-4">
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div><label className="block text-xs font-semibold text-gray-400 mb-1">Subnet Mask</label><input type="text" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={dynamicSubnet} onChange={e => setDynamicSubnet(e.target.value)} /></div>
                            <div><label className="block text-xs font-semibold text-gray-400 mb-1">Gateway</label><input type="text" placeholder="10.0.0.1" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={dynamicGateway} onChange={e => setDynamicGateway(e.target.value)} /></div>
                            <div><label className="block text-xs font-semibold text-gray-400 mb-1">DNS Server</label><input type="text" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={dynamicDns} onChange={e => setDynamicDns(e.target.value)} /></div>
                          </div>
                          
                          <div className="bg-[#0b0f19] border border-gray-800 p-4 rounded-lg">
                            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-3">Manual IP Assignment ({form.vmCount} Nodes)</span>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                              {dynamicIps.map((ip, idx) => (
                                <div key={idx}>
                                  <label className="block text-[10px] font-semibold text-gray-400 mb-1">Node #{idx + 1} IP</label>
                                  <input 
                                    type="text" 
                                    placeholder={`e.g. 10.131.67.${50 + idx}`} 
                                    className="w-full px-3 py-2 bg-dark-800 border border-gray-700 rounded-md text-sm text-gray-200 focus:outline-none focus:border-brand"
                                    value={ip} 
                                    onChange={(e) => handleDynamicIpChange(idx, e.target.value)} 
                                  />
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}

                      {ipMode === "ipam" && (
                        <div className="bg-[#0b0f19] border border-gray-800 p-4 rounded-lg space-y-4">
                          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-3">IPAM Verified Allocation ({form.vmCount} Nodes required)</span>
                          <div>
                            <label className="block text-xs font-semibold text-gray-400 mb-1">Target Subnet Pool</label>
                            <select className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand"
                                    value={form.ipamSubnetId || ""} onChange={e => updateForm("ipamSubnetId", e.target.value)}>
                              <option value="">Select Onboarded Subnet</option>
                              {ipamSubnets.filter(s => !selectedVcenter?.host || s.vcenter === form.vcenter || s.vcenter === selectedVcenter?.host).map((s) => (
                                <option key={s.id} value={s.id} disabled={s.free_ips < form.vmCount}>
                                  {s.name} ({s.cidr}) - {s.free_ips} Available
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="block text-xs font-semibold text-gray-400 mb-1">DNS Server</label>
                            <input type="text" className="w-full px-3 py-2.5 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-brand" value={form.dns} onChange={e => updateForm("dns", e.target.value)} />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions & Progress */}
                  {deploymentError && <div className="p-4 bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-xl">{deploymentError}</div>}
                  {deploymentMessage && !isDeploying && <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm rounded-xl">{deploymentMessage}</div>}

                  <div className="bg-gradient-to-r from-[#111827] to-[#1e3a8a]/20 border border-blue-500/30 rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-4 shadow-[0_0_30px_rgba(59,130,246,0.1)]">
                    <div>
                      <span className="text-[10px] font-bold text-blue-400 uppercase tracking-widest block mb-1">Ready To Execute</span>
                      <h3 className="text-xl font-bold text-white">{form.vmCount || 0} Nodes Configured</h3>
                      <p className="text-xs text-gray-400 mt-1">Target: {form.autoPlacement ? "Auto-Placement" : form.host} | Storage: {form.autoPlacement ? "Optimal DS" : form.datastore}</p>
                    </div>
                    <button onClick={startDeployment} disabled={isDeploying} className={`px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white text-sm font-bold rounded-lg shadow-lg shadow-blue-600/30 transition-all flex items-center gap-2 ${isDeploying ? 'opacity-70 cursor-not-allowed' : ''}`}>
                      {isDeploying ? (
                        <><span>Executing Pipeline...</span></>
                      ) : (
                        <><span>Launch Deployment</span><Icon name="arrowRight" /></>
                      )}
                    </button>
                  </div>

                  {isDeploying && (
                    <div className="bg-[#111827]/80 border border-gray-800 rounded-xl p-6">
                      <div className="flex justify-between text-xs font-semibold text-gray-400 mb-2">
                        <span>Cloning OS & Injecting Configs...</span>
                        <span className="text-blue-400">{Math.round(progress)}%</span>
                      </div>
                      <div className="w-full bg-[#0b0f19] h-2 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 transition-all duration-500 relative" style={{width: `${progress}%`}}>
                          <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                        </div>
                      </div>
                    </div>
                  )}

                </div>
              )}

              {/* ================= INFRASTRUCTURE DETAILS ================= */}
              {activeView === "infrastructure_details" && selectedLiveVcenter && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-xl font-bold text-white tracking-tight">Diagnostics: {selectedLiveVcenter.name || selectedLiveVcenter.host}</h2>
                      <p className="text-sm text-gray-400">Deep telemetry for selected cluster.</p>
                    </div>
                    <button onClick={() => setActiveView('dashboard')} className="px-4 py-2 bg-[#1f2937] hover:bg-[#374151] text-gray-300 text-xs font-semibold rounded-lg border border-gray-700 transition-all flex items-center gap-2">
                        <Icon name="arrowRight" className="rotate-180" />
                        <span>Back</span>
                    </button>
                  </div>

                  <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider mt-4">Hypervisor Nodes</h3>
                  <div className="bg-[#111827]/80 border border-gray-800 rounded-xl overflow-hidden shadow-xl">
                      <div className="overflow-x-auto">
                          <table className="w-full text-left border-collapse">
                              <thead>
                                  <tr className="border-b border-gray-800 bg-[#0b0f19]/50 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                                      <th className="py-3 px-4">Node ID</th>
                                      <th className="py-3 px-4">Status</th>
                                      <th className="py-3 px-4 w-1/3">CPU Load</th>
                                      <th className="py-3 px-4 w-1/3">RAM Load</th>
                                  </tr>
                              </thead>
                              <tbody className="divide-y divide-gray-800 text-xs text-gray-300">
                                {selectedLiveVcenter.hosts?.details?.map((h, idx) => (
                                  <tr key={idx} className="hover:bg-[#1f2937]/30 transition-colors">
                                      <td className="py-3 px-4 font-semibold text-white">{h.name}</td>
                                      <td className="py-3 px-4">
                                        {h.state === "connected" ? <span className="text-[10px] px-2 py-0.5 rounded border bg-emerald-500/10 text-emerald-400 border-emerald-500/20 font-semibold">LINKED</span> : <span className="text-[10px] px-2 py-0.5 rounded border bg-red-500/10 text-red-400 border-red-500/20 font-semibold">OFFLINE</span>}
                                      </td>
                                      <td className="py-3 px-4">
                                        {h.state === "connected" ? (
                                          <div>
                                            <div className="flex justify-between text-[10px] font-semibold text-gray-500 mb-1"><span>{Number(h.cpu_used||0).toFixed(1)} GHz</span><span>{Number(h.cpu_tot||0).toFixed(1)} GHz</span></div>
                                            <div className="w-full bg-[#0b0f19] h-1.5 rounded-full overflow-hidden"><div className="h-full" style={{width: `${formatPercentage(h.cpu_used, h.cpu_tot)}%`, backgroundColor: getBarColor(formatPercentage(h.cpu_used, h.cpu_tot))}}></div></div>
                                          </div>
                                        ) : <span className="text-gray-600">N/A</span>}
                                      </td>
                                      <td className="py-3 px-4">
                                        {h.state === "connected" ? (
                                          <div>
                                            <div className="flex justify-between text-[10px] font-semibold text-gray-500 mb-1"><span>{Number(h.mem_used||0).toFixed(1)} GB</span><span>{Number(h.mem_tot||0).toFixed(1)} GB</span></div>
                                            <div className="w-full bg-[#0b0f19] h-1.5 rounded-full overflow-hidden"><div className="h-full" style={{width: `${formatPercentage(h.mem_used, h.mem_tot)}%`, backgroundColor: getBarColor(formatPercentage(h.mem_used, h.mem_tot))}}></div></div>
                                          </div>
                                        ) : <span className="text-gray-600">N/A</span>}
                                      </td>
                                  </tr>
                                ))}
                              </tbody>
                          </table>
                      </div>
                  </div>

                  <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider mt-6">Storage Volumes</h3>
                  <div className="bg-[#111827]/80 border border-gray-800 rounded-xl overflow-hidden shadow-xl">
                      <div className="overflow-x-auto">
                          <table className="w-full text-left border-collapse">
                              <thead>
                                  <tr className="border-b border-gray-800 bg-[#0b0f19]/50 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                                      <th className="py-3 px-4">Datastore ID</th>
                                      <th className="py-3 px-4 w-2/5">Utilization</th>
                                      <th className="py-3 px-4">Free Space</th>
                                      <th className="py-3 px-4">Capacity</th>
                                  </tr>
                              </thead>
                              <tbody className="divide-y divide-gray-800 text-xs text-gray-300">
                                {selectedLiveVcenter.datastores?.details?.map((ds, idx) => (
                                  <tr key={idx} className="hover:bg-[#1f2937]/30 transition-colors">
                                      <td className="py-3 px-4 font-semibold text-white">{ds.name}</td>
                                      <td className="py-3 px-4">
                                        <div className="w-full bg-[#0b0f19] h-1.5 rounded-full overflow-hidden"><div className="h-full" style={{width: `${formatPercentage(ds.used, ds.capacity)}%`, backgroundColor: getBarColor(formatPercentage(ds.used, ds.capacity))}}></div></div>
                                      </td>
                                      <td className="py-3 px-4">{Number(ds.free||0).toFixed(2)} GB</td>
                                      <td className="py-3 px-4">{Number(ds.capacity||0).toFixed(2)} GB</td>
                                  </tr>
                                ))}
                              </tbody>
                          </table>
                      </div>
                  </div>
                </div>
              )}

              {/* ================= INVENTORY LOGS ================= */}
              {activeView === "inventory" && (
                <div className="space-y-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div>
                            <h2 className="text-xl font-bold text-white tracking-tight">Provisioning Ledger</h2>
                            <p className="text-sm text-gray-400">Historical archive of all automated deployments.</p>
                        </div>
                        <button onClick={downloadCSV} disabled={inventoryLogs.length === 0} className="px-4 py-2 bg-[#1f2937] hover:bg-[#374151] text-white text-xs font-semibold rounded-lg border border-gray-700 transition-all flex items-center gap-2">
                            <span>Download CSV</span>
                        </button>
                    </div>

                    <div className="bg-[#111827]/80 border border-gray-800 rounded-xl overflow-hidden shadow-xl">
                        <div className="p-4 border-b border-gray-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                            <h3 className="text-sm font-bold text-white">Full Archive</h3>
                            <div className="relative flex-1 max-w-sm">
                                <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500"><Icon name="search" /></span>
                                <input type="text" placeholder="Global search..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} 
                                  className="w-full pl-9 pr-4 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-xs text-gray-200 focus:outline-none focus:border-brand transition-all" />
                            </div>
                        </div>

                        {loadingInventoryLogs ? (
                          <div className="py-12 text-center text-sm text-gray-500">Querying database...</div>
                        ) : (
                          <div className="overflow-x-auto pb-4">
                              <table className="w-full text-left border-collapse min-w-[1000px]">
                                  <thead>
                                      <tr className="border-b border-gray-800 bg-[#0b0f19]/50 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                                          <th className="p-3">
                                            <div className="flex flex-col gap-2">
                                              <span>Date</span>
                                              <input type="text" placeholder="Filter..." value={colFilters.timestamp} onChange={(e) => setColFilters(p => ({...p, timestamp: e.target.value}))} className="w-full px-2 py-1 bg-[#111827] border border-gray-700 rounded text-xs font-normal text-gray-200 focus:outline-none focus:border-brand" />
                                            </div>
                                          </th>
                                          <th className="p-3">
                                            <div className="flex flex-col gap-2">
                                              <span>Node Name</span>
                                              <input type="text" placeholder="Filter..." value={colFilters.vmName} onChange={(e) => setColFilters(p => ({...p, vmName: e.target.value}))} className="w-full px-2 py-1 bg-[#111827] border border-gray-700 rounded text-xs font-normal text-gray-200 focus:outline-none focus:border-brand" />
                                            </div>
                                          </th>
                                          <th className="p-3">
                                            <div className="flex flex-col gap-2">
                                              <span>IP Address</span>
                                              <input type="text" placeholder="Filter..." value={colFilters.ipAddress} onChange={(e) => setColFilters(p => ({...p, ipAddress: e.target.value}))} className="w-full px-2 py-1 bg-[#111827] border border-gray-700 rounded text-xs font-normal text-gray-200 focus:outline-none focus:border-brand" />
                                            </div>
                                          </th>
                                          <th className="p-3">
                                            <div className="flex flex-col gap-2">
                                              <span>Template</span>
                                              <input type="text" placeholder="Filter..." value={colFilters.templateName} onChange={(e) => setColFilters(p => ({...p, templateName: e.target.value}))} className="w-full px-2 py-1 bg-[#111827] border border-gray-700 rounded text-xs font-normal text-gray-200 focus:outline-none focus:border-brand" />
                                            </div>
                                          </th>
                                          <th className="p-3">
                                            <div className="flex flex-col gap-2">
                                              <span>Owner</span>
                                              <input type="text" placeholder="Filter..." value={colFilters.vmOwner} onChange={(e) => setColFilters(p => ({...p, vmOwner: e.target.value}))} className="w-full px-2 py-1 bg-[#111827] border border-gray-700 rounded text-xs font-normal text-gray-200 focus:outline-none focus:border-brand" />
                                            </div>
                                          </th>
                                          <th className="p-3">
                                            <div className="flex flex-col gap-2">
                                              <span>Cluster</span>
                                              <input type="text" placeholder="Filter..." value={colFilters.vcenter} onChange={(e) => setColFilters(p => ({...p, vcenter: e.target.value}))} className="w-full px-2 py-1 bg-[#111827] border border-gray-700 rounded text-xs font-normal text-gray-200 focus:outline-none focus:border-brand" />
                                            </div>
                                          </th>
                                          <th className="p-3">
                                            <div className="flex flex-col gap-2">
                                              <span>ESXi Host / IP</span>
                                              <input type="text" placeholder="Filter..." value={colFilters.esxiHost} onChange={(e) => setColFilters(p => ({...p, esxiHost: e.target.value}))} className="w-full px-2 py-1 bg-[#111827] border border-gray-700 rounded text-xs font-normal text-gray-200 focus:outline-none focus:border-brand" />
                                            </div>
                                          </th>
                                          <th className="p-3">
                                            <div className="flex flex-col gap-2">
                                              <span>Operator</span>
                                              <input type="text" placeholder="Filter..." value={colFilters.provisionedBy} onChange={(e) => setColFilters(p => ({...p, provisionedBy: e.target.value}))} className="w-full px-2 py-1 bg-[#111827] border border-gray-700 rounded text-xs font-normal text-gray-200 focus:outline-none focus:border-brand" />
                                            </div>
                                          </th>
                                      </tr>
                                  </thead>
                                  <tbody className="divide-y divide-gray-800 text-xs text-gray-300">
                                    {filteredLogs.length === 0 ? (
                                      <tr><td colSpan="8" className="py-8 text-center text-gray-500">No records found.</td></tr>
                                    ) : (
                                      filteredLogs.map((log, i) => (
                                        <tr key={i} className="hover:bg-[#1f2937]/30 transition-colors">
                                            <td className="py-3 px-4 text-gray-500">{String(log.timestamp || "").split(" ")[0]}</td>
                                            <td className="py-3 px-4 font-semibold text-blue-400">{log.vmName || log.vmname}</td>
                                            <td className="py-3 px-4">{log.ipAddress || log.ipaddress || "N/A"}</td>
                                            <td className="py-3 px-4">{log.templateName || log.templatename || "Unknown"}</td>
                                            <td className="py-3 px-4">{log.vmOwner || log.vmowner}</td>
                                            <td className="py-3 px-4">{log.vcenter}</td>
                                            <td className="py-3 px-4">{log.esxiHost || log.esxihost || "N/A"}</td>
                                            <td className="py-3 px-4 text-gray-500">{log.provisionedBy || log.provisionedby}</td>
                                        </tr>
                                      ))
                                    )}
                                  </tbody>
                              </table>
                          </div>
                        )}
                    </div>
                </div>
              )}

              {/* ================= VCENTERS ================= */}
              {activeView === "vcenters" && (
                <div className="space-y-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div>
                            <h2 className="text-xl font-bold text-white tracking-tight">vCenters</h2>
                            <p className="text-sm text-gray-400">Register and manage linked vCenter environments.</p>
                        </div>
                        <button onClick={() => { setVcenterForm({ name: "", host: "", username: "", password: "", isEdit: false, oldHost: "" }); setShowVcenterModal(true); }} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-blue-600/20 transition-all flex items-center gap-2">
                            <Icon name="plus" />
                            <span>Link Environment</span>
                        </button>
                    </div>

                    <div className="bg-dark-800/80 border border-gray-800 p-4 rounded-xl shadow-lg mb-6 flex items-end gap-4">
                        <div className="flex-1 max-w-sm">
                            <label className="block text-xs font-semibold text-gray-400 mb-1">Discover from Subnet</label>
                            <select id="subnetScanSelect" className="w-full px-3 py-2 bg-dark-900 border border-gray-700 rounded-lg text-sm text-gray-200">
                                <option value="">Select onboarded subnet</option>
                                {ipamSubnets.map(s => <option key={s.id} value={s.id}>{s.name} ({s.cidr})</option>)}
                            </select>
                        </div>
                        <button onClick={async () => {
                            const el = document.getElementById("subnetScanSelect");
                            if(!el.value) return alert("Select subnet");
                            try {
                                const res = await fetch(`${API_BASE}/vcenters/discover`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({subnetId: el.value}) });
                                const data = await res.json();
                                if(data.discovered && data.discovered.length > 0) {
                                    alert(`Found vCenters: \n${data.discovered.join('\n')}\nYou can now link them.`);
                                } else alert("No vCenters found in this subnet.");
                            } catch (e) {
                                alert(`Discovery scan failed: ${e.message}`);
                            }
                        }} className="px-4 py-2 bg-purple-600/20 hover:bg-purple-600/30 text-purple-400 border border-purple-500/30 text-xs font-semibold rounded-lg transition-all">
                            Scan Subnet Network
                        </button>
                    </div>

                    {vcenterError && <div className="p-4 bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-xl">{vcenterError}</div>}

                    <div className="bg-[#111827]/80 border border-gray-800 rounded-xl overflow-hidden shadow-xl">
                        {loadingVcenters ? (
                          <div className="py-12 text-center text-sm text-gray-500">Scanning endpoints...</div>
                        ) : vcenters.length === 0 ? (
                          <div className="py-12 text-center text-sm text-gray-500">No environments linked.</div>
                        ) : (
                          <div className="overflow-x-auto">
                              <table className="w-full text-left border-collapse">
                                  <thead>
                                      <tr className="border-b border-gray-800 bg-[#0b0f19]/50 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                                          <th className="py-3 px-4">Alias</th>
                                          <th className="py-3 px-4">FQDN / IP</th>
                                          <th className="py-3 px-4">Service Account</th>
                                          <th className="py-3 px-4">Security Vault</th>
                                          <th className="py-3 px-4 text-right">Controls</th>
                                      </tr>
                                  </thead>
                                  <tbody className="divide-y divide-gray-800 text-xs text-gray-300">
                                      {vcenters.map((vc, i) => (
                                        <tr key={i} className="hover:bg-[#1f2937]/30 transition-colors">
                                            <td className="py-3 px-4 font-semibold text-white">{vc.name || "Unnamed"}</td>
                                            <td className="py-3 px-4">{vc.host}</td>
                                            <td className="py-3 px-4 text-gray-500">{vc.username}</td>
                                            <td className="py-3 px-4">
                                              {vc.hasPassword ? <span className="text-[10px] px-2 py-0.5 rounded border bg-emerald-500/10 text-emerald-400 border-emerald-500/20 font-semibold">SECURED</span> : <span className="text-[10px] px-2 py-0.5 rounded border bg-amber-500/10 text-amber-400 border-amber-500/20 font-semibold">UNSECURED</span>}
                                            </td>
                                            <td className="py-3 px-4 flex justify-end gap-2">
                                                <button onClick={() => { setVcenterForm({ name: vc.name||"", host: vc.host, username: vc.username, password: "", isEdit: true, oldHost: vc.host }); setShowVcenterModal(true); }} className="px-2.5 py-1.5 bg-[#1f2937] hover:bg-[#374151] text-gray-300 rounded border border-gray-700 transition-all">Edit</button>
                                                <button onClick={() => removeVcenter(vc.host)} className="px-2.5 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded border border-red-500/20 transition-all">Unlink</button>
                                            </td>
                                        </tr>
                                      ))}
                                  </tbody>
                              </table>
                          </div>
                        )}
                    </div>
                </div>
              )}

              {/* ================= USERS & ROLES ================= */}
              {activeView === "users" && (
                <div className="space-y-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div>
                            <h2 className="text-xl font-bold text-white tracking-tight">Access & Security</h2>
                            <p className="text-sm text-gray-400">Manage operator profiles and permission scopes.</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                      
                      {/* Roles Table */}
                      <div className="xl:col-span-1 bg-[#111827]/80 border border-gray-800 rounded-xl overflow-hidden shadow-xl h-fit">
                          <div className="p-4 border-b border-gray-800 flex justify-between items-center">
                            <h3 className="text-sm font-bold text-white">Privilege Scopes</h3>
                            <button onClick={() => setShowRoleModal(true)} className="text-[10px] px-2 py-1 bg-[#1f2937] hover:bg-[#374151] text-gray-300 rounded border border-gray-700 transition-all">+ Add Scope</button>
                          </div>
                          <div className="overflow-x-auto">
                              <table className="w-full text-left border-collapse">
                                  <tbody className="divide-y divide-gray-800 text-xs text-gray-300">
                                      {rolesList.map((r) => (
                                        <tr key={r.id} className="hover:bg-[#1f2937]/30 transition-colors">
                                            <td className="py-3 px-4 font-semibold text-white">{r.name}</td>
                                            <td className="py-3 px-4 flex justify-end">
                                              {["Admin", "Deployer", "Viewer"].includes(r.name) ? (
                                                <span className="text-[10px] text-gray-600">SYSTEM</span>
                                              ) : (
                                                <button onClick={() => removeRole(r.id, r.name)} className="text-red-400 hover:text-red-300"><Icon name="x" className="w-3.5 h-3.5" /></button>
                                              )}
                                            </td>
                                        </tr>
                                      ))}
                                  </tbody>
                              </table>
                          </div>
                      </div>

                      {/* Users Table */}
                      <div className="xl:col-span-2 bg-[#111827]/80 border border-gray-800 rounded-xl overflow-hidden shadow-xl">
                          <div className="p-4 border-b border-gray-800 flex justify-between items-center">
                            <h3 className="text-sm font-bold text-white">Platform Operators</h3>
                            <button onClick={() => { setUserForm({ id: null, username: "", fullName: "", role: rolesList[0]?.name || "", password: "", isEdit: false }); setShowUserModal(true); }} className="text-xs px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg shadow-lg shadow-blue-600/20 transition-all flex items-center gap-2"><Icon name="users" /> <span>Add Operator</span></button>
                          </div>
                          <div className="overflow-x-auto">
                              <table className="w-full text-left border-collapse">
                                  <thead>
                                      <tr className="border-b border-gray-800 bg-[#0b0f19]/50 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                                          <th className="py-3 px-4">Operator ID</th>
                                          <th className="py-3 px-4">Alias</th>
                                          <th className="py-3 px-4">Scope</th>
                                          <th className="py-3 px-4 text-right">Controls</th>
                                      </tr>
                                  </thead>
                                  <tbody className="divide-y divide-gray-800 text-xs text-gray-300">
                                      {usersList.map((usr) => (
                                        <tr key={usr.id} className="hover:bg-[#1f2937]/30 transition-colors">
                                            <td className="py-3 px-4 font-semibold text-blue-400">{usr.username}</td>
                                            <td className="py-3 px-4">{usr.fullName}</td>
                                            <td className="py-3 px-4">
                                              {usr.role === "Admin" && <span className="text-[10px] px-2 py-0.5 rounded border bg-red-500/10 text-red-400 border-red-500/20 font-semibold">ADMIN</span>}
                                              {usr.role === "Viewer" && <span className="text-[10px] px-2 py-0.5 rounded border bg-gray-500/10 text-gray-400 border-gray-500/20 font-semibold">VIEWER</span>}
                                              {usr.role !== "Admin" && usr.role !== "Viewer" && <span className="text-[10px] px-2 py-0.5 rounded border bg-blue-500/10 text-blue-400 border-blue-500/20 font-semibold uppercase">{usr.role}</span>}
                                            </td>
                                            <td className="py-3 px-4 flex justify-end gap-2">
                                                <button onClick={() => { setUserForm({ id: usr.id, username: usr.username, fullName: usr.fullName, role: usr.role, password: "", isEdit: true }); setShowUserModal(true); }} className="px-2.5 py-1.5 bg-[#1f2937] hover:bg-[#374151] text-gray-300 rounded border border-gray-700 transition-all">Edit</button>
                                                <button onClick={() => removeUser(usr.id, usr.username)} disabled={usr.username === 'admin'} className={`px-2.5 py-1.5 rounded border transition-all ${usr.username === 'admin' ? 'bg-transparent text-gray-600 border-gray-800 cursor-not-allowed' : 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/20'}`}>Revoke</button>
                                            </td>
                                        </tr>
                                      ))}
                                  </tbody>
                              </table>
                          </div>
                      </div>

                    </div>
                </div>
              )}

              {/* ================= VMWARE EXPLORER ================= */}
              {activeView === "vmware_explorer" && (() => {
                const filteredExplorerData = (explorerData || []).map(vc => {
                  if (filterVC !== "All" && vc.vc !== filterVC) return null;
                  const matchedHosts = (vc.hosts || []).map(host => {
                    if (explorerHostFilter && host.name !== explorerHostFilter) return null;
                    const matchedVms = (host.vms || []).filter(vm => {
                      const stateMatch = filterState === "All" || 
                        (filterState === "poweredOn" ? String(vm.state).includes("poweredOn") : !String(vm.state).includes("poweredOn"));
                      const searchMatch = !explorerSearch || (vm.name && vm.name.toLowerCase().includes(explorerSearch.toLowerCase()));
                      return stateMatch && searchMatch;
                    });
                    if ((explorerSearch || filterState !== "All") && matchedVms.length === 0) {
                      return null;
                    }
                    return { ...host, vms: matchedVms };
                  }).filter(Boolean);

                  if ((explorerSearch || filterState !== "All" || explorerHostFilter) && matchedHosts.length === 0) {
                    return null;
                  }
                  return { ...vc, hosts: matchedHosts };
                }).filter(Boolean);

                return (
                  <div className="space-y-6">
                    <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
                      <div>
                        <h2 className="text-xl font-bold text-white tracking-tight">VMware Explorer</h2>
                        <p className="text-sm text-gray-400">Hierarchical datacenter topology and VM lifecycle controls.</p>
                      </div>
                      <div className="flex items-center gap-2.5 flex-wrap">
                        {/* Filter by vCenter */}
                        <select value={filterVC} onChange={e => setFilterVC(e.target.value)} className="px-3 py-2 bg-dark-900 border border-gray-700 rounded-lg text-xs text-white focus:outline-none focus:border-brand">
                          <option value="All">All vCenters</option>
                          {(explorerData || []).map(vc => <option key={vc.vc} value={vc.vc}>{vc.vc}</option>)}
                        </select>

                        {/* Filter by Host */}
                        <select value={explorerHostFilter} onChange={e => setExplorerHostFilter(e.target.value)} className="px-3 py-2 bg-dark-900 border border-gray-700 rounded-lg text-xs text-white focus:outline-none focus:border-brand">
                          <option value="">All Hosts</option>
                          {(explorerData || []).filter(vc => filterVC === "All" || vc.vc === filterVC).flatMap(vc => vc.hosts || []).map(h => <option key={h.name} value={h.name}>{h.name}</option>)}
                        </select>

                        {/* Filter by State */}
                        <select value={filterState} onChange={e => setFilterState(e.target.value)} className="px-3 py-2 bg-dark-900 border border-gray-700 rounded-lg text-xs text-white focus:outline-none focus:border-brand">
                          <option value="All">All States</option>
                          <option value="poweredOn">Powered On</option>
                          <option value="poweredOff">Powered Off</option>
                        </select>

                        {/* Global Search */}
                        <input type="text" placeholder="Search VMs..." value={explorerSearch} onChange={e => setExplorerSearch(e.target.value)} className="px-3 py-2 bg-dark-900 border border-gray-700 rounded-lg text-xs text-white focus:outline-none focus:border-brand" />

                        <button onClick={fetchExplorerData} className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white text-xs font-semibold rounded-lg transition-all">↻ Refresh</button>
                      </div>
                    </div>

                    {loadingExplorer ? (
                      <div className="text-center py-12 text-gray-500 text-sm">Building Object Tree...</div>
                    ) : filteredExplorerData.length === 0 ? (
                      <div className="text-center py-12 text-gray-500 text-sm bg-[#111827] rounded-xl border border-gray-800">
                        {explorerData.length === 0 ? "Click 'Refresh' to build datacenter topology." : "No virtual machines or hosts match your filter criteria."}
                      </div>
                    ) : (
                      <div className="flex flex-col gap-4 overflow-x-auto pb-6">
                        {filteredExplorerData.map((vc, vIdx) => (
                          <div key={vIdx} className="bg-[#111827] border border-gray-800 rounded-xl overflow-hidden min-w-[800px]">
                            <div className="bg-[#0b0f19] p-4 border-b border-gray-800 flex justify-between items-center cursor-pointer hover:bg-gray-800/30" onClick={() => setExpandedVCs(p => ({...p, [vc.vc]: !p[vc.vc]}))}>
                              <div className="flex items-center gap-3">
                                <Icon name="cloud" className="text-blue-400" />
                                <span className="font-bold text-white">{vc.vc}</span>
                              </div>
                              <span className="text-xs text-gray-500">{(vc.hosts || []).length} Hosts Connected</span>
                            </div>
                            
                            {expandedVCs[vc.vc] && (
                              <div className="p-4 space-y-4 bg-dark-800/50">
                                {(vc.hosts || []).map((host, hIdx) => (
                                  <div key={hIdx} className="border border-gray-700 rounded-lg bg-dark-900">
                                    <div className="p-3 border-b border-gray-700 flex justify-between items-center cursor-pointer hover:bg-gray-800" onClick={() => setExpandedHosts(p => ({...p, [host.name]: !p[host.name]}))}>
                                      <div className="flex items-center gap-2">
                                        <Icon name="server" className="w-4 h-4 text-emerald-400" />
                                        <span className="font-semibold text-gray-200 text-sm">{host.name}</span>
                                      </div>
                                      <div className="text-xs text-gray-400 flex gap-4">
                                        <span>CPU: {host.cpu_tot}GHz</span>
                                        <span>RAM: {host.mem_tot}GB</span>
                                        <span>{(host.datastores || []).length} Datastores</span>
                                      </div>
                                    </div>
                                    
                                    {expandedHosts[host.name] && (
                                      <div className="p-4 space-y-4">
                                        {/* Visual Resource Bars */}
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-dark-950/60 p-3 rounded-lg border border-gray-800">
                                          <div className="resource-bar">
                                            <span>CPU: {host.cpu_used || 0} / {host.cpu_tot || 0} GHz</span>
                                            <progress value={host.cpu_used || 0} max={host.cpu_tot || 1}></progress>
                                          </div>
                                          <div className="resource-bar">
                                            <span>RAM: {host.mem_used || 0} / {host.mem_tot || 0} GB</span>
                                            <progress value={host.mem_used || 0} max={host.mem_tot || 1}></progress>
                                          </div>
                                        </div>

                                        <div className="flex gap-2 flex-wrap">
                                          {(host.datastores || []).map((ds, dIdx) => (
                                            <div key={dIdx} className="px-3 py-1.5 bg-gray-800 rounded border border-gray-700 text-[10px] text-gray-300">
                                              <span className="font-semibold">{ds.name}</span>: {ds.free} / {ds.cap} GB Free
                                            </div>
                                          ))}
                                        </div>
                                        
                                        {/* Horizontal VM Table */}
                                        <div className="overflow-x-auto rounded-lg border border-gray-800 mt-4">
                                          <table className="w-full text-left text-xs text-gray-300">
                                            <thead className="bg-[#111827] text-gray-400 uppercase text-[10px] tracking-wider border-b border-gray-800">
                                              <tr>
                                                <th className="py-2.5 px-3">VM Name</th>
                                                <th className="py-2.5 px-3">State</th>
                                                <th className="py-2.5 px-3">Power Controls</th>
                                                <th className="py-2.5 px-3 text-right">Advanced Actions</th>
                                              </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-800/60">
                                              {(host.vms || []).length === 0 ? (
                                                <tr>
                                                  <td colSpan="4" className="py-4 text-center text-xs text-gray-500 italic">No virtual machines found</td>
                                                </tr>
                                              ) : (
                                                (host.vms || []).map((vm, vmIdx) => (
                                                  <tr key={vmIdx} className="hover:bg-gray-800/30">
                                                    <td className="py-2.5 px-3 font-semibold text-white">{vm.name}</td>
                                                    <td className="py-2.5 px-3">
                                                      <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${String(vm.state).includes('poweredOn') ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400' : 'bg-red-500/15 border-red-500/30 text-red-400'}`}>
                                                        {String(vm.state).includes('poweredOn') ? 'ON' : 'OFF'}
                                                      </span>
                                                    </td>
                                                    <td className="py-2.5 px-3">
                                                      <div className="flex items-center gap-1.5">
                                                        <button onClick={() => handleVmAction(vc.vc, vm.name, "poweron")} title="Power On" className="px-2 py-1 text-emerald-400 hover:bg-emerald-500/20 rounded border border-emerald-500/30 flex items-center gap-1 text-[11px]"><Icon name="zap" className="w-3 h-3" /> On</button>
                                                        <button onClick={() => handleVmAction(vc.vc, vm.name, "poweroff")} title="Power Off" className="px-2 py-1 text-red-400 hover:bg-red-500/20 rounded border border-red-500/30 flex items-center gap-1 text-[11px]"><Icon name="x" className="w-3 h-3" /> Off</button>
                                                        <button onClick={() => handleVmAction(vc.vc, vm.name, "suspend")} title="Suspend" className="px-2 py-1 text-amber-400 hover:bg-amber-500/20 rounded border border-amber-500/30 flex items-center gap-1 text-[11px]"><Icon name="pause" className="w-3 h-3" /> Suspend</button>
                                                        <button onClick={() => handleVmAction(vc.vc, vm.name, "delete")} title="Destroy" className="px-2 py-1 text-red-500 hover:bg-red-500/20 rounded border border-red-500/30 flex items-center gap-1 text-[11px]"><Icon name="trash2" className="w-3 h-3" /> Delete</button>
                                                      </div>
                                                    </td>
                                                    <td className="py-2.5 px-3 text-right">
                                                      <div className="flex items-center justify-end gap-1.5">
                                                        <button onClick={() => {
                                                          const sName = window.prompt("Enter snapshot name:", `${vm.name}-Snapshot`);
                                                          if (!sName) return;
                                                          const sDesc = window.prompt("Enter snapshot description (optional):", "Created via VMware Explorer") || "";
                                                          handleVmManage(vc.vc, vm.name, "snapshot", { snapshot_name: sName, snapshot_desc: sDesc });
                                                        }} className="px-2.5 py-1 bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 border border-purple-500/30 rounded text-[11px] font-medium flex items-center gap-1">
                                                          <Icon name="camera" className="w-3 h-3" /> Snapshot
                                                        </button>
                                                        <button onClick={() => {
                                                          const newName = window.prompt("Enter new VM name:", vm.name);
                                                          if (!newName || newName === vm.name) return;
                                                          handleVmManage(vc.vc, vm.name, "rename", { new_name: newName });
                                                        }} className="px-2.5 py-1 bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 border border-blue-500/30 rounded text-[11px] font-medium flex items-center gap-1">
                                                          <Icon name="edit" className="w-3 h-3" /> Rename
                                                        </button>
                                                        <button onClick={() => {
                                                          const allOtherHosts = (vc.hosts || []).filter(h => h.name !== host.name).map(h => h.name);
                                                          const defaultHost = allOtherHosts[0] || "";
                                                          const targetHost = window.prompt(`Enter target host for migration:\nAvailable hosts: ${allOtherHosts.join(', ') || 'None'}`, defaultHost);
                                                          if (!targetHost) return;
                                                          handleVmManage(vc.vc, vm.name, "migrate", { target_host: targetHost });
                                                        }} className="px-2.5 py-1 bg-teal-600/20 hover:bg-teal-600/40 text-teal-300 border border-teal-500/30 rounded text-[11px] font-medium flex items-center gap-1">
                                                          <Icon name="arrowRight" className="w-3 h-3" /> Migrate
                                                        </button>
                                                      </div>
                                                    </td>
                                                  </tr>
                                                ))
                                              )}
                                            </tbody>
                                          </table>
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* ================= THRESHOLD DIRECTOR ================= */}
              {activeView === "threshold_director" && (
                <div className="space-y-6">
                    <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
                        <div>
                            <h2 className="text-xl font-bold text-white tracking-tight">Threshold Director</h2>
                            <p className="text-sm text-gray-400">Critical resources exceeding custom utilization caps (Auto-audits every 5m).</p>
                        </div>
                        <div className="flex flex-wrap items-center gap-3">
                            {/* vCenter Filter */}
                            <select 
                              value={thresholdFilters.vcenter} 
                              onChange={(e) => setThresholdFilters(p => ({ ...p, vcenter: e.target.value }))}
                              className="px-3 py-2 bg-dark-900 border border-gray-700 rounded-lg text-xs text-white focus:outline-none focus:border-amber-500"
                            >
                              <option value="all">All vCenters</option>
                              {vcenters.map(vc => <option key={vc.host} value={vc.host}>{vc.name || vc.host}</option>)}
                            </select>

                            {/* Host Filter */}
                            <select 
                              value={thresholdFilters.host} 
                              onChange={(e) => setThresholdFilters(p => ({ ...p, host: e.target.value }))}
                              className="px-3 py-2 bg-dark-900 border border-gray-700 rounded-lg text-xs text-white focus:outline-none focus:border-amber-500"
                            >
                              <option value="all">All Hosts</option>
                              {[...new Set((thresholdData?.hosts || []).map(h => h.name))].map(hostName => (
                                <option key={hostName} value={hostName}>{hostName}</option>
                              ))}
                            </select>

                            <div className="flex items-center gap-2 bg-dark-900 px-3 py-2 rounded-lg border border-gray-700 text-xs">
                                <label className="text-gray-400 font-medium">CPU% &gt;</label>
                                <input type="number" min="1" max="100" value={cpuThreshold} onChange={e => setCpuThreshold(Number(e.target.value))} className="w-12 bg-dark-800 px-1.5 py-0.5 rounded text-white font-mono focus:outline-none focus:border-amber-500 border border-gray-700" />
                            </div>
                            <div className="flex items-center gap-2 bg-dark-900 px-3 py-2 rounded-lg border border-gray-700 text-xs">
                                <label className="text-gray-400 font-medium">RAM% &gt;</label>
                                <input type="number" min="1" max="100" value={memThreshold} onChange={e => setMemThreshold(Number(e.target.value))} className="w-12 bg-dark-800 px-1.5 py-0.5 rounded text-white font-mono focus:outline-none focus:border-amber-500 border border-gray-700" />
                            </div>
                            <div className="flex items-center gap-2 bg-dark-900 px-3 py-2 rounded-lg border border-gray-700 text-xs">
                                <label className="text-gray-400 font-medium">Disk% &gt;</label>
                                <input type="number" min="1" max="100" value={diskThreshold} onChange={e => setDiskThreshold(Number(e.target.value))} className="w-12 bg-dark-800 px-1.5 py-0.5 rounded text-white font-mono focus:outline-none focus:border-amber-500 border border-gray-700" />
                            </div>
                            <input type="text" placeholder="Search resources..." value={thresholdSearch} onChange={e => setThresholdSearch(e.target.value)} className="px-3 py-2 bg-dark-900 border border-gray-700 rounded-lg text-xs text-white" />
                            <button onClick={fetchThresholdData} className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5">
                                <Icon name="activity" className="w-3.5 h-3.5" />
                                <span>Audit Thresholds</span>
                            </button>
                        </div>
                    </div>

                    {loadingThreshold ? (<div className="text-center py-12 text-gray-500 text-sm">Evaluating Clusters...</div>) : (
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                            {/* Hosts Exceeding Limits */}
                            <div className="bg-[#111827] border border-red-500/20 rounded-xl p-4 shadow-lg shadow-red-500/5">
                                <h3 className="text-sm font-bold text-red-400 mb-3 border-b border-red-500/20 pb-2">Hosts &gt; {cpuThreshold}% CPU or &gt; {memThreshold}% RAM</h3>
                                <div className="space-y-2">
                                    {(thresholdData.hosts || [])
                                      .filter(h => thresholdFilters.vcenter === "all" || h.vc === thresholdFilters.vcenter)
                                      .filter(h => thresholdFilters.host === "all" || h.name === thresholdFilters.host)
                                      .filter(h => !thresholdSearch || (h.name && h.name.toLowerCase().includes(thresholdSearch.toLowerCase())))
                                      .map((h, i) => (
                                        <div key={i} className="flex justify-between items-center bg-dark-900 p-3 rounded border border-gray-800">
                                            <div>
                                                <div className="text-sm font-semibold text-white">{h.name}</div>
                                                <div className="text-[10px] text-gray-500">vCenter: {h.vc}</div>
                                            </div>
                                            <div className="text-xs font-bold text-red-400 text-right">
                                                {h.cpu_pct > cpuThreshold && <div>CPU: {h.cpu_pct}%</div>}
                                                {h.mem_pct > memThreshold && <div>RAM: {h.mem_pct}%</div>}
                                            </div>
                                        </div>
                                    ))}
                                    {(thresholdData.hosts || []).length === 0 && (
                                        <div className="py-8 text-center text-xs text-gray-500">All hosts operating within thresholds.</div>
                                    )}
                                </div>
                            </div>

                            {/* Datastores Exceeding Limits */}
                            <div className="bg-[#111827] border border-amber-500/20 rounded-xl p-4 shadow-lg shadow-amber-500/5">
                                <h3 className="text-sm font-bold text-amber-400 mb-3 border-b border-amber-500/20 pb-2">Datastores &gt; {diskThreshold}% Capacity</h3>
                                <div className="space-y-2">
                                    {(thresholdData.datastores || [])
                                      .filter(d => thresholdFilters.vcenter === "all" || d.vc === thresholdFilters.vcenter)
                                      .filter(d => !thresholdSearch || (d.name && d.name.toLowerCase().includes(thresholdSearch.toLowerCase())))
                                      .map((d, i) => (
                                        <div key={i} className="flex justify-between items-center bg-dark-900 p-3 rounded border border-gray-800">
                                            <div>
                                                <div className="text-sm font-semibold text-white">{d.name}</div>
                                                <div className="text-[10px] text-gray-500">vCenter: {d.vc}</div>
                                            </div>
                                            <div className="text-xs font-bold text-amber-400">
                                                Usage: {d.usage_percent}%
                                            </div>
                                        </div>
                                    ))}
                                    {(thresholdData.datastores || []).length === 0 && (
                                        <div className="py-8 text-center text-xs text-gray-500">All datastores within capacity limit.</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
              )}

              {/* ================= RESOURCE RECLAMATION ================= */}
              {activeView === "resource_reclamation" && (
                <div className="space-y-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div>
                            <h2 className="text-xl font-bold text-white tracking-tight">Resource Reclamation</h2>
                            <p className="text-sm text-gray-400">Identify unutilized assets spanning the enterprise.</p>
                        </div>
                        <div className="flex flex-wrap gap-3">
                            <input type="text" placeholder="Search VMs..." value={reclamationSearch} onChange={e => setReclamationSearch(e.target.value)} className="px-3 py-2 bg-dark-900 border border-gray-700 rounded-lg text-xs text-white" />
                            <div className="flex items-center gap-2 bg-dark-900 px-3 py-2 rounded-lg border border-gray-700 text-xs">
                                <label className="text-gray-400">Stale Days:</label>
                                <input type="number" value={staleDays} onChange={e => setStaleDays(e.target.value)} className="w-12 bg-transparent text-white focus:outline-none" />
                            </div>
                            <div className="flex items-center gap-2 bg-dark-900 px-3 py-2 rounded-lg border border-gray-700 text-xs">
                                <label className="text-gray-400">Zombie CPU% &lt;</label>
                                <input type="number" value={zombieCpu} onChange={e => setZombieCpu(e.target.value)} className="w-12 bg-transparent text-white focus:outline-none" />
                            </div>
                            <button onClick={fetchReclamationData} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-all">Scan Datacenter</button>
                        </div>
                    </div>

                    {/* Distinct Tabs */}
                    <div className="flex border-b border-gray-800 gap-6">
                        <button
                            onClick={() => setReclamationTab('zombies')}
                            className={`pb-3 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${reclamationTab === 'zombies' ? 'text-purple-400 border-purple-500' : 'text-gray-400 border-transparent hover:text-white'}`}
                        >
                            <Icon name="cpu" className="w-4 h-4" />
                            <span>Zombie VMs (Running, Low I/O)</span>
                            <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/30 font-mono">{(reclamationData.zombies || []).length}</span>
                        </button>
                        <button
                            onClick={() => setReclamationTab('stale')}
                            className={`pb-3 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${reclamationTab === 'stale' ? 'text-blue-400 border-blue-500' : 'text-gray-400 border-transparent hover:text-white'}`}
                        >
                            <Icon name="pause" className="w-4 h-4" />
                            <span>Stale VMs (Powered Off)</span>
                            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-300 border border-blue-500/30 font-mono">{(reclamationData.stale || []).length}</span>
                        </button>
                    </div>

                    {loadingReclamation ? (<div className="text-center py-12 text-gray-500 text-sm">Auditing Operational Footprint...</div>) : (
                        <div>
                            {reclamationTab === 'zombies' && (
                                <div className="bg-[#111827] border border-gray-800 rounded-xl overflow-hidden shadow-xl">
                                    <div className="p-4 bg-purple-900/20 border-b border-purple-900/30 text-sm font-bold text-purple-400 flex justify-between">
                                        <span>Zombie VMs (Running, Compute &lt; {zombieCpu}%)</span>
                                        <span className="text-purple-400/80">{(reclamationData.zombies || []).length} instances detected</span>
                                    </div>
                                    <div className="p-4 space-y-2 max-h-[600px] overflow-y-auto">
                                        {(reclamationData.zombies || []).filter(v => !reclamationSearch || (v.name && v.name.toLowerCase().includes(reclamationSearch.toLowerCase()))).map((vm, i) => (
                                            <div key={i} className="flex justify-between items-center bg-dark-900 p-3.5 rounded-lg border border-gray-800 hover:border-purple-500/40 transition-colors">
                                                <div>
                                                    <div className="text-sm font-semibold text-gray-200">{vm.name}</div>
                                                    <div className="text-[10px] text-gray-500">vCenter: {vm.vc}</div>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <span className="text-xs font-bold font-mono text-purple-400 bg-purple-500/10 px-2 py-1 rounded border border-purple-500/20">{vm.cpu_usage}% Compute Draw</span>
                                                    <button onClick={() => handleVmAction(vm.vc, vm.name, "poweroff")} className="px-2.5 py-1 text-xs bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded transition-all">Power Off</button>
                                                </div>
                                            </div>
                                        ))}
                                        {(reclamationData.zombies || []).length === 0 && (
                                            <div className="py-12 text-center text-sm text-gray-500">No zombie VMs detected matching current criteria.</div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {reclamationTab === 'stale' && (
                                <div className="bg-[#111827] border border-gray-800 rounded-xl overflow-hidden shadow-xl">
                                    <div className="p-4 bg-gray-800/30 border-b border-gray-800 text-sm font-bold text-white flex justify-between">
                                        <span>Stale VMs (Powered Off &gt; {staleDays} days)</span>
                                        <span className="text-gray-400">{(reclamationData.stale || []).length} instances detected</span>
                                    </div>
                                    <div className="p-4 space-y-2 max-h-[600px] overflow-y-auto">
                                        {(reclamationData.stale || []).filter(v => !reclamationSearch || (v.name && v.name.toLowerCase().includes(reclamationSearch.toLowerCase()))).map((vm, i) => (
                                            <div key={i} className="flex justify-between items-center bg-dark-900 p-3.5 rounded-lg border border-gray-800 hover:border-gray-700 transition-colors">
                                                <div>
                                                    <span className="text-sm font-medium text-gray-200">{vm.name}</span>
                                                    <div className="text-[10px] text-gray-500">vCenter: {vm.vc}</div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[10px] bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded font-semibold">POWERED OFF</span>
                                                    <button onClick={() => handleVmAction(vm.vc, vm.name, "delete")} className="px-2.5 py-1 text-xs bg-red-600/20 hover:bg-red-600/40 text-red-300 border border-red-500/30 rounded transition-all">Delete</button>
                                                </div>
                                            </div>
                                        ))}
                                        {(reclamationData.stale || []).length === 0 && (
                                            <div className="py-12 text-center text-sm text-gray-500">No stale VMs detected matching current criteria.</div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
              )}

              {/* ================= AI DEPLOYMENT ASSISTANT (CHATBOT) ================= */}
              {activeView === "chatbot" && (
                <div className="max-w-4xl mx-auto space-y-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div>
                            <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                              <Icon name="bot" className="w-5 h-5 text-blue-400" />
                              <span>AI Deployment Assistant</span>
                            </h2>
                            <p className="text-sm text-gray-400">Rule-based conversational intent parser for instant multi-node provisioning.</p>
                        </div>
                        <button
                          onClick={() => sendChatMessage("reset")}
                          className="px-3.5 py-1.5 bg-dark-700 hover:bg-dark-600 text-gray-300 text-xs font-semibold rounded-lg border border-gray-700 transition-all"
                        >
                          Clear Session
                        </button>
                    </div>

                    {/* Active Captured Parameters Summary */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <div className="bg-dark-800/80 border border-gray-800 p-3.5 rounded-xl">
                            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block">Target vCenter</span>
                            <span className={`text-sm font-semibold font-mono ${chatParams.vcenter ? 'text-blue-400' : 'text-gray-500'}`}>
                                {chatParams.vcenter || "Awaiting parameter..."}
                            </span>
                        </div>
                        <div className="bg-dark-800/80 border border-gray-800 p-3.5 rounded-xl">
                            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block">Base Template</span>
                            <span className={`text-sm font-semibold font-mono ${chatParams.template ? 'text-purple-400' : 'text-gray-500'}`}>
                                {chatParams.template || "Awaiting parameter..."}
                            </span>
                        </div>
                        <div className="bg-dark-800/80 border border-gray-800 p-3.5 rounded-xl">
                            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block">VM Count</span>
                            <span className={`text-sm font-semibold font-mono ${chatParams.vmCount ? 'text-emerald-400' : 'text-gray-500'}`}>
                                {chatParams.vmCount ? `${chatParams.vmCount} Node(s)` : "Awaiting parameter..."}
                            </span>
                        </div>
                    </div>

                    {/* Chat Messages Log */}
                    <div className="bg-[#111827] border border-gray-800 rounded-xl p-5 shadow-xl flex flex-col h-[460px]">
                        <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                            {chatMessages.map((msg, idx) => (
                                <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`max-w-[80%] p-3.5 rounded-2xl text-xs leading-relaxed ${
                                        msg.sender === 'user' 
                                          ? 'bg-blue-600 text-white rounded-br-none' 
                                          : 'bg-dark-800 text-gray-200 border border-gray-700/70 rounded-bl-none'
                                    }`}>
                                        <div className="flex items-center gap-1.5 mb-1 opacity-70 text-[10px] font-bold uppercase tracking-wider">
                                            <Icon name={msg.sender === 'user' ? 'users' : 'bot'} className="w-3 h-3" />
                                            <span>{msg.sender === 'user' ? (currentUser?.fullName || 'Operator') : 'Deploy Bot'}</span>
                                        </div>
                                        <p className="whitespace-pre-wrap">{msg.text}</p>
                                        
                                        {msg.ready && (
                                            <div className="mt-3 pt-3 border-t border-gray-700/60 flex items-center justify-between gap-3">
                                                <span className="text-emerald-400 font-semibold text-[11px]">Ready for pipeline trigger!</span>
                                                <button
                                                  onClick={() => applyChatbotToDeploy(msg.payload || chatParams)}
                                                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition-all text-xs flex items-center gap-1 shadow-md shadow-emerald-600/30"
                                                >
                                                  <span>Open in VM Studio</span>
                                                  <Icon name="arrowRight" className="w-3 h-3" />
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {chatLoading && (
                                <div className="flex justify-start">
                                    <div className="bg-dark-800 text-gray-400 p-3 rounded-2xl text-xs border border-gray-700 rounded-bl-none flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
                                        <span>Parsing intent...</span>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Quick Prompts */}
                        <div className="pt-3 border-t border-gray-800 flex items-center gap-2 flex-wrap mb-3">
                            <span className="text-[10px] text-gray-500 font-semibold uppercase">Suggestions:</span>
                            <button
                              onClick={() => sendChatMessage("Deploy 2 VMs on vcenter 10.131.33.19 with template win2022-base")}
                              className="text-[11px] px-2.5 py-1 bg-dark-800 hover:bg-dark-700 text-gray-300 rounded border border-gray-700 transition-colors"
                            >
                              Deploy 2 Win2022 VMs
                            </button>
                            <button
                              onClick={() => sendChatMessage("Create 1 VM on vcenter 10.130.80.45 template esxi-appliance")}
                              className="text-[11px] px-2.5 py-1 bg-dark-800 hover:bg-dark-700 text-gray-300 rounded border border-gray-700 transition-colors"
                            >
                              Create 1 ESXi VM
                            </button>
                            <button
                              onClick={() => sendChatMessage("Build 3 VMs")}
                              className="text-[11px] px-2.5 py-1 bg-dark-800 hover:bg-dark-700 text-gray-300 rounded border border-gray-700 transition-colors"
                            >
                              Build 3 VMs (partial)
                            </button>
                        </div>

                        {/* Input Box */}
                        <form
                          onSubmit={(e) => { e.preventDefault(); sendChatMessage(); }}
                          className="flex items-center gap-2"
                        >
                            <input
                              type="text"
                              value={chatPrompt}
                              onChange={(e) => setChatPrompt(e.target.value)}
                              placeholder="e.g. Deploy 2 VMs on vcenter 10.131.33.19 template win2022-base..."
                              className="flex-1 px-4 py-2.5 bg-dark-900 border border-gray-700 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
                            />
                            <button
                              type="submit"
                              disabled={!chatPrompt.trim() || chatLoading}
                              className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl transition-all flex items-center gap-1.5 text-xs font-semibold"
                            >
                              <Icon name="send" className="w-3.5 h-3.5" />
                              <span>Send</span>
                            </button>
                        </form>
                    </div>
                </div>
              )}

            </main>
        </div>
      </div>

      {/* ================= MODALS ================= */}

      {/* vCenter Modal */}
      {showVcenterModal && (
        <div className="fixed inset-0 bg-[#0b0f19]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex justify-between items-center mb-6 border-b border-gray-800 pb-3">
              <h3 className="text-lg font-bold text-white">{vcenterForm.isEdit ? "Modify Cloud Endpoint" : "Link Cloud Endpoint"}</h3>
              <button onClick={() => setShowVcenterModal(false)} className="text-gray-500 hover:text-white"><Icon name="x" /></button>
            </div>
            <form onSubmit={saveVcenterConfig} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Alias / Label</label>
                <input type="text" className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:border-blue-500 focus:outline-none" value={vcenterForm.name} onChange={(e) => setVcenterForm(p => ({ ...p, name: e.target.value }))} autoFocus required />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">vCenter IP / FQDN</label>
                <input type="text" className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:border-blue-500 focus:outline-none" value={vcenterForm.host} onChange={(e) => setVcenterForm(p => ({ ...p, host: e.target.value }))} required />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Service Account (SSO)</label>
                <input type="text" className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:border-blue-500 focus:outline-none" value={vcenterForm.username} onChange={(e) => setVcenterForm(p => ({ ...p, username: e.target.value }))} required />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Vault Key {vcenterForm.isEdit && <span className="font-normal opacity-70">(Leave blank to retain)</span>}</label>
                <input type="password" className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:border-blue-500 focus:outline-none" value={vcenterForm.password} onChange={(e) => setVcenterForm(p => ({ ...p, password: e.target.value }))} />
              </div>
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-800">
                <button type="button" onClick={() => setShowVcenterModal(false)} className="px-4 py-2 bg-[#1f2937] hover:bg-[#374151] text-white text-xs font-semibold rounded-lg border border-gray-700 transition-all">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-all">Store Securely</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* User Modal */}
      {showUserModal && (
        <div className="fixed inset-0 bg-[#0b0f19]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex justify-between items-center mb-6 border-b border-gray-800 pb-3">
              <h3 className="text-lg font-bold text-white">{userForm.isEdit ? "Configure Operator" : "Enroll Operator"}</h3>
              <button onClick={() => setShowUserModal(false)} className="text-gray-500 hover:text-white"><Icon name="x" /></button>
            </div>
            <form onSubmit={saveUserConfig} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Operator ID (Email/UID)</label>
                <input type="text" className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:border-blue-500 focus:outline-none" value={userForm.username} onChange={(e) => setUserForm(p => ({ ...p, username: e.target.value }))} autoFocus disabled={userForm.username === "admin"} required />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Display Alias</label>
                <input type="text" className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:border-blue-500 focus:outline-none" value={userForm.fullName} onChange={(e) => setUserForm(p => ({ ...p, fullName: e.target.value }))} required />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Scope / Role</label>
                <select className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:border-blue-500 focus:outline-none" value={userForm.role} onChange={(e) => setUserForm(p => ({ ...p, role: e.target.value }))} disabled={userForm.username === "admin"}>
                  {rolesList.map(r => (<option key={r.id} value={r.name}>{r.name}</option>))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Security Key {userForm.isEdit && <span className="font-normal opacity-70">(Leave blank to retain)</span>}</label>
                <input type="password" className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:border-blue-500 focus:outline-none" value={userForm.password} onChange={(e) => setUserForm(p => ({ ...p, password: e.target.value }))} required={!userForm.isEdit} />
              </div>
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-800">
                <button type="button" onClick={() => setShowUserModal(false)} className="px-4 py-2 bg-[#1f2937] hover:bg-[#374151] text-white text-xs font-semibold rounded-lg border border-gray-700 transition-all">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-all">Submit Protocol</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Role Modal */}
      {showRoleModal && (
        <div className="fixed inset-0 bg-[#0b0f19]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 w-full max-w-sm shadow-2xl">
            <div className="flex justify-between items-center mb-6 border-b border-gray-800 pb-3">
              <h3 className="text-lg font-bold text-white">Define Scope</h3>
              <button onClick={() => setShowRoleModal(false)} className="text-gray-500 hover:text-white"><Icon name="x" /></button>
            </div>
            <form onSubmit={saveRoleConfig} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Scope Title</label>
                <input type="text" className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:border-blue-500 focus:outline-none" placeholder="e.g. Auditor" value={roleFormName} onChange={(e) => setRoleFormName(e.target.value)} autoFocus required />
              </div>
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-800">
                <button type="button" onClick={() => setShowRoleModal(false)} className="px-4 py-2 bg-[#1f2937] hover:bg-[#374151] text-white text-xs font-semibold rounded-lg border border-gray-700 transition-all">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-all">Apply</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Subnet Onboard Modal */}
      {showSubnetModal && (
        <div className="fixed inset-0 bg-[#0b0f19]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex justify-between items-center mb-6 border-b border-gray-800 pb-3">
              <h3 className="text-lg font-bold text-white">Onboard Subnet</h3>
              <button onClick={() => setShowSubnetModal(false)} className="text-gray-500 hover:text-white"><Icon name="x" /></button>
            </div>
            <form onSubmit={async (e) => {
                e.preventDefault();
                try {
                  const res = await fetch(`${API_BASE}/ipam/subnets`, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(subnetForm)});
                  const data = await res.json();
                  if (!res.ok) throw new Error(data.error || "Failed to onboard subnet");
                  setShowSubnetModal(false);
                  fetchIpamSubnets();
                } catch (err) {
                  alert(err.message);
                }
            }} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Link to vCenter</label>
                <select className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:border-brand" value={subnetForm.vcenter} onChange={(e) => setSubnetForm(p => ({ ...p, vcenter: e.target.value }))} required>
                  <option value="">Select Environment</option>
                  {vcenters.map(vc => <option key={vc.host} value={vc.host}>{vc.name || vc.host}</option>)}
                </select>
              </div>
              <div><label className="block text-xs font-semibold text-gray-400 mb-1">Friendly Name</label><input type="text" className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:border-brand" placeholder="PROD-WEB-TIER" value={subnetForm.name} onChange={(e) => setSubnetForm(p => ({ ...p, name: e.target.value }))} required /></div>
              <div><label className="block text-xs font-semibold text-gray-400 mb-1">CIDR Block</label><input type="text" className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:border-brand" placeholder="10.0.0.0/24" value={subnetForm.cidr} onChange={(e) => setSubnetForm(p => ({ ...p, cidr: e.target.value }))} required /></div>
              <div><label className="block text-xs font-semibold text-gray-400 mb-1">Gateway IP</label><input type="text" className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:border-brand" placeholder="10.0.0.1" value={subnetForm.gateway} onChange={(e) => setSubnetForm(p => ({ ...p, gateway: e.target.value }))} required /></div>
              <div><label className="block text-xs font-semibold text-gray-400 mb-1">VLAN ID / Tag (Optional)</label><input type="text" className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:border-brand" placeholder="e.g. 100" value={subnetForm.vlan || ""} onChange={(e) => setSubnetForm(p => ({ ...p, vlan: e.target.value }))} /></div>
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-800">
                <button type="button" onClick={() => setShowSubnetModal(false)} className="px-4 py-2 bg-[#1f2937] hover:bg-[#374151] text-white text-xs rounded-lg transition-all">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded-lg transition-all">Onboard & Scan</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* IP Override Modal */}
      {showIpEditModal && editingIp && (
        <div className="fixed inset-0 bg-[#0b0f19]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 w-full max-w-sm shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-2">{editingIp.ip_address}</h3>
            <p className="text-xs text-gray-400 mb-4">Last verify: {editingIp.last_scanned || "Never"}</p>
            <form onSubmit={async (e) => {
                e.preventDefault();
                try {
                  await fetch(`${API_BASE}/ipam/ips/${editingIp.id}`, { method: "PUT", headers: {"Content-Type": "application/json"}, body: JSON.stringify({status: editingIp.status, reason: editingIp.reason})});
                  setShowIpEditModal(false);
                  if (selectedIpamSubnet) {
                    const res = await fetch(`${API_BASE}/ipam/subnets/${selectedIpamSubnet.id}/ips`);
                    setSubnetIps(await res.json());
                  }
                  fetchIpamSubnets();
                } catch (err) {
                  alert(err.message);
                }
            }} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Status Override</label>
                <select className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:border-brand" value={editingIp.status} onChange={(e) => setEditingIp(p => ({ ...p, status: e.target.value }))}>
                  <option value="Free">Free (Auto-Scan enabled)</option>
                  <option value="In Use">In Use (Manual)</option>
                  <option value="Quarantined">Quarantined (Exclude from Studio)</option>
                  <option value="Reserved">Reserved (Exclude from Studio)</option>
                </select>
              </div>
              {editingIp.status !== "Free" && (
                <div><label className="block text-xs font-semibold text-gray-400 mb-1">Reason / Note</label><input type="text" className="w-full px-3 py-2 bg-[#0b0f19] border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:border-brand" value={editingIp.reason || ""} onChange={(e) => setEditingIp(p => ({ ...p, reason: e.target.value }))} required /></div>
              )}
              <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-800">
                <button type="button" onClick={() => setShowIpEditModal(false)} className="px-4 py-2 bg-[#1f2937] text-white text-xs rounded-lg transition-all">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 text-white text-xs rounded-lg transition-all">Update Status</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Infrastructure Alerts & Processes Modal */}
      {showAlertsModal && (
        <div className="fixed inset-0 bg-[#0b0f19]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowAlertsModal(false)}>
          <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 w-full max-w-lg shadow-2xl space-y-5" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center border-b border-gray-800 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg border border-amber-500/20">
                  <Icon name="bell" className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Infrastructure Alerts & Processes</h3>
                  <p className="text-xs text-gray-400">Live health telemetry and background tasks</p>
                </div>
              </div>
              <button onClick={() => setShowAlertsModal(false)} className="text-gray-500 hover:text-white"><Icon name="x" /></button>
            </div>

            {/* Disconnected Hosts */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
                <Icon name="server" className="w-3.5 h-3.5 text-red-400" />
                <span>Disconnected / Degraded Hosts</span>
              </h4>
              <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                {(() => {
                  const disconnected = (liveStats || []).flatMap(vc =>
                    (vc.hosts?.details || [])
                      .filter(h => h.state !== "connected")
                      .map(host => ({ vc: vc.name || vc.host, host: host.name, state: host.state }))
                  );
                  if (disconnected.length === 0) {
                    return (
                      <div className="p-3 bg-dark-900/60 rounded-lg border border-gray-800 text-xs text-emerald-400 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                        <span>All ESXi hypervisors report connected & healthy.</span>
                      </div>
                    );
                  }
                  return disconnected.map((d, idx) => (
                    <div key={idx} className="p-2.5 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-300 flex justify-between items-center">
                      <div>
                        <span className="font-semibold">{d.host}</span>
                        <span className="text-[10px] text-gray-400 block">vCenter: {d.vc}</span>
                      </div>
                      <span className="text-[10px] uppercase font-bold bg-red-500/20 text-red-400 px-2 py-0.5 rounded border border-red-500/30">{d.state}</span>
                    </div>
                  ));
                })()}
              </div>
            </div>

            {/* Recent Portal Processes */}
            <div className="space-y-2 pt-2 border-t border-gray-800">
              <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
                <Icon name="activity" className="w-3.5 h-3.5 text-blue-400" />
                <span>Recent Portal Processes</span>
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {(inventoryLogs || []).slice(0, 5).map((log, idx) => (
                  <div key={idx} className="p-2.5 bg-dark-900/60 border border-gray-800 rounded-lg text-xs text-gray-300 flex justify-between items-center">
                    <div>
                      <span className="font-semibold text-blue-400">{log.vmName || log.vmname}</span>
                      <span className="text-[10px] text-gray-400 block">
                        IP: {log.ipAddress || log.ipaddress || "IPAM"} • By: {log.provisionedBy || "Portal"}
                      </span>
                    </div>
                    <span className="text-[10px] text-gray-500 font-mono">{String(log.timestamp || "").split(" ")[0]}</span>
                  </div>
                ))}
                {(inventoryLogs || []).length === 0 && (
                  <div className="p-3 bg-dark-900/60 rounded-lg border border-gray-800 text-xs text-gray-500 italic">
                    No recent deployment operations logged yet.
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-gray-800">
              <button onClick={() => setShowAlertsModal(false)} className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white text-xs font-semibold rounded-lg transition-all">Close</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;