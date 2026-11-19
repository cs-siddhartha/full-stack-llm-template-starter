"use server";

import { flushBackendCache } from "@/lib/backend";
import { BackendRequestError } from "@/lib/backend-error";
import { getSessionToken } from "@/lib/session";

export type CacheFlushState = { message: string | null; ok: boolean };

export async function flushCache(
  _state: CacheFlushState,
): Promise<CacheFlushState> {
  void _state;
  const token = await getSessionToken();
  if (!token) return { ok: false, message: "Your session has expired." };
  try {
    const result = await flushBackendCache(token);
    return { ok: true, message: `Deleted ${result.deleted_keys} cache keys.` };
  } catch (error) {
    if (error instanceof BackendRequestError && error.code === "unauthorized") {
      return { ok: false, message: "Your session has expired." };
    }
    return { ok: false, message: "The cache could not be flushed." };
  }
}
