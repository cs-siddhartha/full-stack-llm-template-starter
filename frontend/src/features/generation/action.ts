"use server";

import { requireBasicAuthorization } from "@/lib/auth";
import { createGeneration } from "@/lib/backend";
import { getGenerationErrorMessage } from "@/features/generation/error-message";
import { parseGenerationFormData } from "@/features/generation/form-data";
import type { GenerationActionState } from "@/features/generation/types";

export async function generateText(
  _previousState: GenerationActionState,
  formData: FormData,
): Promise<GenerationActionState> {
  const parsedForm = parseGenerationFormData(formData);
  if (!parsedForm.ok) {
    return { status: "error", message: parsedForm.message };
  }

  let authorization: string;
  try {
    authorization = await requireBasicAuthorization();
  } catch {
    return {
      status: "error",
      message: "Authentication is required. Reload and sign in before generating.",
    };
  }

  try {
    const generation = await createGeneration(
      parsedForm.request,
      authorization,
    );
    return { status: "success", generation };
  } catch (error) {
    return { status: "error", message: getGenerationErrorMessage(error) };
  }
}
