---
name: Verdant Geomatics & Biosphere System
colors:
  surface: '#f9f9ff'
  surface-dim: '#cfdaf1'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eeff'
  surface-container-high: '#dee8ff'
  surface-container-highest: '#d8e3fa'
  on-surface: '#111c2c'
  on-surface-variant: '#414943'
  inverse-surface: '#263142'
  inverse-on-surface: '#ebf1ff'
  outline: '#717973'
  outline-variant: '#c1c8c1'
  surface-tint: '#3e6751'
  primary: '#002817'
  on-primary: '#ffffff'
  primary-container: '#153e2b'
  on-primary-container: '#7fa990'
  inverse-primary: '#a5d0b6'
  secondary: '#1b6d24'
  on-secondary: '#ffffff'
  secondary-container: '#a0f399'
  on-secondary-container: '#217128'
  tertiary: '#2e1f00'
  on-tertiary: '#ffffff'
  tertiary-container: '#493300'
  on-tertiary-container: '#bf9b54'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c0edd1'
  primary-fixed-dim: '#a5d0b6'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#264e3a'
  secondary-fixed: '#a3f69c'
  secondary-fixed-dim: '#88d982'
  on-secondary-fixed: '#002204'
  on-secondary-fixed-variant: '#005312'
  tertiary-fixed: '#ffdea5'
  tertiary-fixed-dim: '#e9c176'
  on-tertiary-fixed: '#261900'
  on-tertiary-fixed-variant: '#5d4201'
  background: '#f9f9ff'
  on-background: '#111c2c'
  surface-variant: '#d8e3fa'
typography:
  headline-xl:
    fontFamily: Playfair Display
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Playfair Display
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Playfair Display
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Playfair Display
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Playfair Display
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Playfair Display
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.06em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.08em
  data-mono:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: -0.01em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 0.75rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

The design system embodies scientific prestige, ecological authority, and refined editorial poise. It is tailored for global researchers, environmental policy directors, climatologists, and geomatics analysts who require uncompromising data legibility without sacrificing sophisticated aesthetics.

Drawing from modern scientific journals, botanical folios, and refined editorial interfaces, the visual personality balances high-contrast academic weight with clean, contemporary software ergonomics. The UI projects poise, empirical accuracy, and institutional longevity. Interaction details favor quiet grace over excessive motion, establishing trust through spacious layouts, meticulous alignment, tactile boundaries, and crisp typographic hierarchies.

## Colors

The palette is rooted in botanical depths and scholarly publication finishes:

- **Primary (`#153E2B` / `#0F2E20`):** Deep Forest Green serves as the primary structural anchor. Used for primary interactive triggers, heavy display typography, navigation sidebars, and critical data focus markers.
- **Secondary (`#2E7D32`):** Botanical Leaf Green acts as the vibrant affirmative accent for positive ecological delta metrics, success indicators, living telemetry pings, and secondary interactive accents.
- **Tertiary (`#C5A059` / `#D4AF37` / `#E5C158`):** Warm Ochre and Gold provide luminous highlighting for key findings, geomatic coordinates, premium data overlays, alert tiers, and analytical chart accents.
- **Neutrals & Surfaces:**
  - Canvas Base: Warm Ivory (`#FBF9F5`) and Parchment Beige (`#F4F1EA`, `#EFECE6`) provide warm, tactile breathing room that reduces ocular fatigue compared to pure white.
  - Text & Slate Accents: Slate Ink (`#2D3748`) and Muted Gray (`#4A5568`) handle primary and secondary body readability, while soft translucent slate borders define surface containment.

## Typography

The typographic hierarchy pairs the editorial authority of Playfair Display with the metric clarity and utilitarian density of Inter.

- **Headlines (Playfair Display):** Conveys academic legacy and environmental editorial weight. Large titles adopt optical kerning, tight tracking, and italicized accents for scientific taxonomy and nomenclature.
- **Body & Data Displays (Inter):** Implements neutral, legible forms across dense statistical tables, geospatial telemetry, and analytical dashboards. Tabular figures (`tnum`) must be enforced on numerical readouts and geographic coordinates.
- **Labels (Inter Caps/Semibold):** Small metadata tags, geomatic layers, and field attributes employ uppercase styling with open letter-spacing to ensure rapid visual triage across satellite and biometric feeds.

## Layout & Spacing

The layout is built upon a 12-column responsive fluid grid designed to accommodate multi-pane geomatic split screens, map viewports, and deep tabular inspection drawers.

- **Desktop (1200px+):** 12 columns with `gutter` (1.5rem / 24px) and outer container `margin` (2rem / 32px). Complex dashboards support persistent left-hand taxonomy navigation alongside multi-panel telemetry inspect windows.
- **Tablet (768px - 1199px):** 8 columns with 1rem gutters and 1.5rem margins. Secondary analytical sidebars collapse into contextual overlay sheets.
- **Mobile (<768px):** 4 columns with `gutter-mobile` (0.75rem / 12px) and `margin-mobile` (1rem / 16px). High-density metric panels collapse into horizontal scroll ribbons or stacked accordion cards.

Spacers adhere to a strict 4px/8px modular rhythm, favoring generous horizontal and vertical breathing room around editorial headers while preserving disciplined, compact data clusters inside sensor tables and charts.

## Elevation & Depth

Visual hierarchy combines warm tonal layers with subtle glassmorphic translucency, reflecting atmospheric depth reminiscent of layered GIS canopy scans:

- **Level 0 (Canvas Base):** Warm Ivory (`#FBF9F5`) flat background providing the foundational un-elevated substrate.
- **Level 1 (Substrate & Cards):** Ivory/Parchment blend (`#F4F1EA`) with an ambient shadow: `0 2px 8px -2px rgba(21, 62, 43, 0.04), 0 1px 3px 0 rgba(21, 62, 43, 0.02)` bounded by a hairline border: `1px solid rgba(45, 55, 72, 0.08)`.
- **Level 2 (Translucent Glass Panes & Overlays):** Used for map toolbars, floating geospatial legends, and filter menus: `background: rgba(251, 249, 245, 0.82)`, `backdrop-filter: blur(12px)`, accompanied by a high-clarity boundary `1px solid rgba(255, 255, 255, 0.65)` layered with `1px solid rgba(21, 62, 43, 0.08)`. Shadow: `0 8px 24px -4px rgba(21, 62, 43, 0.08)`.
- **Level 3 (Modals & Deep Menus):** Pure ivory card stacked above a deep atmospheric scrim (`rgba(15, 46, 32, 0.4)`): shadow `0 20px 40px -8px rgba(15, 46, 32, 0.16)`.

## Shapes

The design system employs a refined radius scale (`roundedness: 2`), applying 0.5rem (8px) as the structural standard. This soft corner geometry offsets the strict rectilinear nature of satellite grids and tabular records while maintaining disciplined architectural rigor.

- **Base Components (Inputs, Buttons, Chips):** `0.5rem` (8px).
- **Cards, Translucent Toolbars, and Metric Modules:** `rounded-lg` at `1rem` (16px).
- **Modals & Flyout Sheets:** `rounded-xl` at `1.5rem` (24px).
- **Pill Indicators & Badges:** Full circular rounding (`9999px`) reserved specifically for live sensor status or discrete quantitative count tags.

## Components

### Buttons
- **Primary:** Deep Forest Green (`#153E2B`) background with crisp warm white text (`#FBF9F5`), 0.5rem corner radius, and subtle inset top highlight. Hover state transitions to darker `#0F2E20` with a subtle elevation increase.
- **Secondary / Scientific:** Warm Ivory surface with a 1px border of `rgba(21, 62, 43, 0.2)` and Slate Ink text (`#2D3748`). Hover introduces a pale green wash (`rgba(21, 62, 43, 0.04)`).
- **Accent (Ochre):** Soft Gold fill (`#C5A059`) with `#0F2E20` text, reserved exclusively for primary analytical export, geospatial bookmarking, and critical data synthesis triggers.

### Chips & Filter Tags
- Compact height (28px), 0.5rem radius, rendered in translucent parchment (`rgba(239, 236, 230, 0.8)`) with slate typography. Active filter states shift to solid Forest Green with ivory text, or Gold ochre borders when designating active geomatic layers.

### Input Fields & Controls
- Form controls rest on an ivory substrate with a recessed 1px perimeter border (`rgba(74, 85, 104, 0.2)`). Focus triggers a dual ring: a crisp 1px `#153E2B` frame surrounded by a soft 3px `#2E7D32` glow at 15% opacity.
- **Checkboxes & Radios:** Forest green active fill with sharp ivory check glyphs. Unchecked states use subtle slate borders on warm parchment.

### Cards & Data Panels
- Metric and biometric readout cards feature 1rem corner radii, translucent ivory fills (`rgba(251, 249, 245, 0.85)`), and fine dual-toned borders.
- Header bands inside cards utilize Playfair Display typography paired with inline tabular coordinates or status pills.

### Geomatic & Data Visualizations
- Map overlays, chart crosshairs, and spatial legends use frosted glass containers with ochre (`#C5A059`) highlight vectors, forest green choropleths, and botanical green (`#2E7D32`) high-vitality indices. Data tooltips enforce monospace tabular digits for exact latitude, longitude, and biomass quantification.