import { afterEach, describe, expect, it, vi } from "vitest";

import { api, ApiError } from "@/lib/api";

function mockFetch(
  body: unknown,
  init: { status?: number; contentType?: string; redirected?: boolean } = {},
) {
  const response = new Response(body === undefined ? null : JSON.stringify(body), {
    status: init.status ?? 200,
    headers: { "Content-Type": init.contentType ?? "application/json" },
  });
  Object.defineProperty(response, "redirected", { value: init.redirected ?? false });
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
}

afterEach(() => vi.unstubAllGlobals());

describe("api", () => {
  it("returns parsed JSON", async () => {
    mockFetch({ status: "ok" });
    await expect(api("/health")).resolves.toEqual({ status: "ok" });
    expect(fetch).toHaveBeenCalledWith(
      "/api/health",
      expect.objectContaining({ credentials: "same-origin" }),
    );
  });

  it("raises ApiError with the backend's error body", async () => {
    mockFetch(
      { error: { code: "forbidden", message: "Nope", request_id: "abc" } },
      { status: 403 },
    );
    const error = await api("/items").catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 403,
      code: "forbidden",
      message: "Nope",
      requestId: "abc",
    });
  });

  it("treats a redirect to the login page as an expired session", async () => {
    mockFetch("<html>", { contentType: "text/html", redirected: true });
    await expect(api("/me")).rejects.toMatchObject({ code: "session_expired" });
  });
});
