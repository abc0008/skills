---
name: cfin-nextjs-fdas-app-routes
description: >-
  Reference route shells for the ACEAnalytics nextjs-fdas app — marketing pages,
  product detail routes (forecasting, peer-analysis), root layout, and the CFIN
  workspace. Use when adding or updating app-router pages in cfin_new/nextjs-fdas
  and you need the canonical route entrypoints and layout wiring.
metadata:
  author: alex-cardell
  version: "1.0"
  source: cfin_new/nextjs-fdas/src/app
---

# CFIN nextjs-fdas app routes

Canonical Next.js App Router shells from `cfin_new/nextjs-fdas`.

## Routes included

| Path | File |
| --- | --- |
| `/` (marketing home) | `references/src/app/(marketing)/page.tsx` |
| Marketing chrome | `references/src/app/(marketing)/layout.tsx` |
| `/product` | `references/src/app/(marketing)/product/page.tsx` |
| `/product/forecasting` | `references/src/app/(marketing)/product/forecasting/page.tsx` |
| `/product/peer-analysis` | `references/src/app/(marketing)/product/peer-analysis/page.tsx` |
| Root layout + metadata | `references/src/app/layout.tsx` |
| `/workspace` | `references/src/app/workspace/page.tsx` |
| Workspace shell | `references/src/app/workspace/layout.tsx` |

## Notes

- Marketing pages delegate to `@/components/marketing/*` prototypes; this skill stores route entrypoints only.
- `marketing.css` is included because the marketing layout imports it.
- Source of truth remains `cfin_new/nextjs-fdas`; sync this skill when route wiring changes.
