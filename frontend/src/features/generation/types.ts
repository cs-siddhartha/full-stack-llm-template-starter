import type { GenerationResponse } from "@/lib/backend";

export type GenerationActionState =
  | { status: "idle" }
  | { status: "error"; message: string }
  | { status: "success"; generation: GenerationResponse };

export const initialGenerationState: GenerationActionState = { status: "idle" };
