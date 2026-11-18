import { describe, expect, it } from "vitest";

import { generationConstraints } from "../../lib/api-constraints.generated";
import { generationFormFields, parseGenerationFormData } from "./form-data";

function formData(prompt: FormDataEntryValue, instructions?: FormDataEntryValue) {
  const data = new FormData();
  data.set(generationFormFields.prompt, prompt);
  if (instructions !== undefined) {
    data.set(generationFormFields.instructions, instructions);
  }
  return data;
}

describe("parseGenerationFormData", () => {
  it("normalizes valid text fields", () => {
    expect(parseGenerationFormData(formData("  Hello  ", "  Be brief  "))).toEqual({
      ok: true,
      request: { prompt: "Hello", instructions: "Be brief" },
    });
  });

  it("accepts values exactly at the backend-owned limits", () => {
    const result = parseGenerationFormData(
      formData(
        "p".repeat(generationConstraints.promptMaxLength),
        "i".repeat(generationConstraints.instructionsMaxLength),
      ),
    );

    expect(result.ok).toBe(true);
  });

  it("rejects a prompt below the backend-owned minimum", () => {
    const prompt = "p".repeat(generationConstraints.promptMinLength - 1);

    expect(parseGenerationFormData(formData(prompt))).toMatchObject({
      ok: false,
    });
  });

  it.each([
    [
      "prompt",
      "p".repeat(generationConstraints.promptMaxLength + 1),
      undefined,
      "Keep the prompt at 4,000 characters or fewer.",
    ],
    [
      "instructions",
      "Valid prompt",
      "i".repeat(generationConstraints.instructionsMaxLength + 1),
      "Keep the optional instructions at 2,000 characters or fewer.",
    ],
  ])("rejects %s over the backend-owned limit", (_, prompt, instructions, message) => {
    expect(parseGenerationFormData(formData(prompt, instructions))).toEqual({
      ok: false,
      message,
    });
  });

  it("rejects a blank prompt", () => {
    expect(parseGenerationFormData(formData("   "))).toEqual({
      ok: false,
      message: "Enter a prompt before generating.",
    });
  });
});
