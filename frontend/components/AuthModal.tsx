"use client";

import { useEffect, useRef, useState } from "react";
import { loginUser, registerUser, googleLogin, getGoogleClientId } from "@/lib/api";
import type { User } from "@/lib/types";
import KairoLogo from "./KairoLogo";

declare global {
  interface Window {
    google?: any;
  }
}

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
}

export default function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [googleClientId, setGoogleClientId] = useState<string>("");
  const [gisLoaded, setGisLoaded] = useState(false);
  const googleBtnRef = useRef<HTMLDivElement>(null);

  // 1. Fetch configured Google client ID from backend
  useEffect(() => {
    getGoogleClientId().then((cid) => {
      if (cid) setGoogleClientId(cid);
    });
  }, []);

  // 2. Load Google Identity Services script
  useEffect(() => {
    if (typeof window === "undefined") return;

    if (window.google?.accounts?.id) {
      setGisLoaded(true);
      return;
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => {
      setGisLoaded(true);
    };
    script.onerror = () => {
      console.warn("Could not load Google Identity Services script.");
    };
    document.body.appendChild(script);

    return () => {
      // Clean up script if unmounted before load
      if (script.parentNode) script.parentNode.removeChild(script);
    };
  }, []);

  // 3. Initialize and render official Google Sign-In button whenever modal opens and GIS is ready
  useEffect(() => {
    if (!isOpen || !gisLoaded || !googleClientId || !window.google?.accounts?.id) return;

    try {
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response: any) => {
          if (!response?.credential) return;
          setLoading(true);
          setError(null);
          try {
            const authRes = await googleLogin({ credential: response.credential });
            onSuccess(authRes.user);
            onClose();
          } catch (err) {
            setError((err as Error).message || "Google sign-in authentication failed");
          } finally {
            setLoading(false);
          }
        },
        auto_select: false,
        cancel_on_tap_outside: true,
      });

      if (googleBtnRef.current) {
        googleBtnRef.current.innerHTML = "";
        window.google.accounts.id.renderButton(googleBtnRef.current, {
          type: "standard",
          theme: "outline",
          size: "large",
          text: "continue_with",
          shape: "pill",
          width: 320,
          logo_alignment: "left",
        });
      }
    } catch (e) {
      console.warn("Google Accounts initialize failed:", e);
    }
  }, [isOpen, gisLoaded, googleClientId, onClose, onSuccess]);

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "login") {
        const res = await loginUser({ email, password });
        onSuccess(res.user);
        onClose();
      } else {
        if (!name.trim()) {
          throw new Error("Please enter your full name");
        }
        const res = await registerUser({ email, name, password });
        onSuccess(res.user);
        onClose();
      }
    } catch (err) {
      setError((err as Error).message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  function handleFallbackGoogleTrigger() {
    if (window.google?.accounts?.id && googleClientId) {
      window.google.accounts.id.prompt();
    } else {
      setError("Google Sign-In is initializing. Please wait a moment or use email sign-in.");
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-container auth-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={onClose} aria-label="Close dialog">
          ✕
        </button>

        {/* Modal Header */}
        <div className="modal-header-centered">
          <KairoLogo size="md" />
          <h2 className="modal-title font-greek">
            {mode === "login" ? "Enter the Temple" : "Join Kairo"}
          </h2>
          <p className="modal-subtitle">
            {mode === "login"
              ? "Your coordinated student intelligence workspace awaits."
              : "Synchronize your academic, project, and contest horizons."}
          </p>
        </div>

        {/* Auth Tabs */}
        <div className="auth-tab-bar">
          <button
            type="button"
            className={`auth-tab-btn ${mode === "login" ? "active" : ""}`}
            onClick={() => {
              setMode("login");
              setError(null);
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${mode === "register" ? "active" : ""}`}
            onClick={() => {
              setMode("register");
              setError(null);
            }}
          >
            Create Account
          </button>
        </div>

        {error && <div className="modal-error-alert">{error}</div>}

        {/* Official Google Identity Services Container */}
        <div className="google-oauth-wrap">
          <div ref={googleBtnRef} id="google-signin-btn-mount" className="google-btn-mount" />

          {/* Fallback button if GIS button container is loading */}
          {(!gisLoaded || !googleClientId) && (
            <button
              type="button"
              className="google-sso-btn"
              onClick={handleFallbackGoogleTrigger}
              disabled={loading}
            >
              <svg className="google-icon" viewBox="0 0 24 24" width="18" height="18">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>{loading ? "Connecting to Google..." : "Continue with Google"}</span>
            </button>
          )}
        </div>

        <div className="auth-divider">
          <span>or sign in with email</span>
        </div>

        {/* Credentials Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          {mode === "register" && (
            <div className="form-group">
              <label className="form-label" htmlFor="user-name">
                Full Name
              </label>
              <input
                id="user-name"
                type="text"
                className="form-input"
                placeholder="e.g. Nancy Singh"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                disabled={loading}
              />
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="user-email">
              Email Address
            </label>
            <input
              id="user-email"
              type="email"
              className="form-input"
              placeholder="name@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <div className="form-label-row">
              <label className="form-label" htmlFor="user-pwd">
                Password
              </label>
              <button
                type="button"
                className="btn-text-subtle"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
            <input
              id="user-pwd"
              type={showPassword ? "text" : "password"}
              className="form-input"
              placeholder={mode === "register" ? "At least 6 characters" : "••••••••"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              disabled={loading}
            />
          </div>

          <button type="submit" className="auth-submit-btn" disabled={loading}>
            {loading ? "Processing..." : mode === "login" ? "Sign In to Kairo" : "Create My Account"}
          </button>
        </form>
      </div>
    </div>
  );
}
