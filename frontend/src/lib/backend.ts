import "server-only";

import type { paths } from "./api.generated";
import { BackendRequestError } from "./backend-error";
import { type BackendConfig, getBackendConfig } from "./server-config";

const apiPaths = {
  health: "/api/v1/health",
  config: "/api/v1/config",
  generations: "/api/v1/generations",
} as const satisfies Record<string, keyof paths>;

type HealthOperation = paths[(typeof apiPaths)["health"]]["get"];
type ConfigOperation = paths[(typeof apiPaths)["config"]]["get"];
type GenerationOperation = paths[(typeof apiPaths)["generations"]]["post"];

export type HealthResponse = HealthOperation["responses"][200]["content"]["application/json"];
export type PublicConfigResponse = ConfigOperation["responses"][200]["content"]["application/json"];
export type GenerationRequest = GenerationOperation["requestBody"]["content"]["application/json"];
export type GenerationResponse = GenerationOperation["responses"][201]["content"]["application/json"];

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

function createResponseError(response: Response): BackendRequestError {
  if (response.status === 401) {
    return new BackendRequestError(
      "unauthorized",
      "The API rejected the configured credentials.",
      response.status,
    );
  }

  return new BackendRequestError(
    "http-error",
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

function decodeHealth(value: unknown): HealthResponse {
  if (
    !isRecord(value) ||
    value.status !== "healthy" ||
    typeof value.service !== "string" ||
    typeof value.version !== "string" ||
    typeof value.environment !== "string"
  ) {
    throw new BackendRequestError(
      "invalid-response",
      "The health endpoint returned an invalid response.",
    );
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
    throw new BackendRequestError(
      "invalid-response",
      "The configuration endpoint returned an invalid response.",
    );
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
    throw new BackendRequestError(
      "invalid-response",
      "The generation endpoint returned an invalid response.",
    );
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

type BackendRequestOptions<T> = RequestInit & {
  backend: BackendConfig;
  decode: (value: unknown) => T;
  timeoutMs: number;
};

async function requestBackend<T>(
  path: keyof paths,
  { backend, decode, timeoutMs, ...init }: BackendRequestOptions<T>,
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  let response: Response;
  try {
    response = await fetch(`${backend.url}${path}`, {
      ...init,
      cache: "no-store",
      headers,
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new BackendRequestError("timeout", "The API request timed out.");
    }
    throw new BackendRequestError("unavailable", "The API is unavailable.");
  }

  if (!response.ok) {
    throw createResponseError(response);
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new BackendRequestError(
      "invalid-response",
      "The API returned invalid JSON.",
    );
  }
  return decode(payload);
}

export function getBackendHealth(): Promise<HealthResponse> {
  const backend = getBackendConfig();
  return requestBackend(apiPaths.health, {
    backend,
    decode: decodeHealth,
    timeoutMs: backend.readTimeoutMs,
  });
}

export function getPublicConfig(
  authorization: string,
): Promise<PublicConfigResponse> {
  const backend = getBackendConfig();
  return requestBackend(apiPaths.config, {
    backend,
    decode: decodeConfig,
    headers: { Authorization: authorization },
    timeoutMs: backend.readTimeoutMs,
  });
}

export function createGeneration(
  input: GenerationRequest,
  authorization: string,
): Promise<GenerationResponse> {
  const backend = getBackendConfig();
  return requestBackend(apiPaths.generations, {
    backend,
    decode: decodeGeneration,
    method: "POST",
    headers: {
      Authorization: authorization,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
    timeoutMs: backend.generationTimeoutMs,
  });
}
