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
  AudioLines,
  ChartNoAxesCombined,
  FileText,
  LayoutDashboard,
  Menu,
  Mic2,
  ReceiptText,
  Settings2,
  ShieldCheck,
  ClipboardCheck,
  Calculator,
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
  { href: "/dashboard/reviews", label: "Review Center", Icon: ClipboardCheck },
];

const utilityLinks = [
  {
    href: "/dashboard/generate",
    label: "Generate advertisement",
    Icon: AudioLines,
  },
  {
    href: "/dashboard/simulator",
    label: "Royalty simulator",
    Icon: Calculator,
  },
  { href: "/dashboard/references", label: "Reference voice", Icon: Mic2 },
  { href: "/dashboard/audit", label: "Audit trail", Icon: ShieldCheck },
  {
    href: "/dashboard/settings",
    label: "Settings & integrations",
    Icon: Settings2,
  },
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
  const [search, setSearch] = useState("");
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
      notify(`Now viewing the ${value} workspace role.`);
    } catch {
      notify("Could not switch workspace role. Please retry.");
    } finally {
      setSwitching(false);
    }
  }
  useEffect(() => {
    function shortcut(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearch("");
        setMobile((value) => !value);
      }
    }
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  }, []);
  useEffect(() => {
    if (!mobile) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMobile(false);
        requestAnimationFrame(() =>
          document.getElementById("workspace-menu-toggle")?.focus(),
        );
      }
      if (event.key === "Tab") {
        const controls = document.querySelectorAll<HTMLElement>(
          "#workspace-mobile-navigation button, #workspace-mobile-navigation input, #workspace-mobile-navigation a",
        );
        const first = controls[0],
          last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [mobile]);

  function navigationLink({ href, label, Icon }: (typeof links)[number]) {
    const active =
      path === href || (href !== "/dashboard" && path.startsWith(href + "/"));
    return (
      <Link
        key={href}
        href={href}
        className={`workspace-nav-link ${active ? "active" : ""}`}
        aria-current={active ? "page" : undefined}
        onClick={() => setMobile(false)}
      >
        <Icon size={16} />
        {label}
      </Link>
    );
  }

  return (
    <Context.Provider value={{ role, revision, refresh, notify }}>
      <div className="workspace workspace-control workspace-stage">
        <a className="workspace-skip-link" href="#workspace-content">
          Skip to content
        </a>
        <header className="stage-header" inert={mobile}>
          <div className="stage-topbar">
            <Link
              className="stage-brand"
              href="/dashboard"
              aria-label="FairModel workspace"
            >
              <AudioLines size={23} /> FAIRMODEL<span>®</span>
            </Link>
            <span className="stage-edition">VOICE RIGHTS / WORKSPACE</span>
            <div className="stage-topbar-actions">
              <button
                id="workspace-menu-toggle"
                className="stage-launcher"
                aria-label="Open navigation"
                aria-expanded={mobile}
                aria-controls="workspace-mobile-navigation"
                onClick={() => {
                  setSearch("");
                  setMobile(true);
                }}
              >
                <Menu size={17} />
                <span>Jump to a page</span>
                <kbd>Ctrl K</kbd>
              </button>
              <label className="role-select">
                <span className="sr-only">Workspace role</span>
                <select
                  aria-label="Workspace role"
                  disabled={switching}
                  value={role}
                  onChange={(e) => void switchRole(e.target.value as Role)}
                >
                  <option value="artist">Artist view</option>
                  <option value="studio">Studio view</option>
                </select>
              </label>
            </div>
          </div>
          <nav className="stage-navigation" aria-label="Main navigation">
            {links.map(navigationLink)}
          </nav>
          <div className="stage-utility-bar">
            <span className="stage-local-access">
              <ShieldCheck size={12} /> Local role access · test payments only
            </span>
            <nav aria-label="Workspace tools">
              {utilityLinks.map(navigationLink)}
            </nav>
          </div>
        </header>
        {mobile && (
          <>
            <button
              className="workspace-menu-scrim"
              aria-label="Close navigation overlay"
              onClick={() => setMobile(false)}
            />
            <aside
              className="workspace-mobile-menu"
              id="workspace-mobile-navigation"
              aria-label="Workspace navigation"
              role="dialog"
              aria-modal="true"
            >
              <div className="workspace-mobile-heading">
                <span className="eyebrow">YOUR WORKSPACE</span>
                <button
                  className="icon-button"
                  aria-label="Close navigation"
                  onClick={() => setMobile(false)}
                >
                  <X size={21} />
                </button>
              </div>
              <label className="stage-page-search">
                Find a page
                <input
                  autoFocus
                  type="search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Licenses, invoices, analytics…"
                  onKeyDown={(e) => {
                    if (e.key === "ArrowDown") {
                      e.preventDefault();
                      document
                        .querySelector<HTMLElement>(
                          "#workspace-mobile-navigation nav a",
                        )
                        ?.focus();
                    }
                  }}
                />
              </label>
              <nav aria-label="Mobile navigation">
                {links
                  .filter((item) =>
                    item.label.toLowerCase().includes(search.toLowerCase()),
                  )
                  .map(navigationLink)}
                <span className="workspace-menu-divider" />
                {utilityLinks
                  .filter((item) =>
                    item.label.toLowerCase().includes(search.toLowerCase()),
                  )
                  .map(navigationLink)}
              </nav>
              {![...links, ...utilityLinks].some((item) =>
                item.label.toLowerCase().includes(search.toLowerCase()),
              ) && (
                <p className="small">
                  No matching pages. Try “license” or “invoice”.
                </p>
              )}
              <p className="small">Arrow down to browse · Escape to close</p>
            </aside>
          </>
        )}
        <div className="workspace-main" inert={mobile || switching}>
          <main
            className="page-content"
            id="workspace-content"
            key={role}
            tabIndex={-1}
          >
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
