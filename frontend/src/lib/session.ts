import "server-only";

import { cookies } from "next/headers";

import { getBackendSession } from "./backend";
import { BackendRequestError } from "./backend-error";
import { getBackendConfig } from "./server-config";

export async function getSessionToken(): Promise<string | null> {
  const config = getBackendConfig();
  return (await cookies()).get(config.sessionCookieName)?.value ?? null;
}

export async function setSessionToken(token: string, maxAge: number): Promise<void> {
  const config = getBackendConfig();
  (await cookies()).set(config.sessionCookieName, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge,
    priority: "high",
  });
}

export async function clearSessionToken(): Promise<void> {
  const config = getBackendConfig();
  (await cookies()).delete(config.sessionCookieName);
}

export async function readSession() {
  const token = await getSessionToken();
  if (!token) return null;
  try {
    return await getBackendSession(token);
  } catch (error) {
    if (error instanceof BackendRequestError && error.code === "unauthorized") {
      return null;
    }
    throw error;
  }
}
