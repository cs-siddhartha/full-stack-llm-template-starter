export type BackendErrorCode =
  | "unauthorized"
  | "http-error"
  | "timeout"
  | "unavailable"
  | "invalid-response";

export class BackendRequestError extends Error {
  constructor(
    public readonly code: BackendErrorCode,
    message: string,
    public readonly status?: number,
    public readonly retryAfterSeconds?: number,
  ) {
    super(message);
    this.name = "BackendRequestError";
  }
}
