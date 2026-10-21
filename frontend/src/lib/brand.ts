/**
 * Brand colours for code that can't use Tailwind classes, e.g. chart libraries that take
 * colour strings. Values are read from the CSS tokens in index.css, so they follow
 * light/dark mode and there is a single source of truth.
 */

const CHART_TOKENS = ["--chart-1", "--chart-2", "--chart-3", "--chart-4", "--chart-5"] as const;

function token(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** Series colours in brand order: primary palette first, then secondary colours. */
export function chartColors(): string[] {
  return CHART_TOKENS.map(token);
}

/** For CSS-in-JS or SVG `fill`/`stroke`: `var(--chart-1)` etc. These also follow the theme. */
export const chartVars = CHART_TOKENS.map((name) => `var(${name})`);
