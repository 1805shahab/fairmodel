import Link from "next/link";
export default function NotFound() {
  return (
    <main className="not-found">
      <h1>This page is outside the workspace.</h1>
      <p>Return to your dashboard to continue.</p>
      <Link className="button" href="/dashboard">
        Open dashboard
      </Link>
    </main>
  );
}
