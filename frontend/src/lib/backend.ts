import "server-only";

import type { paths } from "./api.generated";
import { BackendRequestError } from "./backend-error";
import { type BackendConfig, getBackendConfig } from "./server-config";

const apiPaths = {
  demo: "/api/v1/auth/demo",
  login: "/api/v1/auth/login",
  logout: "/api/v1/auth/logout",
  session: "/api/v1/auth/session",
  signup: "/api/v1/auth/signup",
  health: "/api/v1/health",
  config: "/api/v1/config",
  generations: "/api/v1/generations",
  cacheFlush: "/api/v1/cache/flush",
} as const satisfies Record<string, keyof paths>;

type LoginOperation = paths[(typeof apiPaths)["login"]]["post"];
type SignupOperation = paths[(typeof apiPaths)["signup"]]["post"];
type SessionOperation = paths[(typeof apiPaths)["session"]]["get"];
type HealthOperation = paths[(typeof apiPaths)["health"]]["get"];
type ConfigOperation = paths[(typeof apiPaths)["config"]]["get"];
type GenerationOperation = paths[(typeof apiPaths)["generations"]]["post"];
type CacheFlushOperation = paths[(typeof apiPaths)["cacheFlush"]]["post"];

export type LoginRequest = LoginOperation["requestBody"]["content"]["application/json"];
export type SignupRequest = SignupOperation["requestBody"]["content"]["application/json"];
export type SignupResponse = SignupOperation["responses"][201]["content"]["application/json"];
export type SessionResponse = SessionOperation["responses"][200]["content"]["application/json"];
export type HealthResponse = HealthOperation["responses"][200]["content"]["application/json"];
export type PublicConfigResponse = ConfigOperation["responses"][200]["content"]["application/json"];
export type GenerationRequest = GenerationOperation["requestBody"]["content"]["application/json"];
export type GenerationResponse = GenerationOperation["responses"][201]["content"]["application/json"];
export type CacheFlushResponse = CacheFlushOperation["responses"][200]["content"]["application/json"];

function parseRetryAfterSeconds(value: string | null): number | undefined {
  if (!value) return undefined;
  const seconds = Number(value);
  return Number.isFinite(seconds) && seconds >= 0 ? Math.ceil(seconds) : undefined;
}

function createResponseError(response: Response): BackendRequestError {
  return new BackendRequestError(
    response.status === 401 ? "unauthorized" : "http-error",
    `The API request failed with status ${response.status}.`,
    response.status,
    response.status === 429
      ? parseRetryAfterSeconds(response.headers.get("Retry-After"))
      : undefined,
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value);
}

function decodeSession(value: unknown): SessionResponse {
  if (
    !isRecord(value) ||
    typeof value.user_id !== "string" ||
    typeof value.username !== "string" ||
    typeof value.role !== "string"
  ) {
    throw new BackendRequestError("invalid-response", "Invalid session response.");
  }
  return { user_id: value.user_id, username: value.username, role: value.role };
}

function decodeSignup(value: unknown): SignupResponse {
  if (!isRecord(value) || typeof value.message !== "string") {
    throw new BackendRequestError("invalid-response", "Invalid signup response.");
  }
  return { message: value.message };
}

function decodeHealth(value: unknown): HealthResponse {
  if (
    !isRecord(value) ||
    value.status !== "healthy" ||
    typeof value.service !== "string" ||
    typeof value.version !== "string" ||
    typeof value.environment !== "string"
  ) {
    throw new BackendRequestError("invalid-response", "Invalid health response.");
  }
  return {
    status: value.status,
    service: value.service,
    version: value.version,
    environment: value.environment,
  };
}

function decodeConfig(value: unknown): PublicConfigResponse {
  if (
    !isRecord(value) ||
    typeof value.generation_provider !== "string" ||
    typeof value.generation_model !== "string" ||
    !isInteger(value.rate_limit_requests) ||
    !isInteger(value.rate_limit_window_seconds)
  ) {
    throw new BackendRequestError("invalid-response", "Invalid configuration response.");
  }
  return {
    generation_provider: value.generation_provider,
    generation_model: value.generation_model,
    rate_limit_requests: value.rate_limit_requests,
    rate_limit_window_seconds: value.rate_limit_window_seconds,
  };
}

function decodeGeneration(value: unknown): GenerationResponse {
  if (
    !isRecord(value) ||
    typeof value.id !== "string" ||
    typeof value.provider !== "string" ||
    typeof value.model !== "string" ||
    typeof value.output !== "string" ||
    !isRecord(value.usage) ||
    !isInteger(value.usage.input_characters) ||
    value.usage.input_characters < 0 ||
    !isInteger(value.usage.output_characters) ||
    value.usage.output_characters < 0
  ) {
    throw new BackendRequestError("invalid-response", "Invalid generation response.");
  }
  return {
    id: value.id,
    provider: value.provider,
    model: value.model,
    output: value.output,
    usage: {
      input_characters: value.usage.input_characters,
      output_characters: value.usage.output_characters,
    },
  };
}

function decodeCacheFlush(value: unknown): CacheFlushResponse {
  if (!isRecord(value) || !isInteger(value.deleted_keys) || value.deleted_keys < 0) {
    throw new BackendRequestError("invalid-response", "Invalid cache response.");
  }
  return { deleted_keys: value.deleted_keys };
}

function sessionHeaders(token: string, backend: BackendConfig): HeadersInit {
  return { Cookie: `${backend.sessionCookieName}=${encodeURIComponent(token)}` };
}

async function fetchBackend(
  path: keyof paths,
  backend: BackendConfig,
  timeoutMs: number,
  init: RequestInit = {},
): Promise<Response> {
  try {
    const response = await fetch(`${backend.url}${path}`, {
      ...init,
      cache: "no-store",
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!response.ok) throw createResponseError(response);
    return response;
  } catch (error) {
    if (error instanceof BackendRequestError) throw error;
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new BackendRequestError("timeout", "The API request timed out.");
    }
    throw new BackendRequestError("unavailable", "The API is unavailable.");
  }
}

async function readJson<T>(response: Response, decode: (value: unknown) => T): Promise<T> {
  try {
    return decode(await response.json());
  } catch (error) {
    if (error instanceof BackendRequestError) throw error;
    throw new BackendRequestError("invalid-response", "The API returned invalid JSON.");
  }
}

async function readSessionCookie(response: Response): Promise<{
  session: SessionResponse;
  token: string;
  maxAge: number;
}> {
  const backend = getBackendConfig();
  const setCookie = response.headers.get("set-cookie") ?? "";
  const token = new RegExp(`${backend.sessionCookieName}=([^;]+)`).exec(setCookie)?.[1];
  const maxAge = Number(/Max-Age=(\d+)/i.exec(setCookie)?.[1]);
  if (!token || !Number.isInteger(maxAge) || maxAge <= 0) {
    throw new BackendRequestError("invalid-response", "The API omitted the session cookie.");
  }
  return { session: await readJson(response, decodeSession), token, maxAge };
}

export async function loginBackend(input: LoginRequest): Promise<{
  session: SessionResponse;
  token: string;
  maxAge: number;
}> {
  const backend = getBackendConfig();
  const response = await fetchBackend(apiPaths.login, backend, backend.readTimeoutMs, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return readSessionCookie(response);
}

export async function loginDemoBackend(): Promise<{
  session: SessionResponse;
  token: string;
  maxAge: number;
}> {
  const backend = getBackendConfig();
  const response = await fetchBackend(apiPaths.demo, backend, backend.readTimeoutMs, {
    method: "POST",
  });
  return readSessionCookie(response);
}

export async function signupBackend(input: SignupRequest): Promise<SignupResponse> {
  const backend = getBackendConfig();
  return readJson(
    await fetchBackend(apiPaths.signup, backend, backend.readTimeoutMs, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    }),
    decodeSignup,
  );
}

export async function getBackendSession(token: string): Promise<SessionResponse> {
  const backend = getBackendConfig();
  return readJson(
    await fetchBackend(apiPaths.session, backend, backend.readTimeoutMs, {
      headers: sessionHeaders(token, backend),
    }),
    decodeSession,
  );
}

export async function logoutBackend(token: string): Promise<void> {
  const backend = getBackendConfig();
  await fetchBackend(apiPaths.logout, backend, backend.readTimeoutMs, {
    method: "POST",
    headers: sessionHeaders(token, backend),
  });
}

export async function getBackendHealth(): Promise<HealthResponse> {
  const backend = getBackendConfig();
  return readJson(
    await fetchBackend(apiPaths.health, backend, backend.readTimeoutMs),
    decodeHealth,
  );
}

export async function getPublicConfig(token: string): Promise<PublicConfigResponse> {
  const backend = getBackendConfig();
  return readJson(
    await fetchBackend(apiPaths.config, backend, backend.readTimeoutMs, {
      headers: sessionHeaders(token, backend),
    }),
    decodeConfig,
  );
}

export async function createGeneration(
  input: GenerationRequest,
  token: string,
): Promise<GenerationResponse> {
  const backend = getBackendConfig();
  return readJson(
    await fetchBackend(apiPaths.generations, backend, backend.generationTimeoutMs, {
      method: "POST",
      headers: {
        ...sessionHeaders(token, backend),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    }),
    decodeGeneration,
  );
}

export async function flushBackendCache(token: string): Promise<CacheFlushResponse> {
  const backend = getBackendConfig();
  return readJson(
    await fetchBackend(apiPaths.cacheFlush, backend, backend.readTimeoutMs, {
      method: "POST",
      headers: sessionHeaders(token, backend),
    }),
    decodeCacheFlush,
  );
}
