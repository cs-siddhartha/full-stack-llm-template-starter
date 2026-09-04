import { Suspense } from "react";

import { BackendDetailsSkeleton } from "@/components/backend-card-skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getBackendHealth } from "@/lib/backend";
import type { HealthResponse } from "@/lib/backend-types";

/** Fetches only the dynamic readiness rows rendered inside the card boundary. */
async function BackendStatusDetails() {
  let health: HealthResponse | null = null;

  try {
    health = await getBackendHealth();
  } catch {
    health = null;
  }

  if (!health) {
    return (
      <div className="grid min-h-28 content-start gap-3 text-sm text-muted-foreground">
        <Badge variant="destructive">Offline</Badge>
        <p>Start the backend on port 8000, then refresh this page.</p>
      </div>
    );
  }

  return (
    <div className="grid min-h-28 content-start gap-3">
      <Badge variant="secondary">Healthy</Badge>
      <dl className="grid gap-3 text-sm">
        <div className="flex items-center justify-between gap-4">
          <dt className="text-muted-foreground">Service</dt>
          <dd className="text-right font-medium">{health.service}</dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="text-muted-foreground">Environment</dt>
          <dd className="text-right font-medium">{health.environment}</dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="text-muted-foreground">Version</dt>
          <dd className="font-mono text-xs">{health.version}</dd>
        </div>
      </dl>
    </div>
  );
}

/** Renders the static card shell immediately and suspends only live readiness data. */
export function BackendStatusCard() {
  return (
    <Card className="min-h-56">
      <CardHeader>
        <CardTitle>Backend status</CardTitle>
        <CardDescription>Live readiness from the FastAPI service.</CardDescription>
      </CardHeader>
      <CardContent>
        <Suspense fallback={<BackendDetailsSkeleton />}>
          <BackendStatusDetails />
        </Suspense>
      </CardContent>
    </Card>
  );
}
