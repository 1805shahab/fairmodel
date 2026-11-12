import type { Metadata } from "next";
import "./globals.css";
import "./workspace-theme.css";
import "./experience.css";
import "./stage-theme.css";
import "./passport.css";

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
      <body>{children}</body>
    </html>
  );
}
