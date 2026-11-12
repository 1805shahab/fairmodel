import { createHash, timingSafeEqual } from "node:crypto";

// A shared demonstration gate, not individual user authentication. The backend
// remains loopback-only in the Render container and retains its ownership checks.
export function hostedAccess(request: Request): Response | null {
  const enabled = process.env.RENDER === "true" || process.env.HOSTED_DEMO === "true";
  if (!enabled) return null;
  const username = process.env.DEMO_ACCESS_USER || "";
  const password = process.env.DEMO_ACCESS_PASSWORD || "";
  const headers = {
    "Cache-Control": "no-store",
    "X-Robots-Tag": "noindex, nofollow",
  };
  if (!username || username.includes(":") || password.length < 24) {
    return new Response("Hosted demo access is not configured. Contact the owner.", {
      status: 503,
      headers,
    });
  }
  const authorization = request.headers.get("authorization") || "";
  const supplied = authorization.startsWith("Basic ")
    ? authorization.slice(6)
    : "";
  const expected = Buffer.from(`${username}:${password}`, "utf8").toString("base64");
  const digest = (value: string) => createHash("sha256").update(value).digest();
  if (!timingSafeEqual(digest(supplied), digest(expected))) {
    return new Response("Sign in with the shared FairModel demo credentials.", {
      status: 401,
      headers: {
        ...headers,
        "WWW-Authenticate": 'Basic realm="FairModel demo", charset="UTF-8"',
      },
    });
  }
  if (!["GET", "HEAD", "OPTIONS"].includes(request.method)) {
    const origin = request.headers.get("origin");
    const crossSite = request.headers.get("sec-fetch-site") === "cross-site";
    let wrongOrigin = false;
    if (origin) {
      try {
        wrongOrigin = new URL(origin).host !== request.headers.get("host");
      } catch {
        wrongOrigin = true;
      }
    }
    if (crossSite || wrongOrigin) {
      return new Response("Open FairModel directly and retry this action.", {
        status: 403,
        headers,
      });
    }
  }
  return null;
}
