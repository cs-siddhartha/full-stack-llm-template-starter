"use client";

import { useActionState } from "react";

import { flushCache, type CacheFlushState } from "./actions";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const initialState: CacheFlushState = { message: null, ok: false };

export function CacheControl() {
  const [state, action, pending] = useActionState(flushCache, initialState);
  return (
    <Card>
      <CardHeader>
        <CardTitle>Cache</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center gap-4">
        <form action={action}>
          <Button disabled={pending} type="submit" variant="outline">
            {pending ? "Flushing…" : "Flush cache"}
          </Button>
        </form>
        {state.message ? (
          <p className={state.ok ? "text-sm" : "text-sm text-destructive"}>
            {state.message}
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
