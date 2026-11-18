import { generationConstraints } from "../../lib/api-constraints.generated";
import type { GenerationRequest } from "../../lib/backend";

export const generationFormFields = {
  prompt: "prompt",
  instructions: "instructions",
} as const;

export type GenerationFormResult =
  | { ok: true; request: GenerationRequest }
  | { ok: false; message: string };

export function parseGenerationFormData(formData: FormData): GenerationFormResult {
  const promptMinLength: number = generationConstraints.promptMinLength;
  const promptValue = formData.get(generationFormFields.prompt);
  if (typeof promptValue !== "string") {
    return { ok: false, message: "Enter a prompt before generating." };
  }
  const prompt = promptValue.trim();
  if (prompt.length < promptMinLength) {
    return {
      ok: false,
      message:
        promptMinLength === 1
          ? "Enter a prompt before generating."
          : `Enter at least ${promptMinLength.toLocaleString("en-US")} prompt characters.`,
    };
  }
  if (prompt.length > generationConstraints.promptMaxLength) {
    return {
      ok: false,
      message: `Keep the prompt at ${generationConstraints.promptMaxLength.toLocaleString("en-US")} characters or fewer.`,
    };
  }

  const instructionsValue = formData.get(generationFormFields.instructions);
  if (instructionsValue !== null && typeof instructionsValue !== "string") {
    return { ok: false, message: "Optional instructions must be text." };
  }
  const instructions = instructionsValue?.trim() || undefined;
  if (
    instructions &&
    instructions.length > generationConstraints.instructionsMaxLength
  ) {
    return {
      ok: false,
      message: `Keep the optional instructions at ${generationConstraints.instructionsMaxLength.toLocaleString("en-US")} characters or fewer.`,
    };
  }

  return { ok: true, request: { prompt, instructions } };
}
