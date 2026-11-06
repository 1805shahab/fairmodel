import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function forward(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  // Only fixed API paths on the configured local backend; never accept caller-supplied destinations.
  if (path.some((part) => !/^[a-zA-Z0-9_-]+$/.test(part))) {
    return Response.json({ detail: "Invalid API path." }, { status: 400 });
  }
  const length = Number(request.headers.get("content-length") || 0);
  if (length > 25 * 1024 * 1024)
    return Response.json({ detail: "Upload exceeds 24 MiB." }, { status: 413 });
  const persona =
    request.cookies.get("fairmodel-persona")?.value || "artist_demo";
  if (!["artist_demo", "studio_demo"].includes(persona))
    return Response.json({ detail: "Invalid demo persona." }, { status: 401 });
  const headers = new Headers({ "X-Demo-Persona": persona });
  for (const name of ["content-type", "range"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  try {
    const hasBody = !["GET", "HEAD"].includes(request.method);
    const response = await fetch(
      `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}/api/${path.join("/")}`,
      {
        method: request.method,
        headers,
        body: hasBody ? await request.arrayBuffer() : undefined,
        cache: "no-store",
        signal: AbortSignal.timeout(180000),
      },
    );
    const outputHeaders = new Headers({
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    });
    for (const key of [
      "content-type",
      "content-disposition",
      "content-length",
      "accept-ranges",
      "content-range",
    ]) {
      const value = response.headers.get(key);
      if (value) outputHeaders.set(key, value);
    }
    return new Response(response.body, {
      status: response.status,
      headers: outputHeaders,
    });
  } catch {
    return Response.json(
      {
        detail:
          "The local API is unavailable or timed out. Start the FastAPI backend and retry.",
      },
      { status: 503 },
    );
  }
}
export { forward as GET, forward as POST, forward as PUT, forward as PATCH };
