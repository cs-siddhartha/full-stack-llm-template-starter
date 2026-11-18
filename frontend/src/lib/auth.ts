import "server-only";

import { headers } from "next/headers";

import { verifyBasicAuthorization } from "@/lib/basic-auth";
import { getConfiguredBasicCredentials } from "@/lib/server-config";

export async function requireBasicAuthorization(): Promise<string> {
  const authorization = (await headers()).get("authorization");
  const credentials = getConfiguredBasicCredentials();

  if (
    !authorization ||
    !credentials ||
    !verifyBasicAuthorization(authorization, credentials)
  ) {
    throw new Error("HTTP Basic authentication is required.");
  }

  return authorization;
}
