import { BackendRequestError } from "../../lib/backend-error";

export function getGenerationErrorMessage(error: unknown): string {
  if (!(error instanceof BackendRequestError)) {
    return "Generation failed unexpectedly. Try again.";
  }

  if (error.code === "http-error" && error.status === 429) {
    const retryMessage =
      error.retryAfterSeconds === undefined
        ? "Try again shortly."
        : `Try again in ${error.retryAfterSeconds} second${error.retryAfterSeconds === 1 ? "" : "s"}.`;
    return `${error.message} ${retryMessage}`;
  }

  if (error.code === "unauthorized") {
    return "The API rejected these credentials. Check that the frontend and backend BASIC_AUTH settings match.";
  }

  if (error.code === "http-error" && error.status === 422) {
    return "Check the prompt and optional instructions, then try again.";
  }

  if (error.code === "timeout") {
    return "The generation timed out. Try again or increase the generation timeout.";
  }

  if (error.code === "unavailable") {
    return "The API is unavailable. Start the FastAPI server and try again.";
  }

  return error.message;
}
