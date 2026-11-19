import Link from "next/link";
import { redirect } from "next/navigation";

import { LoginForm } from "@/features/auth/login-form";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { readSession } from "@/lib/session";

type LoginPageProps = {
  searchParams: Promise<{ verification?: string }>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  if (await readSession()) redirect("/app");
  const verification = (await searchParams).verification;
  return (
    <main className="grid min-h-svh place-items-center bg-muted/30 px-5">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-5">
          {verification === "verified" ? (
            <Alert>
              <AlertTitle>Email confirmed</AlertTitle>
              <AlertDescription>You can now sign in to your account.</AlertDescription>
            </Alert>
          ) : null}
          {verification === "invalid" ? (
            <Alert variant="destructive">
              <AlertTitle>Confirmation link invalid</AlertTitle>
              <AlertDescription>The link has expired or was already used.</AlertDescription>
            </Alert>
          ) : null}
          <LoginForm />
          <p className="text-sm text-muted-foreground">
            Need an account?{" "}
            <Link className="underline" href="/signup">
              Sign up
            </Link>
          </p>
          <Link className="text-sm text-muted-foreground underline" href="/">
            Return to landing page
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}
