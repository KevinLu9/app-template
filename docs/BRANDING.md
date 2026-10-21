# Branding

Every app built from this template uses the Ventia brand. It is defined once, in `frontend/src/index.css`, as shadcn/ui theme tokens. Components refer to tokens (`bg-primary`, `text-muted-foreground`), never to raw colours. That way the whole app follows the brand and dark mode automatically.

**Don't change the brand per app.** If a token needs to change, change it in the template so every app gets it.

## Colours

| Brand colour | Hex | Token(s) | Use for |
|---|---|---|---|
| Deep green | `#004825` | `primary`, `sidebar`, `chart-1` | Primary buttons, links, the app shell sidebar, the lead chart series |
| Mid green | `#00994D` | `brand`, `ring`, `chart-2` | Focus rings, accents, highlights, the second chart series |
| Feijoa green | `#A0CD60` | `success`, `sidebar-primary`, `chart-5` | Success states, the logo tile in the sidebar |
| Safety yellow | `#F5E646` | `warning` | Warnings and highlights **behind dark text only** |
| Red earth | `#9E3323` | `destructive`, `chart-4` | Errors, destructive actions |
| Plum purple | `#671C32` | `info`, `chart-3` | Informational states |

Tailwind classes exist for every token: `bg-success text-success-foreground`, `border-warning`, `text-info`, `bg-brand` and so on.

```tsx
<Badge className="bg-success text-success-foreground">Approved</Badge>
<Badge className="bg-warning text-warning-foreground">Pending</Badge>
<Alert variant="destructive">…</Alert>
```

### How the palette was adapted

- **shadcn's `secondary` is not the brand's "secondary".** In shadcn, `secondary` is a quiet surface (secondary buttons, badges), so it is a light green tint. The brand's mid green is available as `brand`.
- **No white text on mid green.** The contrast is 3.7:1, which fails WCAG AA for normal text. Use it for accents, focus rings, large text and chart marks, not for text buttons.
- **Yellow and feijoa need dark text.** Their `*-foreground` tokens are dark, giving 13:1 and 9:1.
- **Dark mode** swaps deep green, which has too little contrast on a dark background, for mid green as `primary`, and lightens red earth and plum so they keep AA contrast.

All text/background pairs in the theme meet WCAG AA (4.5:1). Check new combinations before using them.

## Typography

| Typeface | Token / class | Use for |
|---|---|---|
| **Source Serif 4** | `font-heading` | Headlines and main titles. `h1` and `h2` get it automatically. Also quotes and emotive callouts |
| **Inter** | `font-sans` (the default) | Everything else: body copy, subheadings (`h3`+, card titles), numbers, statistics, tables, charts, callouts |

- The fonts are self-hosted from npm (`@fontsource-variable/*`). The app's Content Security Policy blocks font CDNs such as Google Fonts, and self-hosting also works offline and on locked-down networks.
- For numbers that line up in tables and KPIs, add `tabular-nums`.

```tsx
<h1>Asset maintenance</h1>                                  {/* Source Serif 4 */}
<blockquote className="font-heading text-xl italic">…</blockquote>
<p className="text-3xl font-semibold tabular-nums">1,284</p> {/* Inter */}
```

## Charts

Keep charts simple and clean: few series, light gridlines, direct labels where possible, no 3D or decorative effects.

- **Series order:** `chart-1` (deep green), then `chart-2` (mid green), then `chart-3` (plum), then `chart-4` (red earth), then `chart-5` (feijoa). The primary palette always leads; secondary colours are only for additional series.
- **One series?** Use `chart-1`. For two, use `chart-1` and `chart-2`.
- **Feijoa is faint on white** (1.8:1), so it comes last. Give it a visible stroke or a direct label. **Yellow is not a series colour** (1.3:1 on white); use it only to highlight a single point or band.
- **In code:** with Tailwind, use `fill-chart-1`, `stroke-chart-2` and so on. For chart libraries that take colour strings, use `chartColors()` or `chartVars` from `frontend/src/lib/brand.ts`.
- **Inter applies everywhere**, including axis labels and values.

```tsx
import { chartVars } from "@/lib/brand";

<Bar dataKey="completed" fill={chartVars[0]} />
<Bar dataKey="scheduled" fill={chartVars[1]} />
```

## Logo and favicon

`frontend/public/favicon.svg` and the sidebar logo tile (`components/layout/app-sidebar.tsx`) are placeholders in brand colours. Replace them with the official Ventia logo assets from the brand team. Don't redraw the logo.
