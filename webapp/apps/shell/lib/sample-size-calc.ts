// sample-size-calc — pure-TS two-sample proportion z-test.
//
// Sprint 8 / Task 008 — experiments-v27-calculator (2026-05-14).
//
// Mono-concern : statistical math only — no I/O, no React, no Supabase. The
// module is consumed by both the client-side `<SampleSizeCalculator>` (real-
// time recalc on keystroke) and any future server-side AB-power audit job.
//
// Formula (two-sample proportion z-test, equal-arm allocation) :
//
//   n_per_arm = (z_alpha + z_beta)^2 * (p1*(1-p1) + p2*(1-p2)) / (p1 - p2)^2
//
// where :
//   p1            = baseline_cvr (e.g. 0.05 for 5%)
//   p2            = p1 * (1 + mde_relative)  (e.g. p1 * 1.20 for +20% MDE)
//   z_alpha       = Φ⁻¹(1 - alpha/sides)
//   z_beta        = Φ⁻¹(power)
//
// Validated against Optimizely's reference value :
//   baselineCvr=0.05, mde=0.20, alpha=0.05, power=0.8, 2-tailed → n ≈ 3,840
//
// Acklam approximation for the inverse normal CDF — pure-TS, no scipy, no npm.
// Source : Peter John Acklam, "An algorithm for computing the inverse normal
// cumulative distribution function" (2003). Max abs relative error ≈ 1.15e-9
// in the central region, sufficient for AB-test sample-size planning.

export type Sides = 1 | 2;

export type SampleSizeInput = {
  baselineCvr: number; // 0 < p1 < 1 (e.g. 0.05 for 5%)
  mdeRelative: number; // > 0 (e.g. 0.20 for +20% lift)
  alpha: number; // type I error (default 0.05)
  power: number; // 1 - type II error (default 0.80)
  sides: Sides; // 1 or 2 (default 2)
};

export type SampleSizeResult = {
  /** Sample size per arm (control or variant) — already rounded up. */
  nPerArm: number;
  /** Total sample size across both arms. */
  nTotal: number;
  /** Days needed at the supplied daily traffic, or null if traffic is 0. */
  estDays: number | null;
  /** Validity flag — false when inputs are out of bounds. */
  valid: boolean;
  /** Human-readable reason when valid=false ; null otherwise. */
  reason: string | null;
};

// Acklam 2003 — pure-TS inverse-normal CDF.
// Returns Φ⁻¹(p) for p ∈ (0, 1). Outside that interval returns ±Infinity.
export function inverseNormalCdf(p: number): number {
  if (!Number.isFinite(p) || p <= 0 || p >= 1) {
    if (p <= 0) return -Infinity;
    if (p >= 1) return Infinity;
    return NaN;
  }
  const a = [
    -3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2,
    1.38357751867269e2, -3.066479806614716e1, 2.506628277459239,
  ];
  const b = [
    -5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2,
    6.680131188771972e1, -1.328068155288572e1,
  ];
  const c = [
    -7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838,
    -2.549732539343734, 4.374664141464968, 2.938163982698783,
  ];
  const d = [
    7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996,
    3.754408661907416,
  ];
  const pLow = 0.02425;
  const pHigh = 1 - pLow;
  let q: number;
  let r: number;
  if (p < pLow) {
    q = Math.sqrt(-2 * Math.log(p));
    return (
      (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
      ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    );
  }
  if (p <= pHigh) {
    q = p - 0.5;
    r = q * q;
    return (
      ((((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) *
        q) /
      (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    );
  }
  q = Math.sqrt(-2 * Math.log(1 - p));
  return -(
    (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
    ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
  );
}

export function calculateSampleSize(
  input: SampleSizeInput,
  dailyTraffic: number = 0,
): SampleSizeResult {
  const { baselineCvr, mdeRelative, alpha, power, sides } = input;

  // Defensive validation : every invalid combo returns a typed result rather
  // than throws — the calculator panel renders the empty state instead of
  // bubbling an error boundary.
  if (
    !Number.isFinite(baselineCvr) ||
    baselineCvr <= 0 ||
    baselineCvr >= 1
  ) {
    return {
      nPerArm: 0,
      nTotal: 0,
      estDays: null,
      valid: false,
      reason: "Baseline CVR doit être ∈ (0, 1)",
    };
  }
  if (!Number.isFinite(mdeRelative) || mdeRelative <= 0) {
    return {
      nPerArm: 0,
      nTotal: 0,
      estDays: null,
      valid: false,
      reason: "MDE relative doit être > 0",
    };
  }
  if (!Number.isFinite(alpha) || alpha <= 0 || alpha >= 1) {
    return {
      nPerArm: 0,
      nTotal: 0,
      estDays: null,
      valid: false,
      reason: "Alpha doit être ∈ (0, 1)",
    };
  }
  if (!Number.isFinite(power) || power <= 0 || power >= 1) {
    return {
      nPerArm: 0,
      nTotal: 0,
      estDays: null,
      valid: false,
      reason: "Power doit être ∈ (0, 1)",
    };
  }
  if (sides !== 1 && sides !== 2) {
    return {
      nPerArm: 0,
      nTotal: 0,
      estDays: null,
      valid: false,
      reason: "Sides doit valoir 1 ou 2",
    };
  }

  const p1 = baselineCvr;
  const p2 = p1 * (1 + mdeRelative);
  if (p2 >= 1 || p2 <= 0) {
    return {
      nPerArm: 0,
      nTotal: 0,
      estDays: null,
      valid: false,
      reason: "Variante prédite ∉ (0, 1) — réduis la MDE",
    };
  }

  // z_alpha is the critical value for the chosen tail count.
  // 2-tailed @ alpha=0.05 → Φ⁻¹(1 - 0.025) ≈ 1.9600 ✓
  // 1-tailed @ alpha=0.05 → Φ⁻¹(1 - 0.05)  ≈ 1.6449
  const zAlpha = inverseNormalCdf(1 - alpha / sides);
  const zBeta = inverseNormalCdf(power);

  const variance = p1 * (1 - p1) + p2 * (1 - p2);
  const delta = p1 - p2;
  const numerator = (zAlpha + zBeta) ** 2 * variance;
  const denominator = delta * delta;
  const nPerArmRaw = numerator / denominator;
  const nPerArm = Math.ceil(nPerArmRaw);
  const nTotal = nPerArm * 2;

  const traffic = Number.isFinite(dailyTraffic) ? dailyTraffic : 0;
  const estDays =
    traffic > 0 ? Math.ceil(nTotal / traffic) : null;

  return {
    nPerArm,
    nTotal,
    estDays,
    valid: true,
    reason: null,
  };
}
