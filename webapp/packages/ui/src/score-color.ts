// score-color — V22 (task 001) continuous HSL gradient red → green for CRO
// scores. Replaces the 3-state flat token approach (`--gc-red` / `--gc-amber`
// / `--gc-green`) with a smooth continuous color informing the eye at a glance.
//
// Source pattern : V26 HTML `scoreColor(pct)` = `hsl(pct/100 * 120, 65%, 55%)`.
// pct=0 → hsl(0, 65%, 55%) = red
// pct=50 → hsl(60, 65%, 55%) = gold / amber
// pct=100 → hsl(120, 65%, 55%) = green

const HUE_RED = 0;
const HUE_GREEN = 120;
const SAT = 65;
const LIGHT = 55;
const LIGHT_MUTED = 40;

/**
 * Returns an HSL color string interpolating red (0%) → gold (50%) → green (100%).
 * Use directly as CSS color value, e.g. `style={{ color: scoreColor(72) }}`.
 *
 * Clamped to [0, 100]. Non-finite inputs default to muted grey.
 */
export function scoreColor(pct: number): string {
  if (!Number.isFinite(pct)) return "hsl(220, 10%, 60%)";
  const clamped = Math.min(100, Math.max(0, pct));
  const hue = (clamped / 100) * (HUE_GREEN - HUE_RED) + HUE_RED;
  return `hsl(${hue.toFixed(0)}, ${SAT}%, ${LIGHT}%)`;
}

/**
 * Muted variant — same hue, lower lightness. Use for backgrounds + borders
 * adjacent to scoreColor() text (avoids over-saturation).
 */
export function scoreColorMuted(pct: number): string {
  if (!Number.isFinite(pct)) return "hsl(220, 10%, 30%)";
  const clamped = Math.min(100, Math.max(0, pct));
  const hue = (clamped / 100) * (HUE_GREEN - HUE_RED) + HUE_RED;
  return `hsl(${hue.toFixed(0)}, ${SAT}%, ${LIGHT_MUTED}%)`;
}
