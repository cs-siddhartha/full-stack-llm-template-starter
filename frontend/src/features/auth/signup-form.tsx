"use client";

import { useActionState } from "react";

import { signup, type SignupState } from "./actions";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

const initialState: SignupState = { error: null, success: false };

export function SignupForm() {
  const [state, action, pending] = useActionState(signup, initialState);

  if (state.success) {
    return (
      <Alert>
        <AlertTitle>Check your inbox</AlertTitle>
        <AlertDescription>
          Follow the confirmation link in the email, then return to sign in.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <form action={action} className="grid gap-5">
      <div className="grid gap-2">
        <Label htmlFor="email">Email</Label>
        <input
          autoComplete="email"
          className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          id="email"
          name="email"
          required
          type="email"
        />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="password">Password</Label>
        <input
          autoComplete="new-password"
          className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          id="password"
          minLength={12}
          name="password"
          required
          type="password"
        />
        <p className="text-xs text-muted-foreground">Use at least 12 characters.</p>
      </div>
      <div className="grid gap-2">
        <Label htmlFor="passwordConfirmation">Confirm password</Label>
        <input
          autoComplete="new-password"
          className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          id="passwordConfirmation"
          minLength={12}
          name="passwordConfirmation"
          required
          type="password"
        />
      </div>
      {state.error ? (
        <Alert variant="destructive">
          <AlertTitle>Sign-up failed</AlertTitle>
          <AlertDescription>{state.error}</AlertDescription>
        </Alert>
      ) : null}
      <Button disabled={pending} type="submit">
        {pending ? "Creating account…" : "Create account"}
      </Button>
    </form>
  );
}
