import { ApiError, request, setAccessToken, setSessionExpiredHandler } from "./client";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const tokenBody = {
  access_token: "new-token",
  token_type: "bearer",
  expires_in: 900,
  user: { id: "1", email: "a@b.co", display_name: "A", created_at: "2026-01-01T00:00:00Z" },
};

const unauthorized = () =>
  json({ error: { code: "invalid_token", message: "Invalid or expired token.", request_id: "r1" } }, 401);

beforeEach(() => {
  setAccessToken(null);
  setSessionExpiredHandler(null);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

it("refreshes ONCE for concurrent 401s, then retries both requests", async () => {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (String(url).endsWith("/auth/refresh")) return json(tokenBody);
    const auth = (init?.headers as Record<string, string> | undefined)?.Authorization;
    return auth === "Bearer new-token" ? json({ ok: true }) : unauthorized();
  });
  vi.stubGlobal("fetch", fetchMock);
  setAccessToken("stale-token");

  const [a, b] = await Promise.all([
    request<{ ok: boolean }>("/things"),
    request<{ ok: boolean }>("/things"),
  ]);

  expect(a.ok).toBe(true);
  expect(b.ok).toBe(true);
  const refreshCalls = fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/auth/refresh"));
  expect(refreshCalls).toHaveLength(1);
});

it("signals session expiry and throws when refresh fails", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => unauthorized()));
  const onExpired = vi.fn();
  setSessionExpiredHandler(onExpired);
  setAccessToken("stale-token");

  await expect(request("/things")).rejects.toMatchObject({ status: 401, code: "invalid_token" });
  expect(onExpired).toHaveBeenCalledTimes(1);
});

it("parses the backend error envelope including field details", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      json(
        {
          error: {
            code: "validation_error",
            message: "Request validation failed.",
            request_id: "abc",
            details: [{ field: "email", message: "bad" }],
          },
        },
        422,
      ),
    ),
  );
  const error = (await request("/x", { auth: false }).catch((e: unknown) => e)) as ApiError;
  expect(error).toBeInstanceOf(ApiError);
  expect(error.details).toEqual([{ field: "email", message: "bad" }]);
  expect(error.requestId).toBe("abc");
});

it("reports network failures as a friendly ApiError", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => Promise.reject(new TypeError("Failed to fetch"))));
  await expect(request("/x", { auth: false })).rejects.toMatchObject({ code: "network_error" });
});