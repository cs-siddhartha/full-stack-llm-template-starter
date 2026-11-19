import "server-only";

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";
const DEFAULT_READ_TIMEOUT_MS = 5_000;
const DEFAULT_GENERATION_TIMEOUT_MS = 60_000;
const DEFAULT_SESSION_COOKIE_NAME = "starter_session";

export type BackendConfig = {
  url: string;
  readTimeoutMs: number;
  generationTimeoutMs: number;
  sessionCookieName: string;
};

let cachedBackendConfig: BackendConfig | undefined;

function readPositiveInteger(name: string, fallback: number): number {
  const value = process.env[name];
  if (value === undefined) {
    return fallback;
  }

  const parsedValue = Number(value);
  if (!Number.isInteger(parsedValue) || parsedValue <= 0) {
    throw new Error(`${name} must be a positive integer.`);
  }
  return parsedValue;
}

function readBackendUrl(): string {
  const value = process.env.BACKEND_URL ?? DEFAULT_BACKEND_URL;
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("BACKEND_URL must use HTTP or HTTPS.");
  }
  if (
    url.username ||
    url.password ||
    url.pathname !== "/" ||
    url.search ||
    url.hash
  ) {
    throw new Error(
      "BACKEND_URL must contain only an HTTP or HTTPS origin.",
    );
  }
  return url.toString().replace(/\/$/, "");
}

export function getBackendConfig(): BackendConfig {
  const sessionCookieName =
    process.env.SESSION_COOKIE_NAME ?? DEFAULT_SESSION_COOKIE_NAME;
  if (!/^[A-Za-z0-9_-]+$/.test(sessionCookieName)) {
    throw new Error("SESSION_COOKIE_NAME contains unsupported characters.");
  }
  cachedBackendConfig ??= {
    url: readBackendUrl(),
    readTimeoutMs: readPositiveInteger(
      "BACKEND_READ_TIMEOUT_MS",
      DEFAULT_READ_TIMEOUT_MS,
    ),
    generationTimeoutMs: readPositiveInteger(
      "BACKEND_GENERATION_TIMEOUT_MS",
      DEFAULT_GENERATION_TIMEOUT_MS,
    ),
    sessionCookieName,
  };
  return cachedBackendConfig;
}
