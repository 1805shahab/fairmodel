// Local HTTP integration test. No provider keys, real database or external calls.
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const http = require("node:http");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { setTimeout: delay } = require("node:timers/promises");

async function listen(server) {
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  return server.address().port;
}

async function freePort() {
  const server = http.createServer();
  const port = await listen(server);
  await new Promise((resolve) => server.close(resolve));
  return port;
}

async function main() {
  let healthy = true;
  let calls = 0;
  const backend = http.createServer((req, res) => {
    calls++;
    res.setHeader("Content-Type", "application/json");
    if (req.url === "/health") {
      res.statusCode = healthy ? 200 : 503;
      res.end(JSON.stringify({ status: healthy ? "ok" : "unavailable" }));
    } else {
      res.end(JSON.stringify({ source: "local-test-server" }));
    }
  });
  const backendPort = await listen(backend);
  const children = [];
  try {
    for (const configured of [false, true]) {
      const port = await freePort();
      const password = configured ? crypto.randomBytes(32).toString("hex") : "";
      const auth = `Basic ${Buffer.from(`test-owner:${password}`).toString("base64")}`;
      const env = {
        ...process.env,
        RENDER: "true",
        HOSTED_DEMO: "true",
        DEMO_ACCESS_USER: "test-owner",
        DEMO_ACCESS_PASSWORD: password,
        BACKEND_URL: `http://127.0.0.1:${backendPort}`,
        NEXT_TELEMETRY_DISABLED: "1",
      };
      const child = spawn(process.execPath, [
        path.resolve("frontend/node_modules/next/dist/bin/next"),
        "start", "--hostname", "127.0.0.1", "--port", String(port),
      ], { cwd: path.resolve("frontend"), env, stdio: "ignore" });
      children.push(child);
      const base = `http://127.0.0.1:${port}`;
      let ready = false;
      for (let attempt = 0; attempt < 100; attempt++) {
        if (child.exitCode !== null) throw new Error("Local test server exited");
        try {
          const response = await fetch(`${base}/healthz`);
          if (response.status === 200) { ready = true; break; }
        } catch { /* startup */ }
        await delay(200);
      }
      assert(ready, "Health endpoint must become ready");
      for (const route of ["/", "/dashboard", "/api/backend/licenses", "/api/persona", "/api/tools/postman"]) {
        const before = calls;
        const response = await fetch(base + route, { headers: { "x-middleware-subrequest": "proxy:proxy:proxy:proxy:proxy" } });
        assert.equal(response.status, configured ? 401 : 503, route);
        assert.equal(calls, before, "Denied access must not reach API");
        assert.equal(response.headers.get("cache-control"), "no-store");
      }
      if (configured) {
        assert.equal((await fetch(base + "/", { headers: { Authorization: "Basic invalid" } })).status, 401);
        assert.equal((await fetch(base + "/", { headers: { Authorization: auth } })).status, 200);
        const api = await fetch(base + "/api/backend/licenses", { headers: { Authorization: auth } });
        assert.deepEqual(await api.json(), { source: "local-test-server" });
        const postman = await fetch(base + "/api/tools/postman", { headers: { Authorization: auth } });
        assert.equal(postman.status, 200);
        assert((await postman.json()).info, "Credential-free Postman source must be packaged");
        const crossSite = await fetch(base + "/api/persona", {
          method: "POST", headers: { Authorization: auth, Origin: "https://other.example", "Content-Type": "application/json" },
          body: JSON.stringify({ persona: "studio_demo" }),
        });
        assert.equal(crossSite.status, 403);
        const sameSite = await fetch(base + "/api/persona", {
          method: "POST", headers: { Authorization: auth, Origin: base, "Content-Type": "application/json" },
          body: JSON.stringify({ persona: "studio_demo" }),
        });
        assert.equal(sameSite.status, 200);
        healthy = false;
        assert.equal((await fetch(base + "/healthz")).status, 503);
      }
      child.kill();
      await new Promise((resolve) => child.once("exit", resolve));
    }
    console.log("Render access checks passed: closed-by-default, password, API, persona, Postman, origin and health.");
  } finally {
    for (const child of children) if (child.exitCode === null) child.kill();
    backend.closeAllConnections();
    backend.close();
  }
}
main().catch((error) => { console.error(error.message); process.exitCode = 1; });
