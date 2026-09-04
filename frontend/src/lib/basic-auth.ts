import { createHash, timingSafeEqual } from "node:crypto";

export type BasicCredentials = {
  username: string;
  password: string;
};

/** Restricts credentials to the portable character set accepted by both app tiers. */
function isPrintableAscii(value: string): boolean {
  return (
    value.length > 0 &&
    Array.from(value).every((character) => {
      const codePoint = character.codePointAt(0);
      return codePoint !== undefined && codePoint >= 0x20 && codePoint <= 0x7e;
    })
  );
}

/** Loads explicit server-only credentials and fails closed on invalid configuration. */
export function getConfiguredBasicCredentials(): BasicCredentials | null {
  const username = process.env.BASIC_AUTH_USERNAME;
  const password = process.env.BASIC_AUTH_PASSWORD;

  if (
    !username ||
    !password ||
    username.includes(":") ||
    !isPrintableAscii(username) ||
    !isPrintableAscii(password)
  ) {
    return null;
  }

  return { username, password };
}

/** Parses the HTTP Basic payload without accepting another authorization scheme. */
function parseBasicAuthorization(
  authorization: string | null,
): BasicCredentials | null {
  if (!authorization) {
    return null;
  }

  const match = /^Basic[\t ]+([A-Za-z0-9+/]+={0,2})$/i.exec(
    authorization.trim(),
  );
  if (!match) {
    return null;
  }

  const decoded = Buffer.from(match[1], "base64").toString("utf8");
  const separatorIndex = decoded.indexOf(":");
  if (separatorIndex < 0) {
    return null;
  }

  return {
    username: decoded.slice(0, separatorIndex),
    password: decoded.slice(separatorIndex + 1),
  };
}

/** Hashes variable-length secrets before comparing fixed-size buffers in constant time. */
function secretsMatch(actual: string, expected: string): boolean {
  const actualDigest = createHash("sha256").update(actual, "utf8").digest();
  const expectedDigest = createHash("sha256").update(expected, "utf8").digest();
  return timingSafeEqual(actualDigest, expectedDigest);
}

/** Verifies both credential fields even when one comparison has already failed. */
export function verifyBasicAuthorization(
  authorization: string | null,
  expected: BasicCredentials | null = getConfiguredBasicCredentials(),
): boolean {
  const supplied = parseBasicAuthorization(authorization);
  if (!supplied || !expected) {
    return false;
  }

  const usernameMatches = secretsMatch(supplied.username, expected.username);
  const passwordMatches = secretsMatch(supplied.password, expected.password);
  return usernameMatches && passwordMatches;
}
