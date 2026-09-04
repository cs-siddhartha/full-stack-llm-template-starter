export type HealthResponse = {
  status: "healthy";
  service: string;
  version: string;
  environment: string;
};

export type PublicConfigResponse = {
  service: string;
  version: string;
  environment: string;
  api_base_path: string;
  generation_provider: string;
  generation_model: string;
  rate_limit_requests: number;
  rate_limit_window_seconds: number;
};

export type GenerationResponse = {
  id: string;
  object: "generation";
  provider: string;
  model: string;
  output: string;
  usage: {
    input_characters: number;
    output_characters: number;
  };
};

export type GenerationActionState =
  | { status: "idle" }
  | { status: "error"; message: string }
  | { status: "success"; generation: GenerationResponse };

export const initialGenerationState: GenerationActionState = { status: "idle" };
