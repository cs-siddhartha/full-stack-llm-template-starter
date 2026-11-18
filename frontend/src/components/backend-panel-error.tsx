import { Badge } from "@/components/ui/badge";
import type { BackendRequestError } from "@/lib/backend-error";

const failureCopy = {
  unauthorized: {
    label: "Credentials rejected",
    message: "Check that the frontend and backend Basic Auth settings match.",
  },
  timeout: {
    label: "Timed out",
    message: "The backend did not respond within the configured timeout.",
  },
  unavailable: {
    label: "Offline",
    message: "Start the FastAPI service, then refresh this page.",
  },
  "invalid-response": {
    label: "Unexpected response",
    message: "The backend returned a response the frontend could not use.",
  },
  "http-error": {
    label: "Backend error",
    message: "The backend rejected the request.",
  },
} as const;

export function BackendPanelError({ error }: { error: BackendRequestError }) {
  const copy = failureCopy[error.code];
  return (
    <div className="grid min-h-28 content-start gap-3 text-sm text-muted-foreground">
      <Badge variant="destructive">{copy.label}</Badge>
      <p>{copy.message}</p>
    </div>
  );
}
