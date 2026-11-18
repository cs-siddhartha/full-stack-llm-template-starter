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
import { requireBasicAuthorization } from "@/lib/auth";
import { getPublicConfig } from "@/lib/backend";
import { BackendRequestError } from "@/lib/backend-error";

async function BackendConfigDetails() {
  let config: Awaited<ReturnType<typeof getPublicConfig>>;
  try {
    const authorization = await requireBasicAuthorization();
    config = await getPublicConfig(authorization);
  } catch (error) {
    if (error instanceof BackendRequestError) {
      return <BackendPanelError error={error} />;
    }
    throw error;
  }

  return (
    <div className="grid min-h-28 content-start gap-3">
      <Badge variant="outline">{config.generation_provider}</Badge>
      <dl className="grid gap-3 text-sm">
        <div className="flex items-center justify-between gap-4">
          <dt className="text-muted-foreground">Model</dt>
          <dd className="font-mono text-xs">{config.generation_model}</dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="text-muted-foreground">Rate limit</dt>
          <dd className="text-right font-medium">
            {config.rate_limit_requests} requests /{" "}
            {config.rate_limit_window_seconds}s
          </dd>
        </div>
      </dl>
    </div>
  );
}

export function BackendConfigCard() {
  return (
    <Card className="min-h-56">
      <CardHeader>
        <CardTitle>Generation provider</CardTitle>
        <CardDescription>Safe capability metadata from FastAPI.</CardDescription>
      </CardHeader>
      <CardContent>
        <Suspense fallback={<BackendDetailsSkeleton />}>
          <BackendConfigDetails />
        </Suspense>
      </CardContent>
    </Card>
  );
}
