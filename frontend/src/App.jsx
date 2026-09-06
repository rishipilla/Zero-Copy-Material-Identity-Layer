import { useState } from "react";
import axios from "axios";
import {
  Upload,
  Search,
  Network,
  Database,
  GitMerge,
  CheckCircle2,
  AlertCircle,
  FileText,
} from "lucide-react";

import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("Ready");
  const [isImporting, setIsImporting] = useState(false);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setSelectedFile(null);
      setStatus("Error");
      setMessage("Please select a CSV file.");
      return;
    }

    setSelectedFile(file);
    setStatus("Ready");
    setMessage(`Selected: ${file.name}`);
  };

  const importCSV = async () => {
    if (!selectedFile) {
      setStatus("Error");
      setMessage("Please select a CSV file first.");
      return;
    }

    try {
      setIsImporting(true);
      setStatus("Importing...");
      setMessage("");

      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await axios.post(
        `${API_BASE_URL}/api/materials/import`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setStatus("Success");
      setMessage(
        `${response.data.imported_count} materials imported successfully.`
      );
    } catch (error) {
      console.error(error);

      setStatus("Error");

      if (error.response?.data?.detail) {
        setMessage(error.response.data.detail);
      } else {
        setMessage("Could not connect to the FastAPI backend.");
      }
    } finally {
      setIsImporting(false);
    }
  };

  const runMatching = async () => {
    try {
      setStatus("Running matching...");
      setMessage("");

      const response = await axios.post(
        `${API_BASE_URL}/api/materials/match`
      );

      setMessage(
        `Matching completed. ${response.data.matched_pairs} pairs evaluated.`
      );

      setStatus("Success");
    } catch (error) {
      console.error(error);

      setMessage("Could not connect to the FastAPI backend.");
      setStatus("Error");
    }
  };

  const buildIdentities = async () => {
    try {
      setStatus("Building identities...");
      setMessage("");

      const response = await axios.post(
        `${API_BASE_URL}/api/materials/identities`
      );

      setMessage(
        `Identity build completed. ${response.data.identity_count} identities created.`
      );

      setStatus("Success");
    } catch (error) {
      console.error(error);

      setMessage("Could not build identities.");
      setStatus("Error");
    }
  };

  const buildGraph = async () => {
    try {
      setStatus("Building graph...");
      setMessage("");

      const response = await axios.post(
        `${API_BASE_URL}/api/materials/graph`
      );

      setMessage(
        `Graph created. ${response.data.material_node_count} materials, ${response.data.identity_node_count} identities, ${response.data.membership_count} relationships.`
      );

      setStatus("Success");
    } catch (error) {
      console.error(error);

      setMessage("Could not create the Neo4j graph.");
      setStatus("Error");
    }
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            <GitMerge size={24} />
          </div>

          <div>
            <h1>Zero-Copy Material Identity</h1>
            <p>Intelligent material deduplication platform</p>
          </div>
        </div>

        <div className="system-status">
          {status === "Success" ? (
            <CheckCircle2 size={18} />
          ) : status === "Error" ? (
            <AlertCircle size={18} />
          ) : (
            <Database size={18} />
          )}

          <span>{status}</span>
        </div>
      </header>

      <main className="dashboard">
        <section className="hero">
          <div>
            <span className="eyebrow">MATERIAL INTELLIGENCE</span>

            <h2>
              One identity.
              <br />
              Many source records.
            </h2>

            <p>
              Normalize, match, consolidate, and visualize material records
              without modifying the original source data.
            </p>
          </div>
        </section>

        <section className="workflow">
          <div className="section-heading">
            <div>
              <span className="eyebrow">WORKFLOW</span>
              <h3>Material identity pipeline</h3>
            </div>
          </div>

          <div className="workflow-grid">
            <div className="workflow-card">
              <div className="card-icon">
                <Upload size={22} />
              </div>

              <div className="card-number">01</div>

              <h4>Import Materials</h4>

              <p>
                Load ERP and CSV material records into the source-preserving
                PostgreSQL layer.
              </p>

              <label className="file-picker">
                <FileText size={16} />

                <span>
                  {selectedFile ? selectedFile.name : "Choose CSV"}
                </span>

                <input
                  type="file"
                  accept=".csv,text/csv"
                  onChange={handleFileChange}
                />
              </label>

              <button
                onClick={importCSV}
                disabled={!selectedFile || isImporting}
              >
                {isImporting ? "Importing..." : "Import CSV"}
              </button>
            </div>

            <div className="workflow-card">
              <div className="card-icon">
                <Search size={22} />
              </div>

              <div className="card-number">02</div>

              <h4>Run Matching</h4>

              <p>
                Compare material descriptions using semantic, attribute, and
                rule-based scoring.
              </p>

              <button onClick={runMatching}>
                Run Matching
              </button>
            </div>

            <div className="workflow-card">
              <div className="card-icon">
                <GitMerge size={22} />
              </div>

              <div className="card-number">03</div>

              <h4>Build Identities</h4>

              <p>
                Group confirmed material matches into canonical material
                identities.
              </p>

              <button onClick={buildIdentities}>
                Build Identities
              </button>
            </div>

            <div className="workflow-card">
              <div className="card-icon">
                <Network size={22} />
              </div>

              <div className="card-number">04</div>

              <h4>Build Graph</h4>

              <p>
                Synchronize material identities and memberships into the Neo4j
                graph.
              </p>

              <button onClick={buildGraph}>
                Build Graph
              </button>
            </div>
          </div>
        </section>

        <section className="status-panel">
          <div className="status-title">
            <Database size={20} />

            <div>
              <span className="eyebrow">SYSTEM OUTPUT</span>
              <h3>Latest operation</h3>
            </div>
          </div>

          <div className="status-message">
            {message || "No operations have been executed yet."}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;