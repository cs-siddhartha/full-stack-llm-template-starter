import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const cookieName = process.env.SESSION_COOKIE_NAME ?? "starter_session";

export function proxy(request: NextRequest) {
  const hasSession = request.cookies.has(cookieName);
  if (request.nextUrl.pathname.startsWith("/app") && !hasSession) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ["/app/:path*"] };
