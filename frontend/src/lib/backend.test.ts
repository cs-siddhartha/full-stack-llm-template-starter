import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
vi.mock("./server-config", () => ({
  getBackendConfig: () => ({
    url: "https://backend.example.com",
    readTimeoutMs: 5000,
    generationTimeoutMs: 60000,
  }),
}));

import {
  createGeneration,
  getBackendHealth,
  getPublicConfig,
} from "./backend";
import { BackendRequestError } from "./backend-error";

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

function jsonResponse(value: unknown, init?: ResponseInit): Response {
  return new Response(JSON.stringify(value), {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
}

describe("backend reads", () => {
  it("uses the generated health path and validates its response", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        status: "healthy",
        service: "Test API",
        version: "1.2.3",
        environment: "test",
      }),
    );

    await expect(getBackendHealth()).resolves.toMatchObject({
      status: "healthy",
      service: "Test API",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "https://backend.example.com/api/v1/health",
      expect.objectContaining({ cache: "no-store" }),
    );
  });

  it("forwards authorization to the generated config path", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        generation_provider: "demo",
        generation_model: "demo-v1",
        rate_limit_requests: 10,
        rate_limit_window_seconds: 60,
      }),
    );

    await getPublicConfig("Basic credential");

    const [, init] = fetchMock.mock.calls[0];
    expect(fetchMock.mock.calls[0][0]).toBe(
      "https://backend.example.com/api/v1/config",
    );
    expect(new Headers(init?.headers).get("Authorization")).toBe(
      "Basic credential",
    );
  });
});

describe("generation requests", () => {
  it("serializes input and validates the provider-neutral response", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        {
          id: "gen_test",
          provider: "demo",
          model: "demo-v1",
          output: "Hello",
          usage: { input_characters: 5, output_characters: 5 },
        },
        { status: 201 },
      ),
    );

    await expect(
      createGeneration({ prompt: "Hello" }, "Basic credential"),
    ).resolves.toMatchObject({ id: "gen_test", output: "Hello" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("https://backend.example.com/api/v1/generations");
    expect(init?.method).toBe("POST");
    expect(init?.body).toBe(JSON.stringify({ prompt: "Hello" }));
    const headers = new Headers(init?.headers);
    expect(headers.get("Authorization")).toBe("Basic credential");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("preserves documented rate-limit retry metadata", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        { detail: "Rate limit exceeded" },
        { status: 429, headers: { "Retry-After": "7" } },
      ),
    );

    const error = await createGeneration(
      { prompt: "Hello" },
      "Basic credential",
    ).catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(BackendRequestError);
    expect(error).toMatchObject({
      code: "http-error",
      status: 429,
      retryAfterSeconds: 7,
    });
  });
});

describe("backend failures", () => {
  it.each([
    [401, "unauthorized"],
    [422, "http-error"],
    [500, "http-error"],
  ])("classifies HTTP %s responses", async (status, code) => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "failure" }, { status }));

    await expect(getBackendHealth()).rejects.toMatchObject({ code, status });
  });

  it("distinguishes timeouts from unavailable transports", async () => {
    fetchMock.mockRejectedValueOnce(new DOMException("timed out", "TimeoutError"));
    await expect(getBackendHealth()).rejects.toMatchObject({ code: "timeout" });

    fetchMock.mockRejectedValueOnce(new TypeError("connection refused"));
    await expect(getBackendHealth()).rejects.toMatchObject({
      code: "unavailable",
    });
  });

  it("rejects malformed JSON", async () => {
    fetchMock.mockResolvedValue(new Response("not-json"));

    await expect(getBackendHealth()).rejects.toMatchObject({
      code: "invalid-response",
    });
  });

  it("rejects valid JSON with the wrong response shape", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ status: "healthy" }));

    await expect(getBackendHealth()).rejects.toMatchObject({
      code: "invalid-response",
    });
  });

  it.each([
    {
      request: () => getPublicConfig("Basic credential"),
      payload: {
        generation_provider: "demo",
        generation_model: "demo-v1",
        rate_limit_requests: 1.5,
        rate_limit_window_seconds: 60,
      },
    },
    {
      request: () => createGeneration({ prompt: "Hello" }, "Basic credential"),
      payload: {
        id: "gen_test",
        provider: "demo",
        model: "demo-v1",
        output: "Hello",
        usage: { input_characters: -1, output_characters: 5 },
      },
    },
  ])("rejects numeric values outside the generated response schema", async ({
    request,
    payload,
  }) => {
    fetchMock.mockResolvedValue(jsonResponse(payload));

    await expect(request()).rejects.toMatchObject({ code: "invalid-response" });
  });
});
