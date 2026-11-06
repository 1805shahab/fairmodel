"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  ArrowUpRight,
  AudioLines,
  ChartNoAxesCombined,
  ChevronDown,
  FileText,
  LayoutDashboard,
  Menu,
  Mic2,
  ReceiptText,
  Settings2,
  ShieldCheck,
  X,
} from "lucide-react";
import type { Role } from "./types";

interface WorkspaceContext {
  role: Role;
  revision: number;
  refresh: () => void;
  notify: (message: string) => void;
}
const Context = createContext<WorkspaceContext>({
  role: "artist",
  revision: 0,
  refresh: () => {},
  notify: () => {},
});
export const useWorkspace = () => useContext(Context);
const links = [
  { href: "/dashboard", label: "Overview", Icon: LayoutDashboard },
  { href: "/dashboard/licenses", label: "Voice licenses", Icon: FileText },
  {
    href: "/dashboard/submissions",
    label: "Audio submissions",
    Icon: AudioLines,
  },
  {
    href: "/dashboard/royalties",
    label: "Royalties",
    Icon: ChartNoAxesCombined,
  },
  {
    href: "/dashboard/invoices",
    label: "Invoices & payments",
    Icon: ReceiptText,
  },
  { href: "/dashboard/analytics", label: "Analytics", Icon: Activity },
];

export default function Workspace({
  children,
  initialRole,
}: {
  children: React.ReactNode;
  initialRole: Role;
}) {
  const [role, setRole] = useState<Role>(initialRole);
  const [revision, setRevision] = useState(0);
  const [message, setMessage] = useState("");
  const [mobile, setMobile] = useState(false);
  const [switching, setSwitching] = useState(false);
  const path = usePathname();
  const refresh = useCallback(() => setRevision((x) => x + 1), []);
  const notify = useCallback((text: string) => setMessage(text), []);
  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(() => setMessage(""), 6000);
    return () => clearTimeout(timer);
  }, [message]);
  async function switchRole(value: Role) {
    setSwitching(true);
    try {
      const response = await fetch("/api/persona", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ persona: `${value}_demo` }),
      });
      if (!response.ok) throw new Error("Could not switch persona.");
      setRole(value);
      refresh();
      notify(`Switched to ${value} demo persona.`);
    } catch {
      notify("Could not switch persona. Please retry.");
    } finally {
      setSwitching(false);
    }
  }
  return (
    <Context.Provider value={{ role, revision, refresh, notify }}>
      <div className="workspace">
        <aside className={`sidebar ${mobile ? "open" : ""}`}>
          <div className="sidebar-brand">
            <Link className="brand" href="/">
              <span className="brand-icon">
                <AudioLines size={23} />
              </span>
              fairmodel<span className="brand-dot">.</span>
            </Link>
            <button
              className="icon-button mobile-only"
              aria-label="Close navigation"
              onClick={() => setMobile(false)}
            >
              <X size={20} />
            </button>
          </div>
          <div className="workspace-label">
            <span className="workspace-avatar">
              {role === "artist" ? "AR" : "NS"}
            </span>
            <div>
              <strong>
                {role === "artist" ? "Amara’s workspace" : "Northstar Studio"}
              </strong>
              <span>Demo {role} account</span>
            </div>
            <ChevronDown size={15} />
          </div>
          <span className="nav-heading">WORKSPACE</span>
          <nav aria-label="Main navigation">
            {links.map(({ href, label, Icon }) => (
              <Link
                onClick={() => setMobile(false)}
                key={href}
                href={href}
                className={`nav-link ${path === href || (href !== "/dashboard" && path.startsWith(href + "/")) ? "active" : ""}`}
              >
                <Icon size={18} />
                {label}
                {label === "Voice licenses" && <span className="nav-dot" />}
              </Link>
            ))}
          </nav>
          <span className="nav-heading lower">MANAGE</span>
          <Link
            className={`nav-link ${path === "/dashboard/references" ? "active" : ""}`}
            href="/dashboard/references"
          >
            <Mic2 size={18} />
            Reference voice
          </Link>
          <Link
            className={`nav-link ${path === "/dashboard/audit" ? "active" : ""}`}
            href="/dashboard/audit"
          >
            <ShieldCheck size={18} />
            Audit trail
          </Link>
          <Link
            className={`nav-link ${path === "/dashboard/settings" ? "active" : ""}`}
            href="/dashboard/settings"
          >
            <Settings2 size={18} />
            Demo & integrations
          </Link>
          <div className="sidebar-bottom">
            <div className="creator-note">
              <span className="live-dot" /> CREATORS COME FIRST
              <p>
                Your voice stays yours.
                <br />
                We help keep it that way.
              </p>
              <Link href="/dashboard/licenses">
                Manage your rights <ArrowUpRight size={14} />
              </Link>
            </div>
            <div className="sidebar-profile">
              <span className="avatar">{role === "artist" ? "AR" : "NS"}</span>
              <div>
                <strong>
                  {role === "artist" ? "Amara Reed" : "Northstar Studio"}
                </strong>
                <span>Demo {role}</span>
              </div>
              <span className="online-dot" />
            </div>
          </div>
        </aside>
        {mobile && (
          <button
            aria-label="Close navigation overlay"
            className="scrim"
            onClick={() => setMobile(false)}
          />
        )}
        <div className="workspace-main">
          <header className="topbar">
            <div className="breadcrumb">
              <button
                className="icon-button mobile-only"
                aria-label="Open navigation"
                onClick={() => setMobile(true)}
              >
                <Menu size={21} />
              </button>
              <span>Workspace</span>
              <span>/</span>
              <strong>
                {links.find(
                  (x) => x.href !== "/dashboard" && path.startsWith(x.href),
                )?.label ||
                  (path.includes("settings")
                    ? "Integrations"
                    : path.includes("references")
                      ? "Reference voice"
                      : path.includes("audit")
                        ? "Audit trail"
                        : "Overview")}
              </strong>
            </div>
            <div className="topbar-right">
              <span className="demo-label">
                <span className="live-dot" /> LOCAL DEMO
              </span>
              <label className="role-select">
                <span className="sr-only">Demo persona</span>
                <select
                  aria-label="Demo persona"
                  disabled={switching}
                  value={role}
                  onChange={(e) => void switchRole(e.target.value as Role)}
                >
                  <option value="artist">Artist view</option>
                  <option value="studio">Studio view</option>
                </select>
              </label>
            </div>
          </header>
          <div className="demo-ribbon">
            <ShieldCheck size={14} />
            <span>
              Demo personas · Human-approved royalties · Simulated payments only
            </span>
            <Link href="/dashboard/settings">
              View setup <ArrowUpRight size={12} />
            </Link>
          </div>
          <main className="page-content" key={role}>
            {children}
          </main>
          <footer className="workspace-footer">
            <span>Every voice deserves a fair share.</span>
            <span>FairModel · Local development</span>
          </footer>
        </div>
        {message && (
          <div className="toast" role="status">
            {message}
            <button
              className="icon-button"
              aria-label="Dismiss notification"
              onClick={() => setMessage("")}
            >
              <X size={16} />
            </button>
          </div>
        )}
      </div>
    </Context.Provider>
  );
}
