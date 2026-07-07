---
name: Luminous Ledger
colors:
  surface: '#051424'
  surface-dim: '#051424'
  surface-bright: '#2c3a4c'
  surface-container-lowest: '#010f1f'
  surface-container-low: '#0d1c2d'
  surface-container: '#122131'
  surface-container-high: '#1c2b3c'
  surface-container-highest: '#273647'
  on-surface: '#d4e4fa'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#d4e4fa'
  inverse-on-surface: '#233143'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#7bd0ff'
  on-secondary: '#00354a'
  secondary-container: '#00a6e0'
  on-secondary-container: '#00374d'
  tertiary: '#ffb783'
  on-tertiary: '#4f2500'
  tertiary-container: '#d97721'
  on-tertiary-container: '#452000'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#c4e7ff'
  secondary-fixed-dim: '#7bd0ff'
  on-secondary-fixed: '#001e2c'
  on-secondary-fixed-variant: '#004c69'
  tertiary-fixed: '#ffdcc5'
  tertiary-fixed-dim: '#ffb783'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#703700'
  background: '#051424'
  on-background: '#d4e4fa'
  surface-variant: '#273647'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  code-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  container-max: 1200px
  gutter: 20px
---

## Brand & Style
The design system is engineered for a premium, high-trust financial environment. It balances the sophisticated technicality of asset management with a modern, ethereal interface. The goal is to evoke a sense of "digital prestige"—where complex financial data feels light, accessible, and futuristic.

The primary aesthetic is **Glassmorphism**. This style utilizes multi-layered translucency to create a sense of depth and hierarchy without the weight of traditional opaque surfaces. The interface should feel like a series of polished glass panes floating over a deep, shifting void.

**Key visual principles:**
- **Translucency:** Every container must allow the background to peak through via backdrop blurs.
- **Luminosity:** Use vibrant indigo glows to draw attention to interactive elements.
- **Precision:** High-contrast typography and razor-thin borders ensure financial data remains legible and authoritative.

## Colors
This design system utilizes a deep, immersive dark palette to provide the "canvas" for glass effects.

- **Primary (Indigo-500):** Used for critical actions, active states, and focus indicators. It provides a "digital spark" against the dark background.
- **Secondary (Sky-400):** Used for accents, data visualizations, and highlighting specific mutual fund metrics.
- **Background:** A solid `Slate-950` (#020617) or true black base. This must be layered with subtle, slow-moving radial gradient meshes in Indigo and Deep Purple (at 5-10% opacity) to provide the "backlight" for the glass elements.
- **Surfaces:** Use `Slate-900` at varying opacities (60%–80%) combined with `backdrop-blur-md` or `lg`.

## Typography
The system uses **Inter** exclusively to maintain a clean, systematic, and highly legible appearance. 

- **Scale:** Use tight letter-spacing on larger headings to reinforce the premium "editorial" feel.
- **Color:** Headlines should be pure White (#FFFFFF). Body text should be Slate-300 (#CBD5E1) to reduce eye strain and establish hierarchy.
- **Weight:** Use Semi-Bold (600) for interactive labels and Bold (700) for headlines. Regular (400) is reserved for conversational body text in the FAQ assistant.

## Layout & Spacing
The layout follows a fluid 12-column grid for desktop and a single-column stack for mobile. 

- **Margins:** 24px on mobile, 40px on tablet, and auto-centering containers on desktop.
- **Rhythm:** Use an 8px base grid. Glass cards should have generous internal padding (min 24px) to allow the content to "breathe" within the blurred container.
- **Chat Specifics:** The assistant interface should be centered with a max-width of 800px to ensure line lengths remain readable for financial explanations.

## Elevation & Depth
Depth is not communicated through shadows, but through **opacity and blur**.

- **Level 1 (Default):** Background mesh.
- **Level 2 (Cards/Bubbles):** `Slate-900` at 60% opacity, `backdrop-blur-md`, and a 1px border at 10% white opacity.
- **Level 3 (Modals/Popovers):** `Slate-900` at 80% opacity, `backdrop-blur-lg`, and a 1px border at 20% white opacity.
- **Inner Glow:** Elements at Level 2 and 3 should have a subtle top-down "shine"—a linear gradient border from White (20% opacity) at the top to Transparent at the bottom.

## Shapes
The shape language is sophisticated and "Rounded" (0.5rem base). 

- **Cards & Chat Bubbles:** Use `rounded-xl` (1.5rem) to soften the technical nature of the content and make the "glass" feel like molded acrylic.
- **Interactive Elements:** Buttons and input fields use `rounded-lg` (1rem) for a distinct click-target appearance.
- **Selection Indicators:** Use pill-shaped (full round) indicators for tags or fund categories.

## Components
Consistent implementation of glass effects is required across all components.

- **Glass Chat Bubbles:** 
  - *User:* Indigo-600 at 40% opacity, white text, right-aligned.
  - *Assistant:* Slate-900 at 60% opacity, slate-200 text, left-aligned. Both require `backdrop-blur-md` and a 1px border.
- **Sleek Input Fields:** Transparent background with a 1px Slate-700 border. On focus, the border transitions to Indigo-500 with a subtle outer glow (0px 0px 12px rgba(99, 102, 241, 0.3)).
- **Action Buttons:**
  - *Primary:* Solid Indigo-600 with a slight "glass" overlay to keep the texture consistent.
  - *Secondary:* Ghost style with 1px border and 5% white hover fill.
- **Fund Cards:** Feature a top-weighted highlight (the "shine") and high-contrast numerical data. 
- **Micro-animations:** 
  - Chat bubbles should "float" in with a subtle 20px Y-axis slide and opacity fade. 
  - Hovering over a glass card should increase the backdrop-blur intensity slightly and brighten the border opacity.