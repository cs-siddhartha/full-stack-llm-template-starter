import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { readSession } from "@/lib/session";

export default async function LandingPage() {
  const session = await readSession();
  return (
    <main className="min-h-svh bg-muted/30">
      <div className="mx-auto flex min-h-svh w-full max-w-5xl flex-col justify-center gap-10 px-5 py-16 sm:px-8">
        <header className="max-w-2xl space-y-5">
          <p className="font-mono text-sm text-muted-foreground">Next.js + FastAPI + Redis</p>
          <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
            Full-stack starter
          </h1>
          <p className="text-lg leading-8 text-muted-foreground">
            Cookie sessions, protected API routes, Redis rate limits, namespaced
            caching, generated contracts, and a server-only backend client.
          </p>
          <div className="flex gap-3">
            <Button
              nativeButton={false}
              render={<Link href={session ? "/app" : "/login"} />}
              size="lg"
            >
              {session ? "Open application" : "Sign in"}
            </Button>
            {!session ? (
              <Button
                nativeButton={false}
                render={<Link href="/signup" />}
                size="lg"
                variant="outline"
              >
                Create account
              </Button>
            ) : null}
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-3" aria-label="Included features">
          <Card>
            <CardHeader><CardTitle>Authentication</CardTitle></CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              Redis-backed opaque sessions in HttpOnly cookies.
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Endpoint controls</CardTitle></CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              Reusable rate-limit decorators with atomic Redis counters.
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Cache</CardTitle></CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              Namespaced JSON caching with a protected flush operation.
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
}
