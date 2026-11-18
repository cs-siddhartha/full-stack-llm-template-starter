import { describe, expect, it } from "vitest";

import { BackendRequestError } from "../../lib/backend-error";
import { getGenerationErrorMessage } from "./error-message";

describe("getGenerationErrorMessage", () => {
  it.each([
    [
      new BackendRequestError("unauthorized", "rejected"),
      "The API rejected these credentials. Check that the frontend and backend BASIC_AUTH settings match.",
    ],
    [
      new BackendRequestError("http-error", "invalid", 422),
      "Check the prompt and optional instructions, then try again.",
    ],
    [
      new BackendRequestError("timeout", "timed out"),
      "The generation timed out. Try again or increase the generation timeout.",
    ],
    [
      new BackendRequestError("unavailable", "offline"),
      "The API is unavailable. Start the FastAPI server and try again.",
    ],
    [
      new BackendRequestError("invalid-response", "Unexpected status 500."),
      "Unexpected status 500.",
    ],
    [new Error("unknown"), "Generation failed unexpectedly. Try again."],
  ])("maps backend failures to actionable copy", (error, expected) => {
    expect(getGenerationErrorMessage(error)).toBe(expected);
  });

  it.each([
    [undefined, "The API rate limit was reached. Try again shortly."],
    [1, "The API rate limit was reached. Try again in 1 second."],
    [2, "The API rate limit was reached. Try again in 2 seconds."],
  ])("includes the retry delay when available", (retryAfter, expected) => {
    const error = new BackendRequestError(
      "http-error",
      "The API rate limit was reached.",
      429,
      retryAfter,
    );

    expect(getGenerationErrorMessage(error)).toBe(expected);
  });
});
