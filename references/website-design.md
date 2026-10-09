# Website design procedure

## Research and art direction
Start with the customer task and observed problem, not a theme. Inspect the existing page and a few current first-party product sites in the same category. Identify useful hierarchy, output presentation, and interaction patterns; do not copy brand assets. Write a short DESIGN.md before implementation: audience and buying moment, primary action, truthful proof, typography, palette, composition, and phone adaptation.

For cluster-owned interfaces use ~/cluster-style/WEB-CRAWLERS-BRAND.md: black, neutral text, electric blue/cyan accents. Product-specific composition still matters. Spider imagery is optional; if used, preserve the rectangular outlined silhouette. Avoid fake dashboards, invented customer logos, decorative charts, and stock images that pretend to show results.

## Compose, don't clone
Choose the layout that makes the product legible: comparison for a checker, an actual waveform/player for audio, readable specimen for a report, or a working canvas for a creative tool. Put concrete proof beside the promise at desktop width and immediately after it on phones. A split hero is one option, not a universal requirement. Do not default to centered headline, three audience cards, three feature cards, and FAQ for every product.

Use a restrained type system with fluid display sizing, tight display leading, comfortable body leading, and bounded paragraph widths. Give sections different visual roles and intentional spacing; repeated identical rounded panels flatten hierarchy. Prefer strong alignment, clear borders, and one dominant accent over gratuitous gradients, glass, shadows, or motion. Start with system fonts when a custom font adds no identity; ensure font fallback and no layout jump if loading fails.

Show one clear primary action and an optional example action. State trial allowance and limitations beside the action. Keep pricing comprehensible in customer units. Don't label a pack popular or recommended without a reason. Show loading, empty, success, insufficient-credit, network-failure, and restore states in the same visual language. Disable duplicate submissions and retain input on errors. Never show success on a failed feedback request.

## Implement for real browsers
Use semantic landmarks, one h1, explicit input labels, logical keyboard order, visible focus, and status announcements. Text contrast target is 4.5:1 for normal text and 3:1 for large text; controls need discernible boundaries. Aim for 44px touch targets (WCAG 2.2 AA minimum is 24px with exceptions). Don't communicate meaning by color alone. Support reduced motion, 200% zoom, long text, and 320px screens. Wide reports need deliberate scrolling or a mobile representation, without page-wide horizontal overflow.

Use modern CSS Grid/Flexbox, clamp(), custom properties, and content-sized layouts. Avoid fixed-height text containers. Keep the initial page small, reserve media dimensions, defer nonessential assets, and use animation only to explain an action. Core Web Vitals good thresholds at the 75th percentile are LCP <=2.5s, INP <=200ms, CLS <=0.1; local screenshots cannot prove field performance.

## Acceptance: observe and repair
Use the host's approved browser capability. Inspect 390px phone and 1440px desktop (plus 320px overflow and zoom where supported). Save screenshots, inspect them, and iterate on crowded or empty areas, hierarchy, alignment, clipping, and contrast. Check initial view, form, actual/example output, pricing, and expanded FAQ, not just the hero.

Exercise primary flow, invalid input, loading/duplicate prevention, output, free-credit display, insufficient credits, restore and feedback errors. Verify keyboard access and focus. Record exact observed coverage and remaining gaps in DESIGN-QA.md. An API verifier doesn't prove browser usability; an attractive hero doesn't prove output readability. Separate laboratory performance from real-user performance, and do not claim complete accessibility conformance from a spot check.

Sources (checked 2026-10-08): https://www.w3.org/TR/WCAG22/ and https://web.dev/articles/defining-core-web-vitals-thresholds . Recheck these when relevant standards or browser behavior changes.
