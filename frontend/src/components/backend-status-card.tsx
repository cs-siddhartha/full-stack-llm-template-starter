import { Suspense } from "react";

import { BackendDetailsSkeleton } from "@/components/backend-card-skeleton";
import { BackendPanelError } from "@/components/backend-panel-error";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getBackendHealth } from "@/lib/backend";
import { BackendRequestError } from "@/lib/backend-error";

async function BackendStatusDetails() {
  let health: Awaited<ReturnType<typeof getBackendHealth>>;
  try {
    health = await getBackendHealth();
  } catch (error) {
    if (error instanceof BackendRequestError) {
      return <BackendPanelError error={error} />;
    }
    throw error;
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
