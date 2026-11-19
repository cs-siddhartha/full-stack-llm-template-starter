"use server";

import { redirect } from "next/navigation";

import {
  loginBackend,
  loginDemoBackend,
  logoutBackend,
  signupBackend,
} from "@/lib/backend";
import { BackendRequestError } from "@/lib/backend-error";
import {
  clearSessionToken,
  getSessionToken,
  setSessionToken,
} from "@/lib/session";

export type LoginState = { error: string | null };
export type SignupState = { error: string | null; success: boolean };

export async function login(
  _state: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const username = formData.get("username");
  const password = formData.get("password");
  if (typeof username !== "string" || typeof password !== "string") {
    return { error: "Enter an email and password." };
  }

  try {
    const result = await loginBackend({ username: username.trim(), password });
    await setSessionToken(result.token, result.maxAge);
  } catch (error) {
    if (error instanceof BackendRequestError && error.code === "unauthorized") {
      return { error: "Invalid email or password." };
    }
    if (error instanceof BackendRequestError && error.status === 403) {
      return { error: "Confirm your email before signing in." };
    }
    if (error instanceof BackendRequestError && error.status === 429) {
      return { error: "Too many login attempts. Try again shortly." };
    }
    return { error: "Login is unavailable. Check the backend and Redis." };
  }

  redirect("/app");
}

export async function loginDemo(
  _state: LoginState,
  _formData: FormData,
): Promise<LoginState> {
  void _state;
  void _formData;
  try {
    const result = await loginDemoBackend();
    await setSessionToken(result.token, result.maxAge);
  } catch (error) {
    if (error instanceof BackendRequestError && error.status === 429) {
      return { error: "Too many login attempts. Try again shortly." };
    }
    return { error: "Demo login is unavailable." };
  }

  redirect("/app");
}

export async function signup(
  _state: SignupState,
  formData: FormData,
): Promise<SignupState> {
  const email = formData.get("email");
  const password = formData.get("password");
  const passwordConfirmation = formData.get("passwordConfirmation");
  if (
    typeof email !== "string" ||
    typeof password !== "string" ||
    typeof passwordConfirmation !== "string"
  ) {
    return { error: "Complete every field.", success: false };
  }
  if (password.length < 12) {
    return { error: "Use at least 12 characters for your password.", success: false };
  }
  if (password !== passwordConfirmation) {
    return { error: "Passwords do not match.", success: false };
  }

  try {
    await signupBackend({ email: email.trim(), password });
    return { error: null, success: true };
  } catch (error) {
    if (error instanceof BackendRequestError && error.status === 409) {
      return { error: "An account already exists for this email.", success: false };
    }
    if (error instanceof BackendRequestError && error.status === 429) {
      return { error: "Too many sign-up attempts. Try again later.", success: false };
    }
    if (error instanceof BackendRequestError && error.status === 503) {
      return {
        error: "Email delivery is unavailable. Check the Resend configuration.",
        success: false,
      };
    }
    return { error: "Sign-up is unavailable.", success: false };
  }
}

export async function logout(): Promise<void> {
  const token = await getSessionToken();
  if (token) {
    try {
      await logoutBackend(token);
    } catch {
      // The local cookie must still be removed when the backend session has expired.
    }
  }
  await clearSessionToken();
  redirect("/");
}
