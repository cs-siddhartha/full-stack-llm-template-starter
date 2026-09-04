"use client";

import { useActionState } from "react";

import { generateText } from "@/app/actions";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { initialGenerationState } from "@/lib/backend-types";

/** Keeps the interactive surface small while delegating API communication to a Server Action. */
export function PromptForm() {
  const [state, formAction, isPending] = useActionState(
    generateText,
    initialGenerationState,
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Prompt playground</CardTitle>
        <CardDescription>
          This form posts to a Next.js Server Action, which calls FastAPI privately.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form action={formAction} className="grid gap-5">
          <div className="grid gap-2">
            <Label htmlFor="prompt">Prompt</Label>
            <Textarea
              id="prompt"
              name="prompt"
              minLength={1}
              maxLength={4_000}
              placeholder="Explain retrieval-augmented generation in plain language."
              required
              rows={5}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="instructions">Instructions (optional)</Label>
            <Textarea
              id="instructions"
              name="instructions"
              maxLength={2_000}
              placeholder="Keep the answer concise and practical."
              rows={3}
            />
          </div>

          <Button className="w-fit" disabled={isPending} type="submit">
            {isPending ? "Generating…" : "Generate response"}
          </Button>

          {state.status === "error" ? (
            <Alert variant="destructive">
              <AlertTitle>Could not generate</AlertTitle>
              <AlertDescription>{state.message}</AlertDescription>
            </Alert>
          ) : null}

          {state.status === "success" ? (
            <Alert>
              <AlertTitle>
                {state.generation.provider} · {state.generation.model}
              </AlertTitle>
              <AlertDescription className="space-y-2">
                <p className="whitespace-pre-wrap text-foreground">
                  {state.generation.output}
                </p>
                <p className="font-mono text-xs">
                  {state.generation.usage.input_characters} input characters ·{" "}
                  {state.generation.usage.output_characters} output characters
                </p>
              </AlertDescription>
            </Alert>
          ) : null}
        </form>
      </CardContent>
    </Card>
  );
}
