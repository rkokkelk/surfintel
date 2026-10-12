// The dataviz skill's validated 8-hue categorical theme (references/palette.md) —
// passes the CVD/contrast gates as an ordered set (validated via
// scripts/validate_palette.js). Assign in this fixed order; never cycle past
// 8 — fold any tail into "Overig" instead (see DASHBOARD_SOURCE_CAP on the
// backend, which already does this).
// Resolved as CSS custom properties (app/globals.css) rather than literal hex
// so series colors swap with the light/dark theme automatically — dark mode
// uses its own stepped values there, not an automatic flip of these.
export const CATEGORICAL_PALETTE = [
  "var(--si-cat-1)", // blue
  "var(--si-cat-2)", // orange
  "var(--si-cat-3)", // aqua
  "var(--si-cat-4)", // yellow
  "var(--si-cat-5)", // magenta
  "var(--si-cat-6)", // green
  "var(--si-cat-7)", // violet
  "var(--si-cat-8)", // red
];

export const OTHER_COLOR = "var(--si-cat-other)"; // de-emphasis gray, reserved for "Overig" — never a categorical slot
