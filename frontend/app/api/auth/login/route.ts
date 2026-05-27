import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
  INTERNAL_API_URL,
  COOKIE_SECURE,
  COOKIE_SAMESITE,
  TOKEN_MAX_AGE_SECONDS,
} from "@/lib/serverEnv";
import { BACKEND_API_V1_PREFIX } from "@/lib/apiConfig";

const TOKEN_COOKIE = "library_token";

export async function POST(request: Request) {
  let body: { email: string; password: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ message: "Invalid request body" }, { status: 400 });
  }

  const { email, password } = body;
  if (!email || !password) {
    return NextResponse.json(
      { message: "Email and password are required" },
      { status: 400 },
    );
  }

  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  let backendRes: Response;
  try {
    backendRes = await fetch(`${INTERNAL_API_URL}${BACKEND_API_V1_PREFIX}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
    });
  } catch {
    return NextResponse.json(
      { message: "Unable to reach authentication service" },
      { status: 503 },
    );
  }

  if (!backendRes.ok) {
    let message = "Invalid email or password";
    try {
      const err = await backendRes.json();
      if (typeof err?.message === "string") message = err.message;
    } catch {
      /* ignore parse errors */
    }
    return NextResponse.json({ message }, { status: backendRes.status });
  }

  let tokenData: { access_token: string };
  try {
    tokenData = await backendRes.json();
  } catch {
    return NextResponse.json(
      { message: "Unexpected response from auth service" },
      { status: 502 },
    );
  }

  const cookieStore = await cookies();
  cookieStore.set(TOKEN_COOKIE, tokenData.access_token, {
    httpOnly: true,
    secure: COOKIE_SECURE,
    sameSite: COOKIE_SAMESITE,
    maxAge: TOKEN_MAX_AGE_SECONDS,
    path: "/",
  });

  return NextResponse.json({ ok: true });
}
