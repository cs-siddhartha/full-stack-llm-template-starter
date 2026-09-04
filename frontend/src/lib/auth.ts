import "server-only";

import { headers } from "next/headers";

import { verifyBasicAuthorization } from "@/lib/basic-auth";

/** Revalidates auth at the data boundary and returns the header needed by FastAPI. */
export async function requireBasicAuthorization(): Promise<string> {
  const authorization = (await headers()).get("authorization");

  if (!authorization || !verifyBasicAuthorization(authorization)) {
    throw new Error("HTTP Basic authentication is required.");
  }

  return authorization;
}
