import { describe, expect, it } from "vitest";

import vectors from "../../../contracts/basic-auth-vectors.json";
import {
  credentialsArePortable,
  verifyBasicAuthorization,
} from "./basic-auth";

const expectedCredentials = {
  username: "test-user",
  password: "test-password",
};

function basicAuthorization(username: string, password: string): string {
  return `Basic ${Buffer.from(`${username}:${password}`, "utf8").toString("base64")}`;
}

describe("credentialsArePortable", () => {
  it.each(vectors.credentials)(
    "matches the shared cross-runtime contract for $username",
    ({ username, password, portable }) => {
      expect(credentialsArePortable({ username, password })).toBe(portable);
    },
  );
});

describe("verifyBasicAuthorization", () => {
  it("accepts the configured username and password", () => {
    expect(
      verifyBasicAuthorization(
        basicAuthorization("test-user", "test-password"),
        expectedCredentials,
      ),
    ).toBe(true);
  });

  it.each([
    basicAuthorization("wrong-user", "test-password"),
    basicAuthorization("test-user", "wrong-password"),
    "Bearer token",
    "Basic not-base64!",
    null,
  ])("rejects invalid authorization", (authorization) => {
    expect(verifyBasicAuthorization(authorization, expectedCredentials)).toBe(false);
  });
});
