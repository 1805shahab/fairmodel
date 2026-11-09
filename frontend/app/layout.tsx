import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FairModel — Every voice deserves a fair share.",
  description:
    "AI voice licensing, explainable compliance and artist-approved royalties. Local development demo.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
