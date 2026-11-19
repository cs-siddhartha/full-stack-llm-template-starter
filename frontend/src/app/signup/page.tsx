import Link from "next/link";
import { redirect } from "next/navigation";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SignupForm } from "@/features/auth/signup-form";
import { readSession } from "@/lib/session";

export default async function SignupPage() {
  if (await readSession()) redirect("/app");
  return (
    <main className="grid min-h-svh place-items-center bg-muted/30 px-5 py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create account</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-5">
          <SignupForm />
          <p className="text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link className="underline" href="/login">
              Sign in
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
