import { createBrowserRouter } from "react-router";

import { AppShell } from "@/components/layout/app-shell";
import { ExamplesPage } from "@/pages/examples-page";
import { HomePage } from "@/pages/home-page";
import { ItemsPage } from "@/pages/items-page";
import { NotFoundPage } from "@/pages/not-found-page";

export const routes = [
  {
    element: <AppShell />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "items", element: <ItemsPage /> },
      { path: "examples", element: <ExamplesPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];

export const router = createBrowserRouter(routes);
