import { readFile } from "node:fs/promises";
import path from "node:path";
import { hostedAccess } from "@/lib/hosted-access";

export const runtime = "nodejs";

// Fixed, credential-free source artifact. Never accept a user-supplied path.
export async function GET(request: Request) {
  const denied = hostedAccess(request);
  if (denied) return denied;
  try {
    const collection = await readFile(
      path.resolve(
        process.cwd(),
        "../postman/FairModel.postman_collection.json",
      ),
      "utf8",
    );
    return new Response(collection, {
      headers: {
        "Content-Type": "application/json",
        "Content-Disposition":
          'attachment; filename="FairModel.postman_collection.json"',
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return Response.json(
      {
        detail:
          "The local Postman collection is unavailable. Restore the project's postman directory.",
      },
      { status: 503 },
    );
  }
}
