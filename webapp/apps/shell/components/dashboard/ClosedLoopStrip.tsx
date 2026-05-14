// ClosedLoopStrip — V26 dashboard signature surface (Sprint 4 / Task 004).
//
// 8-module coverage strip rendered horizontally under the KPI grid : Evidence
// · Lifecycle · BrandDNA · Design Grammar · Funnel · Reality · GEO · Learning.
// Each card shows the module icon + label + count/total + status badge
// (active=green / partial=amber / pending=soft).
//
// Source pattern : V26 HTML L909-919 + L1626-1640. Tone aware of the
// stratospheric DNA — gold left-border accent + glass card surface.

import { Card, Pill } from "@growthcro/ui";
import type {
  ClosedLoopCoverage,
  ClosedLoopModule,
  ClosedLoopModuleStatus,
} from "./queries";

const TONE_BY_STATUS: Record<ClosedLoopModuleStatus, "green" | "amber" | "soft"> = {
  active: "green",
  partial: "amber",
  pending: "soft",
};

const LABEL_BY_STATUS: Record<ClosedLoopModuleStatus, string> = {
  active: "actif",
  partial: "partiel",
  pending: "pending",
};

function ModuleCard({ mod }: { mod: ClosedLoopModule }) {
  const pct =
    mod.total > 0 ? Math.round((mod.count / mod.total) * 100) : 0;
  return (
    <div
      className="gc-glass-card"
      style={{
        padding: "12px 14px",
        borderRadius: 12,
        minHeight: 84,
        display: "flex",
        flexDirection: "column",
        gap: 6,
        position: "relative",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div
          style={{
            fontSize: 12,
            color: "var(--gc-muted)",
            textTransform: "uppercase",
            letterSpacing: "0.04em",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span aria-hidden style={{ fontSize: 14 }}>
            {mod.icon}
          </span>
          {mod.label}
        </div>
        <Pill tone={TONE_BY_STATUS[mod.status]}>{LABEL_BY_STATUS[mod.status]}</Pill>
      </div>
      <div
        style={{
          fontSize: 22,
          fontFamily: "var(--ff-display, var(--gc-font-display))",
          fontStyle: "italic",
          fontWeight: 500,
          background:
            mod.status === "active"
              ? "linear-gradient(135deg, var(--gold-sunset), var(--gold))"
              : "linear-gradient(135deg, var(--gc-text-soft, #e8eef8), var(--gc-muted))",
          WebkitBackgroundClip: "text",
          backgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}
      >
        {mod.count}
        <span
          style={{
            fontSize: 12,
            opacity: 0.6,
            marginLeft: 4,
            fontStyle: "normal",
            fontFamily: "var(--ff-body, var(--gc-font-sans))",
            WebkitTextFillColor: "var(--gc-muted)",
            color: "var(--gc-muted)",
          }}
        >
          / {mod.total} ({pct}%)
        </span>
      </div>
      <div
        style={{
          fontSize: 11,
          color: "var(--gc-muted)",
          lineHeight: 1.3,
        }}
      >
        {mod.hint}
      </div>
    </div>
  );
}

type Props = {
  coverage: ClosedLoopCoverage;
};

export function ClosedLoopStrip({ coverage }: Props) {
  return (
    <Card
      title="🔄 V26 Closed-Loop coverage"
      actions={
        <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>
          État réel des 7 piliers V26 + V29/V30 sur la fleet
        </span>
      }
    >
      <div
        data-testid="closed-loop-strip"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 12,
        }}
      >
        {coverage.modules.map((m) => (
          <ModuleCard key={m.key} mod={m} />
        ))}
      </div>
    </Card>
  );
}
