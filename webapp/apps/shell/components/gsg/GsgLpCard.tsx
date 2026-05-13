// GsgLpCard — single LP preview card for the GSG Studio index.
//
// FR-3 of `webapp-full-buildout`. Renders metadata pills + an iframe pointed
// at `/api/gsg/[slug]/html` (which sets `X-Frame-Options: SAMEORIGIN` so the
// frame only renders on the shell origin). Pure server-renderable — no
// client hooks, no `"use client"`.

import { Card, Pill } from "@growthcro/ui";
import type { GsgDemo } from "@/lib/gsg-fs";

type Props = {
  demo: GsgDemo;
};

function scoreTone(score: number | null): "green" | "amber" | "red" | "soft" {
  if (score === null) return "soft";
  if (score >= 70) return "green";
  if (score >= 50) return "amber";
  return "red";
}

function fmtSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${bytes} B`;
}

function fmtDate(iso: string): string {
  // YYYY-MM-DD only (avoid TZ-sensitive rendering between SSR & hydrate).
  return iso.slice(0, 10);
}

export function GsgLpCard({ demo }: Props) {
  const iframeSrc = `/api/gsg/${encodeURIComponent(demo.slug)}/html`;
  const score = demo.multi_judge?.final_score_pct ?? null;
  const tier = demo.multi_judge?.tier ?? null;
  const scoreLabel =
    score !== null
      ? `${score.toFixed(1)}%${tier ? ` ${tier}` : ""}`
      : tier ?? null;

  return (
    <Card
      title={demo.slug}
      actions={
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {demo.page_type ? <Pill tone="cyan">{demo.page_type}</Pill> : null}
          {demo.doctrine_version ? (
            <Pill tone="gold">{demo.doctrine_version}</Pill>
          ) : null}
          {scoreLabel ? <Pill tone={scoreTone(score)}>{scoreLabel}</Pill> : null}
        </div>
      }
    >
      <p style={{ color: "var(--gc-muted)", fontSize: 12, margin: "0 0 10px" }}>
        <code>{demo.filename}</code>
        {" · "}
        {fmtSize(demo.size_bytes)}
        {" · "}
        modified {fmtDate(demo.last_modified)}
        {demo.brand ? ` · brand: ${demo.brand}` : ""}
      </p>
      <div
        style={{
          width: "100%",
          height: 600,
          border: "1px solid var(--gc-line-soft)",
          borderRadius: 6,
          overflow: "hidden",
          background: "#0f1520",
        }}
      >
        <iframe
          title={`Preview: ${demo.slug}`}
          src={iframeSrc}
          loading="lazy"
          style={{ width: "100%", height: "100%", border: 0, display: "block" }}
        />
      </div>
      <div style={{ marginTop: 10, display: "flex", gap: 8 }}>
        <a
          href={iframeSrc}
          target="_blank"
          rel="noreferrer noopener"
          className="gc-pill gc-pill--soft"
          style={{ textDecoration: "none" }}
        >
          Open full ↗
        </a>
      </div>
    </Card>
  );
}
