// Design tokens — mirror the V27 CSS custom properties so the V28 UI feels
// continuous with the legacy HTML during the transition.

export const tokens = {
  colors: {
    bg: "#0c1018",
    panel: "#121823",
    panel2: "#171f2d",
    line: "#273246",
    lineSoft: "#1e2839",
    text: "#f4f1e8",
    muted: "#98a2b3",
    soft: "#c8cfda",
    gold: "#d7b46a",
    cyan: "#65d6cf",
    green: "#80d48b",
    red: "#f07178",
    amber: "#f3c76b",
    blue: "#7ba7ff",
    ink: "#080b10",
  },
  radius: "8px",
  shadow: "0 18px 54px rgba(0,0,0,.28)",
  font: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
} as const;

export type Tokens = typeof tokens;
