import { BackendConfigCard } from "@/components/backend-config-card";
import { BackendStatusCard } from "@/components/backend-status-card";
import { PromptForm } from "@/components/prompt-form";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export const dynamic = "force-dynamic";

/** Composes a static shell around independently streamed backend panels. */
export default function Home() {
  return (
    <main className="min-h-svh bg-muted/30">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-5 py-10 sm:px-8 sm:py-16">
        <header className="max-w-3xl space-y-5">
          <Badge variant="outline">Next.js 16 · FastAPI · shadcn/ui</Badge>
          <div className="space-y-3">
            <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-6xl">
              A server-first base for your next LLM product.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">
              Start with typed API boundaries, streamed Server Components, and a
              replaceable generation provider—without shipping backend details to
              the browser.
            </p>
          </div>
        </header>

        <section aria-labelledby="runtime-heading" className="space-y-5">
          <div className="max-w-2xl space-y-1">
            <h2 id="runtime-heading" className="text-2xl font-semibold tracking-tight">
              Runtime
            </h2>
            <p className="text-sm leading-6 text-muted-foreground">
              These panels fetch independently on the server. Each streams through
              its own Suspense boundary and stable shimmer fallback.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <BackendStatusCard />
            <BackendConfigCard />
          </div>
        </section>

        <section id="playground" aria-labelledby="playground-heading" className="space-y-5">
          <div className="max-w-2xl space-y-1">
            <h2 id="playground-heading" className="text-2xl font-semibold tracking-tight">
              Try the full stack
            </h2>
            <p className="text-sm leading-6 text-muted-foreground">
              The included deterministic provider needs no API key and is ready to
              replace with your preferred LLM SDK.
            </p>
          </div>
          <PromptForm />
        </section>

        <section aria-labelledby="architecture-heading" className="space-y-5">
          <div className="max-w-2xl space-y-1">
            <h2 id="architecture-heading" className="text-2xl font-semibold tracking-tight">
              Reusable by design
            </h2>
            <p className="text-sm leading-6 text-muted-foreground">
              Keep the seams, replace the product-specific pieces.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Server-only API client</CardTitle>
                <CardDescription>No public backend URL or browser fetches.</CardDescription>
              </CardHeader>
              <CardContent className="text-sm leading-6 text-muted-foreground">
                Reads happen in Server Components and mutations use Server Actions.
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Granular streaming</CardTitle>
                <CardDescription>Static content never waits for API data.</CardDescription>
              </CardHeader>
              <CardContent className="text-sm leading-6 text-muted-foreground">
                Add one focused boundary and matching Skeleton for each async panel.
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Provider-neutral backend</CardTitle>
                <CardDescription>Routes depend on a small service protocol.</CardDescription>
              </CardHeader>
              <CardContent className="text-sm leading-6 text-muted-foreground">
                Swap the demo implementation without rewriting the HTTP contract.
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </main>
  );
}
