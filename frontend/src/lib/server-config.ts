import "server-only";

import {
  type BasicCredentials,
  credentialsArePortable,
} from "./basic-auth";

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";
const DEFAULT_READ_TIMEOUT_MS = 5_000;
const DEFAULT_GENERATION_TIMEOUT_MS = 60_000;

export type BackendConfig = {
  url: string;
  readTimeoutMs: number;
  generationTimeoutMs: number;
};

let cachedBackendConfig: BackendConfig | undefined;
let cachedCredentials: BasicCredentials | null | undefined;

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
  };
  return cachedBackendConfig;
}

export function getConfiguredBasicCredentials(): BasicCredentials | null {
  if (cachedCredentials !== undefined) {
    return cachedCredentials;
  }
  const credentials = {
    username: process.env.BASIC_AUTH_USERNAME ?? "",
    password: process.env.BASIC_AUTH_PASSWORD ?? "",
  };
  cachedCredentials = credentialsArePortable(credentials) ? credentials : null;
  return cachedCredentials;
}
