import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
vi.mock("./server-config", () => ({
  getBackendConfig: () => ({
    url: "https://backend.example.com",
    readTimeoutMs: 5000,
    generationTimeoutMs: 60000,
    sessionCookieName: "starter_session",
  }),
}));

import {
  createGeneration,
  getBackendHealth,
  getPublicConfig,
  loginDemoBackend,
  loginBackend,
  signupBackend,
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

  it("uses the generated config path", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        generation_provider: "demo",
        generation_model: "demo-v1",
        rate_limit_requests: 10,
        rate_limit_window_seconds: 60,
      }),
    );

    await getPublicConfig("session-token");

    const [, init] = fetchMock.mock.calls[0];
    expect(fetchMock.mock.calls[0][0]).toBe(
      "https://backend.example.com/api/v1/config",
    );
    expect(new Headers(init?.headers).get("Cookie")).toBe(
      "starter_session=session-token",
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
      createGeneration({ prompt: "Hello" }, "session-token"),
    ).resolves.toMatchObject({ id: "gen_test", output: "Hello" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("https://backend.example.com/api/v1/generations");
    expect(init?.method).toBe("POST");
    expect(init?.body).toBe(JSON.stringify({ prompt: "Hello" }));
    const headers = new Headers(init?.headers);
    expect(headers.get("Cookie")).toBe("starter_session=session-token");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("preserves documented rate-limit retry metadata", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        { detail: "Rate limit exceeded" },
        { status: 429, headers: { "Retry-After": "7" } },
      ),
    );

    const error = await createGeneration({ prompt: "Hello" }, "session-token").catch(
      (caught: unknown) => caught,
    );

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
      request: () => getPublicConfig("session-token"),
      payload: {
        generation_provider: "demo",
        generation_model: "demo-v1",
        rate_limit_requests: 1.5,
        rate_limit_window_seconds: 60,
      },
    },
    {
      request: () => createGeneration({ prompt: "Hello" }, "session-token"),
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

  it("extracts the opaque session cookie from login", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        { user_id: "env:local", username: "local", role: "admin" },
        {
          headers: {
            "Set-Cookie":
              "starter_session=opaque-token; HttpOnly; Max-Age=86400; Path=/; SameSite=lax",
          },
        },
      ),
    );

    await expect(
      loginBackend({ username: "local", password: "local-development-only" }),
    ).resolves.toMatchObject({ token: "opaque-token", maxAge: 86400 });
  });

  it("creates a demo session without sending credentials", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        { user_id: "demo:local", username: "demo", role: "demo" },
        {
          headers: {
            "Set-Cookie":
              "starter_session=demo-token; HttpOnly; Max-Age=86400; Path=/; SameSite=lax",
          },
        },
      ),
    );

    await expect(loginDemoBackend()).resolves.toMatchObject({ token: "demo-token" });
    expect(fetchMock).toHaveBeenCalledWith(
      "https://backend.example.com/api/v1/auth/demo",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("submits a registration for email confirmation", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        { message: "Check your email to confirm your account" },
        { status: 201 },
      ),
    );

    await expect(
      signupBackend({
        email: "person@example.com",
        password: "correct-horse-battery-staple",
      }),
    ).resolves.toEqual({ message: "Check your email to confirm your account" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("https://backend.example.com/api/v1/auth/signup");
    expect(init?.method).toBe("POST");
  });
});
