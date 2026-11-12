import { NextRequest, NextResponse } from "next/server";
import { hostedAccess } from "./lib/hosted-access";

export function proxy(request: NextRequest) {
  // Only the read-only health probe is public; it returns no private records.
  if (request.nextUrl.pathname === "/healthz") return NextResponse.next();
  return hostedAccess(request) || NextResponse.next();
}
