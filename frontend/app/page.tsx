import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  AudioLines,
  Check,
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
        <Link className="button secondary" href="/control-room">
          Open control room <ArrowRight size={16} />
        </Link>
      </nav>
      <section className="landing-hero">
        <div className="landing-copy">
          <span className="eyebrow">
            <span className="live-dot" /> A FAIRER FUTURE FOR CREATOR VOICES
          </span>
          <h1>
            Every voice
            <br />
            deserves a <span>fair share.</span>
          </h1>
          <p>
            Make AI voice licensing easier to understand—from source-backed
            terms to transparent royalties artists approve.
          </p>
          <div className="button-row">
            <Link className="button" href="/control-room">
              Open control room <ArrowRight size={17} />
            </Link>
            <Link className="text-link" href="/dashboard/settings">
              See how the demo works <ArrowUpRight size={15} />
            </Link>
          </div>
          <div className="landing-trust">
            <span>
              <ShieldCheck size={15} /> Human approval stays in control
            </span>
            <span>
              <AudioLines size={15} /> Usage explained, not guessed
            </span>
          </div>
        </div>
        <div className="landing-art" aria-label="FairModel workflow preview">
          <div className="art-glow" />
          <div className="art-orbit orbit-one" />
          <div className="art-orbit orbit-two" />
          <div className="art-wave" aria-hidden="true">
            {Array.from({ length: 31 }, (_, i) => (
              <span
                key={i}
                style={
                  {
                    "--wave-height": `${18 + Math.abs(Math.sin(i * 0.63)) * (i % 7 === 0 ? 72 : 38)}px`,
                    "--wave-delay": `${i * 22}ms`,
                  } as React.CSSProperties
                }
              />
            ))}
          </div>
          <div className="art-label">
            <span className="art-label-icon">
              <AudioLines size={17} />
            </span>
            <span>
              <strong>Voice rights, made clear.</strong>
              <small>Terms · Usage · Artist approval</small>
            </span>
            <Sparkles size={16} />
          </div>
          <div className="art-review">
            <div className="art-review-top">
              <span className="art-check">
                <Check size={15} />
              </span>
              <span>
                <strong>Ready for artist review</strong>
                <small>Evidence first. People decide.</small>
              </span>
              <span className="art-status">REVIEW</span>
            </div>
            <div className="art-review-rule" />
            <div className="art-review-bottom">
              <span>Agreement terms</span>
              <span>Usage evidence</span>
              <span>Royalty approval</span>
            </div>
          </div>
          <span className="art-caption">
            BUILT FOR CLEARER COLLABORATION
          </span>
        </div>
      </section>
      <section className="landing-preview">
        <div className="preview-header">
          <div>
            <span className="eyebrow">A BETTER WAY TO WORK TOGETHER</span>
            <h2>Clarity at every step.</h2>
          </div>
          <span className="pill blue">Human-approved by design</span>
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
        <span>Demo payments are simulated. No real funds are transferred.</span>
      </footer>
    </main>
  );
}
