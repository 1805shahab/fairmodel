import { NextRequest, NextResponse } from "next/server";
import { hostedAccess } from "@/lib/hosted-access";

export async function POST(request: NextRequest) {
  const denied = hostedAccess(request);
  if (denied) return denied;
  const { persona } = await request.json();
  if (!["artist_demo", "studio_demo"].includes(persona))
    return NextResponse.json({ detail: "Unknown persona." }, { status: 422 });
  const response = NextResponse.json({ persona, demo_auth: true });
  response.cookies.set("fairmodel-persona", persona, {
    httpOnly: true,
    sameSite: "strict",
    path: "/",
  });
  return response;
}
