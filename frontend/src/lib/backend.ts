import "server-only";

import type {
  GenerationResponse,
  HealthResponse,
  PublicConfigResponse,
} from "@/lib/backend-types";

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";
const DEFAULT_API_PREFIX = "/api/v1";
const DEFAULT_READ_TIMEOUT_MS = 5_000;
const DEFAULT_GENERATION_TIMEOUT_MS = 60_000;

/** Preserves an optional HTTP status while exposing a safe message to the UI. */
export class BackendRequestError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly retryAfterSeconds?: number,
  ) {
    super(message);
    this.name = "BackendRequestError";
  }
}

/** Converts either Retry-After wire format into a non-negative client wait. */
function parseRetryAfterSeconds(value: string | null): number | undefined {
  if (!value) {
    return undefined;
  }

  const delaySeconds = Number(value);
  if (Number.isFinite(delaySeconds) && delaySeconds >= 0) {
    return Math.ceil(delaySeconds);
  }

  const retryAt = Date.parse(value);
  if (Number.isNaN(retryAt)) {
    return undefined;
  }

  return Math.max(0, Math.ceil((retryAt - Date.now()) / 1_000));
}

/** Maps backend auth and throttling failures to safe, actionable UI messages. */
function createResponseError(response: Response): BackendRequestError {
  if (response.status === 401) {
    return new BackendRequestError(
      "The API rejected these credentials. Check that the frontend and backend BASIC_AUTH settings match.",
      response.status,
    );
  }

  if (response.status === 429) {
    const retryAfterSeconds = parseRetryAfterSeconds(
      response.headers.get("Retry-After"),
    );
    const retryMessage =
      retryAfterSeconds === undefined
        ? "Try again shortly."
        : `Try again in ${retryAfterSeconds} second${retryAfterSeconds === 1 ? "" : "s"}.`;

    return new BackendRequestError(
      `The API rate limit was reached. ${retryMessage}`,
      response.status,
      retryAfterSeconds,
    );
  }

  return new BackendRequestError(
    `The API request failed with status ${response.status}.`,
    response.status,
  );
}

/** Normalizes the private backend origin so route composition never creates // paths. */
function getBackendUrl(): string {
  return (process.env.BACKEND_URL ?? DEFAULT_BACKEND_URL).replace(/\/$/, "");
}

/** Keeps the frontend route prefix aligned with a customized FastAPI deployment. */
function getApiPrefix(): string {
  const configuredPrefix = process.env.BACKEND_API_PREFIX ?? DEFAULT_API_PREFIX;
  const withLeadingSlash = configuredPrefix.startsWith("/")
    ? configuredPrefix
    : `/${configuredPrefix}`;
  return withLeadingSlash.replace(/\/$/, "");
}

/** Accepts only positive millisecond overrides and falls back to a safe default. */
function getTimeout(value: string | undefined, fallback: number): number {
  const parsedValue = Number(value);
  return Number.isFinite(parsedValue) && parsedValue > 0 ? parsedValue : fallback;
}

/** Centralizes server-only HTTP behavior and prevents accidental browser API calls. */
async function requestBackend<T>(
  path: string,
  init?: RequestInit,
  timeoutMs = getTimeout(
    process.env.BACKEND_READ_TIMEOUT_MS,
    DEFAULT_READ_TIMEOUT_MS,
  ),
): Promise<T> {
  let response: Response;
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");

  try {
    response = await fetch(`${getBackendUrl()}${path}`, {
      ...init,
      cache: "no-store",
      headers,
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch {
    throw new BackendRequestError(
      "The API is unavailable. Start the FastAPI server and try again.",
    );
  }

  if (!response.ok) {
    throw createResponseError(response);
  }

  return (await response.json()) as T;
}

/** Reads readiness metadata from FastAPI during server rendering. */
export function getBackendHealth(): Promise<HealthResponse> {
  return requestBackend<HealthResponse>(`${getApiPrefix()}/health`);
}

/** Reads only the frontend-safe provider configuration exposed by FastAPI. */
export function getPublicConfig(
  authorization: string,
): Promise<PublicConfigResponse> {
  return requestBackend<PublicConfigResponse>(`${getApiPrefix()}/config`, {
    headers: { Authorization: authorization },
  });
}

/** Sends validated form input to FastAPI without exposing its origin to the browser. */
export function createGeneration(
  input: {
    prompt: string;
    instructions?: string;
  },
  authorization: string,
): Promise<GenerationResponse> {
  return requestBackend<GenerationResponse>(
    `${getApiPrefix()}/generations`,
    {
      method: "POST",
      headers: {
        Authorization: authorization,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    },
    getTimeout(
      process.env.BACKEND_GENERATION_TIMEOUT_MS,
      DEFAULT_GENERATION_TIMEOUT_MS,
    ),
  );
}
