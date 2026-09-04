"use server";

import {
  BackendRequestError,
  createGeneration,
} from "@/lib/backend";
import type { GenerationActionState } from "@/lib/backend-types";
import { requireBasicAuthorization } from "@/lib/auth";

/** Converts an optional form field into a trimmed value without sending empty text. */
function readOptionalText(formData: FormData, field: string): string | undefined {
  const value = formData.get(field);
  if (typeof value !== "string") {
    return undefined;
  }

  return value.trim() || undefined;
}

/** Validates browser input and performs the generation request on the Next.js server. */
export async function generateText(
  _previousState: GenerationActionState,
  formData: FormData,
): Promise<GenerationActionState> {
  let authorization: string;
  try {
    authorization = await requireBasicAuthorization();
  } catch {
    return {
      status: "error",
      message: "Authentication is required. Reload and sign in before generating.",
    };
  }

  const prompt = readOptionalText(formData, "prompt");
  const instructions = readOptionalText(formData, "instructions");

  if (!prompt) {
    return { status: "error", message: "Enter a prompt before generating." };
  }

  if (prompt.length > 4_000) {
    return { status: "error", message: "Keep the prompt under 4,000 characters." };
  }

  if (instructions && instructions.length > 2_000) {
    return {
      status: "error",
      message: "Keep the optional instructions under 2,000 characters.",
    };
  }

  try {
    const generation = await createGeneration(
      { prompt, instructions },
      authorization,
    );
    return { status: "success", generation };
  } catch (error) {
    const message =
      error instanceof BackendRequestError
        ? error.message
        : "Generation failed unexpectedly. Try again.";
    return { status: "error", message };
  }
}
