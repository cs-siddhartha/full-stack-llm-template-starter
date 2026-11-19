"use client";

import { useActionState } from "react";

import { generateText } from "@/features/generation/action";
import { generationFormFields } from "@/features/generation/form-data";
import { initialGenerationState } from "@/features/generation/types";
import { generationConstraints } from "@/lib/api-constraints.generated";
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

export function GenerationForm() {
  const [state, formAction, isPending] = useActionState(
    generateText,
    initialGenerationState,
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Text generation</CardTitle>
        <CardDescription>
          Submissions run through a Next.js Server Action and FastAPI.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form action={formAction} className="grid gap-5">
          <div className="grid gap-2">
            <Label htmlFor={generationFormFields.prompt}>Prompt</Label>
            <Textarea
              id={generationFormFields.prompt}
              name={generationFormFields.prompt}
              maxLength={generationConstraints.promptMaxLength}
              minLength={generationConstraints.promptMinLength}
              placeholder="Explain retrieval-augmented generation in plain language."
              required
              rows={5}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor={generationFormFields.instructions}>
              Instructions (optional)
            </Label>
            <Textarea
              id={generationFormFields.instructions}
              name={generationFormFields.instructions}
              maxLength={generationConstraints.instructionsMaxLength}
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
