import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

beforeEach(() => {
  vi.resetModules();
  vi.unstubAllEnvs();
});

describe("getBackendConfig", () => {
  it("normalizes a valid API URL and positive timeouts", async () => {
    vi.stubEnv("BACKEND_URL", "https://api.example.com/");
    vi.stubEnv("BACKEND_READ_TIMEOUT_MS", "2500");
    vi.stubEnv("BACKEND_GENERATION_TIMEOUT_MS", "45000");
    const { getBackendConfig } = await import("./server-config");

    expect(getBackendConfig()).toEqual({
      url: "https://api.example.com",
      readTimeoutMs: 2500,
      generationTimeoutMs: 45000,
      sessionCookieName: "starter_session",
    });
  });

  it.each([
    ["ftp://api.example.com", "must use HTTP or HTTPS"],
    ["https://user:password@api.example.com", "only an HTTP or HTTPS origin"],
    ["https://api.example.com/api/v1", "only an HTTP or HTTPS origin"],
    ["https://api.example.com?tenant=test", "only an HTTP or HTTPS origin"],
  ])("rejects invalid backend API URLs", async (url, message) => {
    vi.stubEnv("BACKEND_URL", url);
    const { getBackendConfig } = await import("./server-config");

    expect(() => getBackendConfig()).toThrow(message);
  });

  it.each(["0", "-1", "1.5", "not-a-number"])(
    "rejects invalid timeout values",
    async (timeout) => {
      vi.stubEnv("BACKEND_READ_TIMEOUT_MS", timeout);
      const { getBackendConfig } = await import("./server-config");

      expect(() => getBackendConfig()).toThrow(
        "BACKEND_READ_TIMEOUT_MS must be a positive integer",
      );
    },
  );
});
