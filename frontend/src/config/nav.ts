import { FlaskConical, Home, ListChecks, type LucideIcon } from "lucide-react";

export type NavItem = { title: string; to: string; icon: LucideIcon };

/** Sidebar entries. Add a page: create it in src/pages, add a route in router.tsx, list it here. */
export const NAV_ITEMS: NavItem[] = [
  { title: "Home", to: "/", icon: Home },
  { title: "Items", to: "/items", icon: ListChecks },
  { title: "OBO vs SP examples", to: "/examples", icon: FlaskConical },
];
