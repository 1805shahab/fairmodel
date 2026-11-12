import Link from "next/link";
import { ArrowUpRight, AudioLines } from "lucide-react";

export default function SiteFooter({ compact = false }: { compact?: boolean }) {
  return (
    <footer
      className={`site-footer ${compact ? "site-footer-compact" : "site-footer-public"}`}
    >
      <div className="site-footer-inner">
        <div className="site-footer-main">
          <div className="site-footer-brand">
            <Link href="/" aria-label="FairModel home">
              <AudioLines size={24} aria-hidden="true" />
              <strong>FAIRMODEL</strong>
            </Link>
            <p>Every voice deserves a fair share.</p>
            {!compact && (
              <span>
                Voice licensing, explainable compliance and artist-approved
                royalties.
              </span>
            )}
          </div>
          {compact ? (
            <nav className="site-footer-quick" aria-label="Footer navigation">
              <Link href="/dashboard/licenses">License directory</Link>
              <Link href="/dashboard/invoices">Payment history</Link>
              <Link href="/dashboard/settings">Integration status</Link>
            </nav>
          ) : (
            <div className="site-footer-directory">
              <nav aria-label="Footer workspace">
                <h3>Workspace</h3>
                <Link href="/dashboard">
                  Overview <ArrowUpRight size={13} />
                </Link>
                <Link href="/dashboard/licenses">Voice licenses</Link>
                <Link href="/dashboard/generate">Generate advertisement</Link>
              </nav>
              <nav aria-label="Footer evidence">
                <h3>Evidence</h3>
                <Link href="/dashboard/submissions">Audio & compliance</Link>
                <Link href="/dashboard/reviews">Review Center</Link>
                <Link href="/dashboard/audit">Audit trail</Link>
              </nav>
              <nav aria-label="Footer financial records">
                <h3>Financial records</h3>
                <Link href="/dashboard/royalties">Royalties</Link>
                <Link href="/dashboard/invoices">Invoices & payments</Link>
                <Link href="/dashboard/analytics">Royalty analytics</Link>
              </nav>
            </div>
          )}
        </div>
        <div className="site-footer-bottom">
          <span>© 2026 FairModel</span>
          <span>Demo personas · test payments only</span>
          <nav aria-label="Footer resources">
            <Link href="/dashboard/settings">Integrations & local access</Link>
            <Link href="/design-system">Interface reference</Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}
