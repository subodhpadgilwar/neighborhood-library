import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const TOKEN_COOKIE = "library_token";

export async function POST() {
  const cookieStore = await cookies();
  cookieStore.set(TOKEN_COOKIE, "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 0,
    path: "/",
  });
  return NextResponse.json({ ok: true });
}
