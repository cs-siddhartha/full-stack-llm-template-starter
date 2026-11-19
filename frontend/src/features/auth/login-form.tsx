"use client";

import { useActionState } from "react";

import { login, loginDemo, type LoginState } from "./actions";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

const initialState: LoginState = { error: null };

export function LoginForm() {
  const [state, action, pending] = useActionState(login, initialState);
  const [demoState, demoAction, demoPending] = useActionState(loginDemo, initialState);

  return (
    <div className="grid gap-5">
      <form action={action} className="grid gap-5">
        <div className="grid gap-2">
          <Label htmlFor="username">Email</Label>
          <input
            autoComplete="email"
            className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            id="username"
            name="username"
            required
            type="email"
          />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="password">Password</Label>
          <input
            autoComplete="current-password"
            className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            id="password"
            name="password"
            required
            type="password"
          />
        </div>
        {state.error ? (
          <Alert variant="destructive">
            <AlertTitle>Login failed</AlertTitle>
            <AlertDescription>{state.error}</AlertDescription>
          </Alert>
        ) : null}
        <Button disabled={pending} type="submit">
          {pending ? "Signing in…" : "Sign in"}
        </Button>
      </form>
      <div className="relative flex items-center justify-center">
        <span className="absolute inset-x-0 border-t" />
        <span className="relative bg-card px-2 text-xs text-muted-foreground">or</span>
      </div>
      <form action={demoAction}>
        <Button className="w-full" disabled={demoPending} type="submit" variant="outline">
          {demoPending ? "Opening demo…" : "Continue with demo account"}
        </Button>
      </form>
      {demoState.error ? (
        <Alert variant="destructive">
          <AlertTitle>Demo login failed</AlertTitle>
          <AlertDescription>{demoState.error}</AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
}
