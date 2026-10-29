import { useState } from "react";
import "./App.css";

function App() {
  const [showAddForm, setShowAddForm] = useState(false);

  const [vCenters, setVCenters] = useState([
    {
      id: 1,
      name: "Production vCenter",
      address: "vcenter-prod.example.com",
      username: "administrator@vsphere.local",
    },
  ]);

  const [form, setForm] = useState({
    name: "",
    address: "",
    username: "",
  });

  const handleChange = (event) => {
    setForm({
      ...form,
      [event.target.name]: event.target.value,
    });
  };

  const handleAdd = (event) => {
    event.preventDefault();

    if (!form.name || !form.address || !form.username) {
      return;
    }

    setVCenters([
      ...vCenters,
      {
        id: Date.now(),
        ...form,
      },
    ]);

    setForm({
      name: "",
      address: "",
      username: "",
    });

    setShowAddForm(false);
  };

  const handleDelete = (id) => {
    setVCenters(
      vCenters.filter((vcenter) => vcenter.id !== id)
    );
  };

  return (
    <div className="app">

      {/* Sidebar */}
      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">V</div>

          <div>
            <h1>VMware Portal</h1>
            <span>Infrastructure Manager</span>
          </div>
        </div>

        <nav className="navigation">

          <div className="nav-section">
            MANAGEMENT
          </div>

          <button className="nav-item active">
            <span>▦</span>
            Dashboard
          </button>

          <button className="nav-item">
            <span>☁</span>
            vCenters
          </button>

          <button className="nav-item">
            <span>▣</span>
            VM Deployment
          </button>

          <div className="nav-section">
            SYSTEM
          </div>

          <button className="nav-item">
            <span>⚙</span>
            Settings
          </button>

        </nav>

        <div className="sidebar-footer">
          <div className="status-dot"></div>

          <div>
            <strong>System Online</strong>
            <span>Portal is running</span>
          </div>
        </div>

      </aside>

      {/* Main */}
      <main className="main">

        {/* Header */}
        <header className="topbar">

          <div>
            <h2>vCenter Management</h2>
            <p>
              Manage your configured VMware vCenter servers
            </p>
          </div>

          <button
            className="primary-button"
            onClick={() => setShowAddForm(true)}
          >
            <span>+</span>
            Add vCenter
          </button>

        </header>

        {/* Content */}
        <section className="content">

          {/* Stats */}
          <div className="stats-grid">

            <div className="stat-card">
              <div className="stat-icon blue">☁</div>

              <div>
                <span>Total vCenters</span>
                <strong>{vCenters.length}</strong>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon green">✓</div>

              <div>
                <span>Configured</span>
                <strong>{vCenters.length}</strong>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon purple">▣</div>

              <div>
                <span>VM Deployment</span>
                <strong>Ready</strong>
              </div>
            </div>

          </div>

          {/* vCenter List */}
          <div className="panel">

            <div className="panel-header">

              <div>
                <h3>Configured vCenters</h3>
                <p>
                  Select a vCenter later during VM deployment.
                </p>
              </div>

              <span className="count-badge">
                {vCenters.length}
              </span>

            </div>

            {vCenters.length === 0 ? (

              <div className="empty-state">

                <div className="empty-icon">
                  ☁
                </div>

                <h3>No vCenters configured</h3>

                <p>
                  Add your first vCenter to start deploying
                  virtual machines.
                </p>

                <button
                  className="primary-button"
                  onClick={() => setShowAddForm(true)}
                >
                  + Add vCenter
                </button>

              </div>

            ) : (

              <div className="vcenter-list">

                {vCenters.map((vcenter) => (

                  <div
                    className="vcenter-card"
                    key={vcenter.id}
                  >

                    <div className="vcenter-left">

                      <div className="vcenter-icon">
                        V
                      </div>

                      <div className="vcenter-info">

                        <h4>{vcenter.name}</h4>

                        <span>
                          {vcenter.address}
                        </span>

                        <small>
                          {vcenter.username}
                        </small>

                      </div>

                    </div>

                    <div className="vcenter-right">

                      <span className="online-badge">
                        ● Configured
                      </span>

                      <button
                        className="delete-button"
                        onClick={() =>
                          handleDelete(vcenter.id)
                        }
                      >
                        Delete
                      </button>

                    </div>

                  </div>

                ))}

              </div>

            )}

          </div>

        </section>

      </main>

      {/* Add vCenter Modal */}
      {showAddForm && (

        <div
          className="modal-overlay"
          onClick={() => setShowAddForm(false)}
        >

          <div
            className="modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <div className="modal-header">

              <div>
                <h3>Add vCenter</h3>
                <p>
                  Add a vCenter for future deployments.
                </p>
              </div>

              <button
                className="close-button"
                onClick={() =>
                  setShowAddForm(false)
                }
              >
                ×
              </button>

            </div>

            <form onSubmit={handleAdd}>

              <div className="form-group">
                <label>vCenter Name</label>

                <input
                  type="text"
                  name="name"
                  placeholder="Production vCenter"
                  value={form.name}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label>vCenter IP / FQDN</label>

                <input
                  type="text"
                  name="address"
                  placeholder="vcenter.example.com"
                  value={form.address}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label>Username</label>

                <input
                  type="text"
                  name="username"
                  placeholder="administrator@vsphere.local"
                  value={form.username}
                  onChange={handleChange}
                />
              </div>

              <div className="info-box">
                <span>🔒</span>

                <p>
                  The vCenter password will not be stored.
                  It will be requested when you connect to
                  the selected vCenter.
                </p>
              </div>

              <div className="modal-actions">

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() =>
                    setShowAddForm(false)
                  }
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                >
                  Save vCenter
                </button>

              </div>

            </form>

          </div>

        </div>

      )}

    </div>
  );
}

export default App;