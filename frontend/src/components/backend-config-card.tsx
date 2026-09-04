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
import { requireBasicAuthorization } from "@/lib/auth";
import { getPublicConfig } from "@/lib/backend";
import type { PublicConfigResponse } from "@/lib/backend-types";

/** Fetches only safe provider values for the card's suspended data region. */
async function BackendConfigDetails() {
  let config: PublicConfigResponse | null = null;

  try {
    const authorization = await requireBasicAuthorization();
    config = await getPublicConfig(authorization);
  } catch {
    config = null;
  }

  if (!config) {
    return (
      <div className="grid min-h-28 content-start gap-3 text-sm text-muted-foreground">
        <Badge variant="destructive">Unavailable</Badge>
        <p>Check `BACKEND_URL` and confirm the API is running.</p>
      </div>
    );
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
          <dt className="text-muted-foreground">API base</dt>
          <dd className="font-mono text-xs">{config.api_base_path}</dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="text-muted-foreground">Rate limit</dt>
          <dd className="text-right font-medium">
            {config.rate_limit_requests} requests /{" "}
            {config.rate_limit_window_seconds}s
          </dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="text-muted-foreground">Mode</dt>
          <dd className="text-right font-medium">Server only</dd>
        </div>
      </dl>
    </div>
  );
}

/** Renders the static card shell immediately and suspends only provider metadata. */
export function BackendConfigCard() {
  return (
    <Card className="min-h-56">
      <CardHeader>
        <CardTitle>Generation provider</CardTitle>
        <CardDescription>Safe capability metadata from FastAPI.</CardDescription>
      </CardHeader>
      <CardContent>
        <Suspense fallback={<BackendDetailsSkeleton rowCount={4} />}>
          <BackendConfigDetails />
        </Suspense>
      </CardContent>
    </Card>
  );
}
