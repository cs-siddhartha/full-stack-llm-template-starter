import { readFile, writeFile } from "node:fs/promises";

const schemaPath = new URL("../openapi.json", import.meta.url);
const outputPath = new URL(
  "../frontend/src/lib/api-constraints.generated.ts",
  import.meta.url,
);
const schema = JSON.parse(await readFile(schemaPath, "utf8"));
const properties = schema.components.schemas.GenerationCreate.properties;
const promptMinLength = properties.prompt.minLength;
const promptMaxLength = properties.prompt.maxLength;
const instructionsMaxLength = properties.instructions.anyOf.find(
  (candidate) => candidate.type === "string",
)?.maxLength;

if (
  !Number.isInteger(promptMinLength) ||
  !Number.isInteger(promptMaxLength) ||
  !Number.isInteger(instructionsMaxLength)
) {
  throw new Error("GenerationCreate must declare its text limits in OpenAPI.");
}

const output = `// Generated from openapi.json. Do not edit directly.\nexport const generationConstraints = {\n  promptMinLength: ${promptMinLength},\n  promptMaxLength: ${promptMaxLength},\n  instructionsMaxLength: ${instructionsMaxLength},\n} as const;\n`;

if (process.argv.includes("--check")) {
  const current = await readFile(outputPath, "utf8");
  if (current !== output) {
    throw new Error("Generated API constraints are out of date.");
  }
} else {
  await writeFile(outputPath, output, "utf8");
}
