"use client";

import { useEffect, useState } from "react";
import {
  getConnections,
  saveConnection,
  testConnection,
  disconnectConnection,
  getGoogleClientId,
  exchangeGoogleCode,
} from "@/lib/api";
import type { ConnectionOut, ConnectionTestResult } from "@/lib/types";

interface IntegrationsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnectionsUpdated?: () => void;
}

export default function IntegrationsModal({
  isOpen,
  onClose,
  onConnectionsUpdated,
}: IntegrationsModalProps) {
  const [connections, setConnections] = useState<ConnectionOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<string>("github");
  const [formData, setFormData] = useState<Record<string, Record<string, string>>>({});
  const [testing, setTesting] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  const [testResults, setTestResults] = useState<Record<string, ConnectionTestResult | null>>({});
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadConnections();
    }
  }, [isOpen]);

  async function loadConnections() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await getConnections();
      setConnections(data);
      if (data.length > 0 && !data.some((c) => c.provider === activeTab)) {
        setActiveTab(data[0].provider);
      }
    } catch (e) {
      setErrorMsg((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function handleFieldChange(provider: string, fieldName: string, val: string) {
    setFormData((prev) => ({
      ...prev,
      [provider]: {
        ...(prev[provider] || {}),
        [fieldName]: val,
      },
    }));
  }

  async function handleTest(provider: string) {
    const creds = formData[provider] || {};
    setTesting((prev) => ({ ...prev, [provider]: true }));
    setTestResults((prev) => ({ ...prev, [provider]: null }));
    try {
      const res = await testConnection(provider, creds);
      setTestResults((prev) => ({ ...prev, [provider]: res }));
    } catch (e) {
      setTestResults((prev) => ({
        ...prev,
        [provider]: {
          provider,
          ok: false,
          message: (e as Error).message || "Connection test failed",
        },
      }));
    } finally {
      setTesting((prev) => ({ ...prev, [provider]: false }));
    }
  }

  async function handleSave(provider: string) {
    const creds = formData[provider] || {};
    setSaving((prev) => ({ ...prev, [provider]: true }));
    setErrorMsg(null);
    try {
      const res = await saveConnection(provider, creds);
      setTestResults((prev) => ({ ...prev, [provider]: res }));
      await loadConnections();
      if (onConnectionsUpdated) onConnectionsUpdated();
    } catch (e) {
      setErrorMsg((e as Error).message || `Failed to save ${provider}`);
    } finally {
      setSaving((prev) => ({ ...prev, [provider]: false }));
    }
  }

  async function handleDisconnect(provider: string) {
    if (!window.confirm(`Are you sure you want to disconnect ${provider}?`)) return;
    setSaving((prev) => ({ ...prev, [provider]: true }));
    try {
      await disconnectConnection(provider);
      setTestResults((prev) => ({ ...prev, [provider]: null }));
      setFormData((prev) => ({ ...prev, [provider]: {} }));
      await loadConnections();
      if (onConnectionsUpdated) onConnectionsUpdated();
    } catch (e) {
      setErrorMsg((e as Error).message);
    } finally {
      setSaving((prev) => ({ ...prev, [provider]: false }));
    }
  }

  async function handleGoogleOAuthConnect() {
    setSaving((prev) => ({ ...prev, google: true }));
    setErrorMsg(null);
    try {
      const clientId = await getGoogleClientId();
      if (!clientId) {
        throw new Error("Google Client ID is not configured on the backend server.");
      }

      if (window.google?.accounts?.oauth2) {
        const client = window.google.accounts.oauth2.initCodeClient({
          client_id: clientId,
          scope: [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/classroom.courses.readonly",
            "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
            "https://www.googleapis.com/auth/classroom.announcements.readonly",
            "https://www.googleapis.com/auth/userinfo.email",
          ].join(" "),
          callback: async (response: any) => {
            if (response.code) {
              try {
                const res = await exchangeGoogleCode(response.code);
                setTestResults((prev) => ({ ...prev, google: res }));
                await loadConnections();
                if (onConnectionsUpdated) onConnectionsUpdated();
              } catch (err) {
                setErrorMsg((err as Error).message || "Google token exchange failed");
              } finally {
                setSaving((prev) => ({ ...prev, google: false }));
              }
            } else if (response.error) {
              setErrorMsg(`Google authorization error: ${response.error}`);
              setSaving((prev) => ({ ...prev, google: false }));
            }
          },
        });
        client.requestCode();
      } else {
        throw new Error("Google authentication library is loading. Please try again in a moment.");
      }
    } catch (e) {
      setErrorMsg((e as Error).message);
      setSaving((prev) => ({ ...prev, google: false }));
    }
  }

  if (!isOpen) return null;

  const currentApp = connections.find((c) => c.provider === activeTab);
  const connectedCount = connections.filter((c) => c.is_connected).length;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-container integrations-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="modal-close-btn"
          onClick={onClose}
          aria-label="Close integrations dialog"
        >
          ✕
        </button>

        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-header-text">
            <span className="modal-eyebrow font-greek">Sanctuary Integrations</span>
            <h2 className="modal-title font-greek">Connected App Vault</h2>
            <p className="modal-subtitle">
              Securely connect your tools. Credentials are encrypted at rest with
              Fernet and never stored in plaintext.
            </p>
          </div>
          <div className="connected-status-pill">
            <span className="live-status-dot pulse" />
            <span>
              {connectedCount} of {connections.length || 5} Apps Active
            </span>
          </div>
        </div>

        {errorMsg && <div className="modal-error-alert">{errorMsg}</div>}

        {/* Layout: Left Sidebar App List + Right Detail Panel */}
        <div className="integrations-body">
          {/* App Selector Sidebar */}
          <div className="integrations-nav">
            {connections.map((c) => (
              <button
                key={c.provider}
                type="button"
                className={`integration-nav-item ${
                  activeTab === c.provider ? "active" : ""
                }`}
                onClick={() => {
                  setActiveTab(c.provider);
                  setErrorMsg(null);
                }}
              >
                <div className="nav-item-icon">
                  {c.provider === "github" && "🐙"}
                  {c.provider === "codeforces" && "🏆"}
                  {c.provider === "google" && "📬"}
                  {c.provider === "gemini" && "✨"}
                  {c.provider === "telegram" && "✈️"}
                </div>
                <div className="nav-item-info">
                  <div className="nav-item-title">{c.title}</div>
                  <div className="nav-item-status">
                    {c.is_connected ? (
                      <span className="status-tag connected">Connected</span>
                    ) : (
                      <span className="status-tag pending">Needs Setup</span>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Right Detail / Configuration Panel */}
          <div className="integration-detail-panel">
            {loading && connections.length === 0 ? (
              <div className="loading-state">Loading connection states...</div>
            ) : currentApp ? (
              <div className="integration-card-expanded">
                <div className="detail-header">
                  <div>
                    <h3 className="detail-app-title font-greek">
                      {currentApp.title}
                    </h3>
                    <p className="detail-app-desc">{currentApp.description}</p>
                  </div>
                  <div
                    className={`status-chip ${
                      currentApp.is_connected ? "chip-connected" : "chip-idle"
                    }`}
                  >
                    <span className="chip-dot" />
                    <span>
                      {currentApp.is_connected ? "Connected" : "Disconnected"}
                    </span>
                  </div>
                </div>

                {/* Display connected metadata if available */}
                {currentApp.is_connected && currentApp.meta && (
                  <div className="connected-meta-box">
                    <span className="meta-label">Active Connection Data:</span>
                    <div className="meta-details">
                      {Object.entries(currentApp.meta).map(([k, v]) => (
                        <span key={k} className="meta-pill">
                          <strong>{k}:</strong> {String(v)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Google Workspace One-Click OAuth View */}
                {currentApp.provider === "google" ? (
                  <div style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "16px",
                    padding: "20px",
                    background: "var(--bg-panel)",
                    border: "1px solid var(--border-gold-subtle)",
                    borderRadius: "14px",
                    marginTop: "6px"
                  }}>
                    <div>
                      <h4 style={{ margin: "0 0 6px", color: "var(--gold-primary)", fontSize: "15px" }}>
                        One-Click Google Account Connection
                      </h4>
                      <p style={{ margin: 0, fontSize: "13px", color: "var(--text-muted)", lineHeight: 1.5 }}>
                        Authorize Kairo to read your university coursework, calendar schedules, and important emails in read-only mode. No manual code or tokens needed.
                      </p>
                    </div>

                    {currentApp.is_connected ? (
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px", paddingTop: "8px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#4ade80", fontWeight: 600, fontSize: "13px" }}>
                          <span style={{ fontSize: "16px" }}>✓</span>
                          <span>Connected ({String(currentApp.meta?.account || "Active")})</span>
                        </div>
                        <button
                          type="button"
                          className="btn-disconnect-conn"
                          style={{ margin: 0 }}
                          onClick={() => handleDisconnect("google")}
                          disabled={saving["google"]}
                        >
                          Disconnect Account
                        </button>
                      </div>
                    ) : (
                      <div style={{ paddingTop: "6px" }}>
                        <button
                          type="button"
                          className="google-sso-btn"
                          style={{ width: "auto", display: "inline-flex", padding: "10px 22px" }}
                          onClick={handleGoogleOAuthConnect}
                          disabled={saving["google"]}
                        >
                          <svg className="google-icon" viewBox="0 0 24 24" width="18" height="18">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                          </svg>
                          <span>{saving["google"] ? "Opening Google Authorization..." : "Connect Google Account"}</span>
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  /* Form fields for other apps (GitHub, Codeforces, Gemini, Telegram) */
                  <div className="detail-form">
                    {currentApp.fields.map((f) => (
                      <div key={f.name} className="form-group">
                        <label className="form-label">
                          {f.label}
                          {f.required && <span className="text-urgent"> *</span>}
                        </label>
                        <input
                          type={f.type}
                          className="form-input font-mono"
                          placeholder={f.placeholder}
                          value={formData[currentApp.provider]?.[f.name] || ""}
                          onChange={(e) =>
                            handleFieldChange(
                              currentApp.provider,
                              f.name,
                              e.target.value
                            )
                          }
                        />
                        {f.help_text && (
                          <span className="form-help-text">{f.help_text}</span>
                        )}
                      </div>
                    ))}

                    {/* Test feedback */}
                    {testResults[currentApp.provider] && (
                      <div
                        className={`test-result-box ${
                          testResults[currentApp.provider]?.ok
                            ? "test-success"
                            : "test-failed"
                        }`}
                      >
                        <span>
                          {testResults[currentApp.provider]?.ok ? "✓ " : "✕ "}
                          {testResults[currentApp.provider]?.message}
                        </span>
                      </div>
                    )}

                    {/* Actions Bar */}
                    <div className="detail-actions">
                      <button
                        type="button"
                        className="btn-test-conn"
                        onClick={() => handleTest(currentApp.provider)}
                        disabled={testing[currentApp.provider]}
                      >
                        {testing[currentApp.provider]
                          ? "Pinging Service..."
                          : "Test Connection"}
                      </button>

                      <button
                        type="button"
                        className="btn-save-conn"
                        onClick={() => handleSave(currentApp.provider)}
                        disabled={saving[currentApp.provider]}
                      >
                        {saving[currentApp.provider]
                          ? "Encrypting & Saving..."
                          : "Save & Connect"}
                      </button>

                      {currentApp.is_connected && (
                        <button
                          type="button"
                          className="btn-disconnect-conn"
                          onClick={() => handleDisconnect(currentApp.provider)}
                          disabled={saving[currentApp.provider]}
                        >
                          Disconnect
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
