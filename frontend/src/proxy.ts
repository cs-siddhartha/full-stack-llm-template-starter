import { NextResponse, type NextRequest } from "next/server";

import {
  getConfiguredBasicCredentials,
  verifyBasicAuthorization,
} from "@/lib/basic-auth";

const AUTHENTICATE_HEADER = 'Basic realm="LLM Starter"';

/** Challenges unauthorized page and Server Action requests before application code runs. */
export function proxy(request: NextRequest) {
  const credentials = getConfiguredBasicCredentials();
  if (!credentials) {
    return new Response("Authentication is not configured.", {
      status: 503,
      headers: { "Cache-Control": "no-store" },
    });
  }

  if (
    verifyBasicAuthorization(
      request.headers.get("authorization"),
      credentials,
    )
  ) {
    return NextResponse.next();
  }

  return new Response("Authentication required.", {
    status: 401,
    headers: {
      "Cache-Control": "no-store",
      "WWW-Authenticate": AUTHENTICATE_HEADER,
    },
  });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
