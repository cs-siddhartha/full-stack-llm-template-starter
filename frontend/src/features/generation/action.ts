"use server";

import { createGeneration } from "@/lib/backend";
import { getGenerationErrorMessage } from "@/features/generation/error-message";
import { parseGenerationFormData } from "@/features/generation/form-data";
import type { GenerationActionState } from "@/features/generation/types";
import { getSessionToken } from "@/lib/session";

export async function generateText(
  _previousState: GenerationActionState,
  formData: FormData,
): Promise<GenerationActionState> {
  const parsedForm = parseGenerationFormData(formData);
  if (!parsedForm.ok) {
    return { status: "error", message: parsedForm.message };
  }

  const token = await getSessionToken();
  if (!token) {
    return { status: "error", message: "Your session has expired." };
  }

  try {
    const generation = await createGeneration(parsedForm.request, token);
    return { status: "success", generation };
  } catch (error) {
    return { status: "error", message: getGenerationErrorMessage(error) };
  }
}
