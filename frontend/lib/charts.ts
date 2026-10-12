// The dataviz skill's validated 8-hue categorical theme (references/palette.md) —
// passes the CVD/contrast gates as an ordered set (validated via
// scripts/validate_palette.js). Assign in this fixed order; never cycle past
// 8 — fold any tail into "Overig" instead (see DASHBOARD_SOURCE_CAP on the
// backend, which already does this).
export const CATEGORICAL_PALETTE = [
  "#2a78d6", // blue
  "#eb6834", // orange
  "#1baf7a", // aqua
  "#eda100", // yellow
  "#e87ba4", // magenta
  "#008300", // green
  "#4a3aa7", // violet
  "#e34948", // red
];

export const OTHER_COLOR = "#9aa3b2"; // de-emphasis gray, reserved for "Overig" — never a categorical slot
