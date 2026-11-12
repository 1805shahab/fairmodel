import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  AudioLines,
  Check,
  ShieldCheck,
} from "lucide-react";
import VoiceSculpture from "@/components/voice-sculpture";
import ProductWalkthrough from "@/components/product-walkthrough";
import ThemeToggle from "@/components/theme-toggle";
import SiteFooter from "@/components/site-footer";

// FairModel has one application. The former landing/preview fork is retired.
export default function Home() {
  return (
    <div className="landing-control rights-landing">
      <a className="rights-skip" href="#rights-main">
        Skip to content
      </a>
      <header className="rights-nav">
        <Link className="brand" href="/" aria-label="FairModel home">
          <span className="brand-icon">
            <AudioLines size={23} />
          </span>
          fairmodel<span className="brand-dot">.</span>
        </Link>
        <a className="rights-nav-explore" href="#how-it-works">
          How it works
        </a>
        <ThemeToggle />
        <Link className="button secondary" href="/dashboard">
          Open workspace <ArrowUpRight size={17} />
        </Link>
      </header>
      <main id="rights-main">
        <section
          className="rights-hero"
          aria-labelledby="rights-title"
          data-enter
        >
          <div className="rights-hero-copy">
            <span className="eyebrow">
              VOICE LICENSING, WITH THE ARTIST IN CONTROL
            </span>
            <h1 id="rights-title">
              Your voice. Your <em>rights.</em> Your royalties.
            </h1>
            <p>
              AI voice licensing, from permission to payment. Review the terms,
              measure the speech, and keep the artist in control of every
              charge.
            </p>
            <div className="rights-hero-actions">
              <Link className="button" href="/dashboard">
                Open workspace <ArrowRight size={18} />
              </Link>
              <a href="#how-it-works">
                Follow the workflow <span aria-hidden="true">↓</span>
              </a>
            </div>
            <div className="rights-hero-fact">
              <ShieldCheck size={17} />
              <span>Artist review before activation and invoicing.</span>
            </div>
          </div>
          <VoiceSculpture />
        </section>
        <section
          className="rights-story"
          id="how-it-works"
          aria-labelledby="workflow-heading"
        >
          <div className="rights-section-heading">
            <span className="eyebrow">ONE CONNECTED WORKSPACE</span>
            <h2 id="workflow-heading">
              From a clause
              <br />
              to a clear decision.
            </h2>
            <p>
              Artists and studios share the evidence. Each keeps the decisions
              that belong to them.
            </p>
          </div>
          <ProductWalkthrough />
        </section>
        <section className="rights-trust" aria-labelledby="trust-heading">
          <div>
            <span className="eyebrow">BUILT FOR ACCOUNTABILITY</span>
            <h2 id="trust-heading">
              Every finding,
              <br />
              open to <em>question.</em>
            </h2>
            <p>
              AI assists the review. Approved terms, measured usage and recorded
              human decisions determine what happens next.
            </p>
            <Link className="button" href="/dashboard">
              Open workspace <ArrowRight size={18} />
            </Link>
          </div>
          <div className="rights-trust-list">
            {[
              [
                "Evidence you can inspect",
                "PDF source clauses, transcript timestamps and measured speech intervals.",
              ],
              [
                "Math you can follow",
                "Deterministic royalty calculations using the approved allowance and rate.",
              ],
              [
                "Identity stated honestly",
                "Manual artist attestation is separate from optional speaker verification.",
              ],
              [
                "Payments labeled clearly",
                "PayPal Sandbox uses test funds. Local mock payments are simulations. Neither transfers real money.",
              ],
            ].map(([title, text]) => (
              <article key={title}>
                <Check size={19} />
                <div>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  );
}
