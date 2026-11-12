"use client";
import Link from "next/link";
import ThemeToggle from "@/components/theme-toggle";
import {
  Badge,
  BusyButton,
  Empty,
  ErrorPanel,
  Field,
  Loading,
} from "@/components/ui";

export default function DesignSystem() {
  return (
    <main className="design-system workspace-stage">
      <nav className="detail-toolbar">
        <Link href="/dashboard" className="text-link">
          ← Open workspace
        </Link>
        <ThemeToggle />
      </nav>
      <span className="eyebrow">FAIRMODEL / INTERFACE REFERENCE</span>
      <h1>Recording-studio ledger.</h1>
      <p>
        Every voice deserves a fair share. One system for permissions, evidence
        and money.
      </p>
      <section>
        <h2>Palette & typography</h2>
        <div className="design-swatches">
          <span className="bg-paper text-ink">Paper / canvas</span>
          <span className="bg-ink text-paper">Ink / text</span>
          <span className="bg-vermilion text-paper">Vermilion / action</span>
        </div>
        <p>
          Instrument Serif for decisions. Geist for work. JetBrains Mono for
          exact values.
        </p>
        <p className="ledger-money">USD 57.54 · 58.77s · VERSION 4</p>
      </section>
      <section>
        <h2>Actions & input</h2>
        <div className="button-row">
          <button className="button">Primary action</button>
          <button className="button secondary">Secondary action</button>
          <BusyButton busy>Processing request</BusyButton>
        </div>
        <Field
          label="Campaign name"
          hint="Use the declared campaign name from the agreement."
        >
          <input placeholder="Campaign name" />
        </Field>
        <label className="checkbox">
          <input type="checkbox" />
          Consent is never selected in advance.
        </label>
      </section>
      <section>
        <h2>Status uses words and symbols</h2>
        <div className="button-row">
          {[
            "ANALYZED",
            "COMPLIANT",
            "NEEDS_REVIEW",
            "RESTRICTED_USAGE",
            "ADDITIONAL_ROYALTY_DUE",
          ].map((status) => (
            <Badge key={status} status={status} />
          ))}
        </div>
        <p>
          No payment success is illustrated here. Paid states require provider
          evidence.
        </p>
        <span className="provider-badge">PayPal Sandbox (test funds)</span>{" "}
        <span className="provider-badge">Mock provider</span>
      </section>
      <section>
        <h2>Loading, empty, error and stale</h2>
        <Loading />
        <Empty
          title="No recordings yet"
          description="Submit authorized audio to begin the analysis workflow."
          href="/dashboard/submissions/new"
          label="Submit audio"
        />
        <ErrorPanel
          message="The provider is unavailable. Your saved inputs remain available; retry when service is restored."
          retry={() => {}}
        />
        <div className="alert warning">
          Evidence changed after approval. Inspect the current recording and
          renew the review before invoicing.
        </div>
        <div className="alert success">
          Changes saved. No provider request or financial action was performed.
        </div>
      </section>
      <section>
        <h2>Interaction rules</h2>
        <p>
          8px spacing grid. 4px corners. 1px borders. 44px control targets.
          180ms ease-out transitions. Reduced motion pauses animation. Both
          themes use the same hierarchy and semantic status labels.
        </p>
      </section>
    </main>
  );
}
