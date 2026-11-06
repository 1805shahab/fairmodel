import Link from "next/link";
import {
  ArrowRight,
  AudioLines,
  FileCheck2,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

export default function Landing() {
  return (
    <main className="landing">
      <nav className="landing-nav">
        <Link className="brand" href="/">
          <span className="brand-icon">
            <AudioLines size={22} />
          </span>
          fairmodel<span className="brand-dot">.</span>
        </Link>
        <span className="small hide-mobile">VOICE RIGHTS. MADE RIGHT.</span>
        <Link className="button secondary" href="/dashboard">
          Open workspace <ArrowRight size={16} />
        </Link>
      </nav>
      <section className="landing-hero">
        <span className="eyebrow">
          <span className="live-dot" /> THE FUTURE OF VOICE IS FAIR
        </span>
        <h1>
          Every voice deserves
          <br />a <span>fair share.</span>
        </h1>
        <p>
          Your voice. Your terms. Your royalties. Bring clarity to AI voice
          licensing, from the first agreement to the final approval.
        </p>
        <div className="button-row">
          <Link className="button" href="/dashboard">
            Enter demo workspace <ArrowRight size={17} />
          </Link>
          <Link className="text-link" href="/dashboard/settings">
            Explore integrations →
          </Link>
        </div>
        <span className="small">
          Local demo personas · Transparent AI evidence · Simulated payments
        </span>
      </section>
      <section className="landing-preview">
        <div className="preview-header">
          <span className="eyebrow">THE FAIRMODEL WORKFLOW</span>
          <span className="pill blue">Human approved. Always.</span>
        </div>
        <div className="workflow-cards">
          {[
            {
              Icon: FileCheck2,
              n: "01",
              title: "Set the terms",
              text: "Turn a licensing PDF into structured rules, with source evidence and artist review.",
            },
            {
              Icon: AudioLines,
              n: "02",
              title: "Understand every second",
              text: "Measure speech, transcribe audio, and evaluate declared campaign usage.",
            },
            {
              Icon: ShieldCheck,
              n: "03",
              title: "Make fairness measurable",
              text: "Explain every royalty. Approve each charge. Follow every simulated invoice.",
            },
          ].map(({ Icon, n, title, text }) => (
            <article key={n}>
              <div className="step-top">
                <Icon size={25} />
                <span>{n}</span>
              </div>
              <h2>{title}</h2>
              <p>{text}</p>
            </article>
          ))}
        </div>
        <div className="preview-footer">
          <Sparkles size={16} /> Powered by Gemini + Groq when configured. Demo
          fixtures are explicitly labeled.
        </div>
      </section>
      <footer className="landing-footer">
        <span>FairModel © 2026</span>
        <span>Built for a future where creators come first.</span>
      </footer>
    </main>
  );
}
