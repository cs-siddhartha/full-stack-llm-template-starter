import Link from "next/link";
import { redirect } from "next/navigation";

import { BackendConfigCard } from "@/components/backend-config-card";
import { BackendStatusCard } from "@/components/backend-status-card";
import { Button } from "@/components/ui/button";
import { CacheControl } from "@/features/cache/cache-control";
import { GenerationForm } from "@/features/generation/generation-form";
import { readSession } from "@/lib/session";

export default async function ApplicationPage() {
  const session = await readSession();
  if (!session) redirect("/login");

  return (
    <main className="min-h-svh bg-muted/30">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-5 py-10 sm:px-8">
        <header className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">Application</h1>
            <p className="text-sm text-muted-foreground">
              Signed in as {session.username}
            </p>
          </div>
          <Button
            nativeButton={false}
            render={<Link href="/logout" />}
            variant="outline"
          >
            Sign out
          </Button>
        </header>

        <section aria-labelledby="runtime-heading" className="space-y-4">
          <h2 id="runtime-heading" className="text-2xl font-semibold tracking-tight">
            Runtime
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            <BackendStatusCard />
            <BackendConfigCard />
          </div>
        </section>

        <section aria-labelledby="generation-heading" className="space-y-4">
          <h2 id="generation-heading" className="text-2xl font-semibold tracking-tight">
            Generation
          </h2>
          <GenerationForm />
        </section>

        <section aria-labelledby="cache-heading" className="space-y-4">
          <h2 id="cache-heading" className="text-2xl font-semibold tracking-tight">
            Operations
          </h2>
          <CacheControl />
        </section>
      </div>
    </main>
  );
}
