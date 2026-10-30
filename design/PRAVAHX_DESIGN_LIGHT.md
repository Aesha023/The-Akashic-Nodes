# PravahX — Light Design System ("Clear Water")

Visual direction: Apple product pages + Linear/Vercel product craft + calm, trustworthy government-grade clarity.
White, airy, precise. Colour is reserved for water and for status. Everything else is restraint.

This file replaces the colours of `design/stitch/hydrologic_tactical_command/DESIGN.md`.
Keep Stitch's page layouts and navigation; take ALL look-and-feel from this file.

---

## 1. Principles

1. **White space is the luxury.** Generous padding, few borders, one idea per section.
2. **Water is the only loud colour.** Blues carry flood data; status colours carry truth labels. UI chrome stays neutral.
3. **Typography does the hierarchy**, not boxes. Big confident headlines, quiet body text.
4. **Honesty is designed in.** Labels like "Hypothetical scenario", "Tier-0 screening", "NOT RUN", "UNVERIFIED" are first-class, beautiful components, never small grey footnotes.
5. **Motion explains, never decorates.** Every animation shows cause and effect (water spreading, a panel opening from the thing you clicked).
6. **Maps are the hero** inside the app; the chrome floats around them.

---

## 2. Colour tokens (light)

| Token | Hex | Use |
|---|---|---|
| `bg` | `#FFFFFF` | Page background |
| `bg-subtle` | `#F7F8FA` | Section bands, sidebar |
| `bg-muted` | `#EFF1F5` | Inputs, table header, hover |
| `surface` | `#FFFFFF` | Cards |
| `surface-glass` | `rgba(255,255,255,0.72)` + `backdrop-filter: blur(20px) saturate(180%)` | Floating panels over the map, top bar |
| `border` | `#E4E7EC` | Hairlines (1px) |
| `border-strong` | `#D0D5DD` | Inputs, focus base |
| `text` | `#0B1220` | Headlines, primary text |
| `text-secondary` | `#475467` | Body |
| `text-tertiary` | `#667085` | Captions, metadata |
| `brand` | `#0A66FF` | Primary buttons, links, focus ring |
| `brand-hover` | `#0052CC` | |
| `brand-soft` | `#EAF2FF` | Selected nav item, soft button |
| `accent-teal` | `#0EA5A4` | Secondary highlight (sparingly) |

### Status (truth labels) — always icon + text, never colour alone
| Status | Text | Background | Icon |
|---|---|---|---|
| RUN AND PASSED | `#067647` | `#ECFDF3` | check-circle |
| RUN AND FAILED | `#B42318` | `#FEF3F2` | x-circle |
| NOT RUN | `#475467` | `#F2F4F7` | minus-circle |
| PENDING | `#B54708` | `#FFFAEB` | clock |
| UNVERIFIED | `#6941C6` | `#F4F3FF` | help-circle |
| TESTED (unit / live) | `#175CD3` | `#EFF8FF` | beaker |
| Hypothetical scenario (banner) | `#B54708` | `#FFFAEB` | flask |

### Flood depth ramp (sequential, light-map friendly, colour-blind safe)
| Class (m) | Hex |
|---|---|
| 0 – 0.5 | `#D6F0FF` |
| 0.5 – 1.5 | `#8FD0F8` |
| 1.5 – 3 | `#41A6E8` |
| 3 – 5 | `#1874C7` |
| 5 – 8 | `#0B4C99` |
| > 8 | `#062B5F` |
Legend always shows the note: "Depth above DEM water surface; true channel depth is greater."

Other map layers: evacuation route `#12B76A` (4px, white 2px casing); severed road `#F04438` dashed; marooned building `#F79009` outline; extent outline `#0A66FF` 1.5px.

Dark mode: optional, later. Light is the default and the reference.

---

## 3. Typography

- **Display / headlines:** `Inter Display` or `Geist` (both open licence). Do **not** self-host SF Pro on the web; as far as I know its licence restricts use to Apple platforms.
- **Body / UI:** `Inter` (variable), `font-feature-settings: "cv11","ss01","tnum"` for tabular numbers in tables.
- **Mono (hashes, coordinates, run IDs):** `Geist Mono` or `JetBrains Mono`.
- **Hindi:** `Noto Sans Devanagari` (matched weights).

| Style | Size / line | Weight | Tracking |
|---|---|---|---|
| Hero (landing) | 72 / 76 desktop, 44 / 48 mobile | 700 | -0.035em |
| H1 | 48 / 56 | 650 | -0.03em |
| H2 | 32 / 40 | 600 | -0.02em |
| H3 | 22 / 30 | 600 | -0.01em |
| Body L | 18 / 28 | 400 | 0 |
| Body | 15 / 24 | 400 | 0 |
| Small / caption | 13 / 18 | 500 | 0 |
| Overline | 12 / 16 | 600, uppercase | 0.08em |
| Big number (KPI) | 40 / 44 | 600, tabular | -0.02em |

---

## 4. Space, shape, depth

- 8-pt grid; section padding 120px desktop / 64px mobile; card padding 24px.
- Max content width 1200px (landing), full-bleed map in the app.
- Radius: 8 (inputs), 12 (buttons), 16 (cards), 24 (hero media, floating map panels), 999 (pills/badges).
- Shadows (soft, layered, never grey-black blobs):
  - `sm`: `0 1px 2px rgba(16,24,40,0.05)`
  - `md`: `0 4px 12px rgba(16,24,40,0.06), 0 1px 3px rgba(16,24,40,0.04)`
  - `lg` (floating map panels): `0 24px 48px -12px rgba(16,24,40,0.12)`
- Borders: 1px `border`; prefer shadow OR border, not both.

---

## 5. Motion

- Easing: `cubic-bezier(0.22, 1, 0.36, 1)` (ease-out-expo feel); durations 160ms (hover), 240ms (panels), 400–600ms (page/section reveals).
- Landing: scroll-reveal fade + 16px rise, staggered 60ms; hero map shows the **real Ganga Tier-0 extent** filling in (from the API/COG), not a fake animation.
- App: panels slide from the side they belong to; map flies to a clicked feature (`flyTo`, 800ms).
- Respect `prefers-reduced-motion` (disable all non-essential motion).

---

## 6. Components (key ones)

- **Top bar:** glass, 64px, logo left, ⌘K search centre, EN/हिं + user right. Hairline bottom border.
- **Sidebar:** `bg-subtle`, 248px, icon + label, selected item = `brand-soft` pill with `brand` text. Collapsible to 72px icons.
- **Buttons:** Primary (brand fill, white text, radius 12, 44px height), Secondary (white, 1px border), Ghost, Destructive. Focus ring: 3px `rgba(10,102,255,0.35)`.
- **Cards:** white, radius 16, `md` shadow, 24px padding, title + overline.
- **KPI tile:** overline label, big tabular number, small source line ("from run tier0_ganga · VALIDATION §11"). No number without a source line.
- **Status badge:** pill, icon + uppercase text, colours from §2.
- **Scenario banner:** full-width amber strip at top of any result page: "Hypothetical scenario · Tier-0 screening · Precomputed demo run".
- **Not-run state:** greyed card, minus-circle icon, "Not run yet", one-line reason from the API, link to BACKEND_STATUS.
- **Map floating panels:** glass, radius 24, `lg` shadow, 16px from map edges.
- **Tables:** no vertical lines, 52px rows, sticky header `bg-muted`, tabular numbers, row hover `bg-subtle`.
- **Empty / loading:** skeleton shimmer in `bg-muted`; empty states with a short sentence and one action.

---

## 7. Maps (MapLibre, light)

- Basemap: light, low-contrast (Positron-like). For secure/air-gapped mode, self-host vector tiles (e.g. a Protomaps PMTiles "light" style) — no external tile calls.
- Hillshade at 15% opacity for terrain context.
- Labels in English + Hindi where available.
- Flood layers above roads, below labels.

---

## 8. Landing page structure ("award-winning" feel)

1. **Hero:** huge headline ("Know where the water goes. Before it gets there."), one-line subhead, two buttons (Open console / See the validation), and a large live map card showing the real Ganga demo extent.
2. **The problem:** one big number band — "735 of 6,598 dams have an Emergency Action Plan" (with source).
3. **Three tiers:** three tall cards with simple diagrams (seconds / minutes / near-field), each with its honest status badge.
4. **Proof, not promises:** the real Ritter plot (from `docs/img/ritter_t30.png`), engine status table with badges.
5. **Built for:** NDMA/SDMA, dam owners, HADR teams — as audience, not as endorsement. No logos of government bodies.
6. **Footer:** SIH 2026 · PS 26161 · The Akashic Nodes, GitHub link, licence, data attributions (© OpenStreetMap contributors, WorldPop, Copernicus).

---

## 9. Accessibility & quality bar

- WCAG 2.2 AA contrast (all text tokens above pass on white); focus visible everywhere; full keyboard navigation; ARIA labels on map controls.
- Lighthouse ≥ 90 for Performance / Accessibility / Best Practices on the landing page.
- Responsive: mobile (≥360px), laptop, wall display (≥2560px, larger type scale ×1.25).
- Numbers: Indian grouping where shown in Hindi locale; units always shown (m, km², m³/s).
