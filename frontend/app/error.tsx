"use client";
export default function ErrorPage({
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <main className="not-found">
      <h1>The workspace hit an unexpected error.</h1>
      <p>Your saved data remains in the local backend.</p>
      <button className="button" onClick={reset}>
        Try again
      </button>
    </main>
  );
}
