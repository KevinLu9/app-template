import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, expect, it, vi } from "vitest";

import { createQueryClient } from "@/lib/query-client";
import { routes } from "@/router";

afterEach(() => vi.unstubAllGlobals());

it("renders the app shell with navigation and the signed-in user", async () => {
  const user = { user_id: "1", email: "ada@example.com", display_name: "Ada Lovelace", groups: [] };
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify(user), { headers: { "Content-Type": "application/json" } }),
      ),
  );

  render(
    <QueryClientProvider client={createQueryClient()}>
      <RouterProvider router={createMemoryRouter(routes, { initialEntries: ["/"] })} />
    </QueryClientProvider>,
  );

  expect(await screen.findByText("Welcome, Ada Lovelace")).toBeInTheDocument();
  expect(screen.getAllByText("Items").length).toBeGreaterThan(0);
  expect(screen.getByText("OBO vs SP examples")).toBeInTheDocument();
});
