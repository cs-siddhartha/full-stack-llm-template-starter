import Link from "next/link";
import { redirect } from "next/navigation";

import { logout } from "@/features/auth/actions";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { readSession } from "@/lib/session";

export default async function LogoutPage() {
  if (!(await readSession())) redirect("/");
  return (
    <main className="grid min-h-svh place-items-center bg-muted/30 px-5">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign out</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-3">
          <form action={logout}>
            <Button type="submit">Sign out</Button>
          </form>
          <Button
            nativeButton={false}
            render={<Link href="/app" />}
            variant="outline"
          >
            Cancel
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
