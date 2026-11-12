import type { Metadata } from "next";
import "./globals.css";
import "./workspace-theme.css";
import "./experience.css";
import "./stage-theme.css";
import "./passport.css";
import "./ledger-theme.css";
import "./layout-refinement.css";

export const metadata: Metadata = {
  title: "FairModel — Every voice deserves a fair share.",
  description:
    "AI voice licensing, explainable compliance and artist-approved royalties. One artist and studio workspace with PayPal Sandbox test payments.",
  other: { "page-type": "software", "site-kind": "software" },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-type="software" suppressHydrationWarning>
      <body>
        {process.env.NEXT_PUBLIC_HOSTED_EPHEMERAL_DEMO === "true" && (
          <aside className="banner warning" role="note">
            Temporary hosted demo: records and uploads may disappear after inactivity,
            restart or redeploy. PayPal invoice writes are disabled. Keep permanent
            evidence in your local FairModel copy.
          </aside>
        )}
        <script
          dangerouslySetInnerHTML={{
            __html: `try{document.documentElement.dataset.theme=localStorage.getItem('fairmodel-theme')==='dark'?'dark':'light'}catch{}`,
          }}
        />
        {children}
      </body>
    </html>
  );
}
