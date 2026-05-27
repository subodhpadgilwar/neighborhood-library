import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";
import { INTERNAL_API_URL } from "@/lib/serverEnv";
import { BACKEND_API_V1_PREFIX } from "@/lib/apiConfig";

const TOKEN_COOKIE = "library_token";

function resolveRedirectUrl(baseUrl: string, location: string): string {
  try {
    // Absolute redirect
    return new URL(location).toString();
  } catch {
    // Relative redirect
    return new URL(location, baseUrl).toString();
  }
}

async function proxyRequest(
  request: NextRequest,
  params: { path: string[] },
) {
  const cookieStore = await cookies();
  const token = cookieStore.get(TOKEN_COOKIE)?.value;

  // Preserve the original URL path (including trailing slash) instead of
  // rebuilding from params, which can change redirect behavior for some
  // FastAPI routes (notably POST /staff vs /staff/).
  const proxyPrefix = "/api/proxy";
  const pathname = request.nextUrl.pathname.startsWith(proxyPrefix)
    ? request.nextUrl.pathname.slice(proxyPrefix.length)
    : `/${params.path.join("/")}`;
  const normalizedPath = pathname.startsWith("/") ? pathname : `/${pathname}`;
  const search = request.nextUrl.search;
  const backendUrl = `${INTERNAL_API_URL}${BACKEND_API_V1_PREFIX}${normalizedPath}${search}`;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("cookie");
  // Avoid forwarding hop-by-hop / transport headers that can cause undici to throw.
  headers.delete("connection");
  headers.delete("content-length");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let bodyBuffer: ArrayBuffer | null = null;
  let body: BodyInit | null = null;
  if (!["GET", "HEAD"].includes(request.method)) {
    bodyBuffer = await request.arrayBuffer();
    body = bodyBuffer;
  }

  let backendRes: Response;
  try {
    backendRes = await fetch(backendUrl, {
      method: request.method,
      headers,
      body,
      // We handle redirects manually so we can replay the body if needed.
      redirect: "manual",
    });
  } catch {
    return NextResponse.json(
      { status: "error", message: "Unable to reach backend service" },
      { status: 503 },
    );
  }

  // FastAPI may redirect /resource -> /resource/ (307/308). For non-GET methods
  // Node fetch cannot automatically resend the consumed body. Replay manually.
  if (
    (backendRes.status === 307 || backendRes.status === 308) &&
    backendRes.headers.get("location")
  ) {
    const location = backendRes.headers.get("location")!;
    const redirectedUrl = resolveRedirectUrl(backendUrl, location);
    try {
      backendRes = await fetch(redirectedUrl, {
        method: request.method,
        headers,
        body: bodyBuffer,
        redirect: "manual",
      });
    } catch {
      return NextResponse.json(
        { status: "error", message: "Unable to reach backend service" },
        { status: 503 },
      );
    }
  }

  const responseBody = await backendRes.arrayBuffer();
  const responseHeaders = new Headers();
  const ct = backendRes.headers.get("content-type");
  if (ct) responseHeaders.set("content-type", ct);

  return new NextResponse(responseBody, {
    status: backendRes.status,
    headers: responseHeaders,
  });
}

type RouteContext = { params: Promise<{ path: string[] }> };

async function resolveParams(context: RouteContext) {
  return context.params;
}

export const GET = (req: NextRequest, context: RouteContext) =>
  resolveParams(context).then((params) => proxyRequest(req, params));
export const POST = (req: NextRequest, context: RouteContext) =>
  resolveParams(context).then((params) => proxyRequest(req, params));
export const PUT = (req: NextRequest, context: RouteContext) =>
  resolveParams(context).then((params) => proxyRequest(req, params));
export const DELETE = (req: NextRequest, context: RouteContext) =>
  resolveParams(context).then((params) => proxyRequest(req, params));
export const PATCH = (req: NextRequest, context: RouteContext) =>
  resolveParams(context).then((params) => proxyRequest(req, params));
