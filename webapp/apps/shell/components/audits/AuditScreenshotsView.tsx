"use client";

// AuditScreenshotsView — Sprint 6 / Task 005 — client island for the
// dual-viewport (💻 Desktop / 📱 Mobile) toggle on the captures card.
//
// Inputs come from the server wrapper (AuditScreenshotsPanel) which owns
// the fs/Supabase inventory ; this component is pure presentation + state.
// The active viewport is read from the shared `useViewport` hook so
// RichRecoCard's bbox crop stays in sync without prop drilling.
//
// Mono-concern : renders the toggle + the current viewport's pair of
// (fold + full) thumbnails. Defensive : when a slot is null we render
// "Pas de capture" rather than throwing.

import { ViewportToggle } from "./ViewportToggle";
import { useViewport } from "@/lib/use-viewport";

type Props = {
  clientSlug: string;
  pageSlug: string;
  desktopFold: string | null;
  desktopFull: string | null;
  mobileFold: string | null;
  mobileFull: string | null;
  otherFiles: string[];
};

function screenshotUrl(clientSlug: string, pageSlug: string, filename: string): string {
  return `/api/screenshots/${encodeURIComponent(clientSlug)}/${encodeURIComponent(
    pageSlug,
  )}/${encodeURIComponent(filename)}`;
}

function Thumbnail({
  src,
  alt,
  caption,
  priority = false,
}: {
  src: string;
  alt: string;
  caption: string;
  priority?: boolean;
}) {
  return (
    <a
      className="gc-audit-screens__thumb"
      href={src}
      target="_blank"
      rel="noopener noreferrer"
    >
      {/* eslint-disable-next-line @next/next/no-img-element -- redirect-based src, see AuditScreenshotsPanel comment */}
      <img
        src={src}
        alt={alt}
        width={480}
        height={300}
        loading={priority ? "eager" : "lazy"}
        fetchPriority={priority ? "high" : "auto"}
        decoding="async"
        style={{ width: "100%", height: "auto", display: "block" }}
      />
      <span className="gc-audit-screens__caption">{caption}</span>
    </a>
  );
}

function EmptySlot({ label }: { label: string }) {
  return (
    <div
      className="gc-audit-screens__thumb"
      style={{
        padding: 16,
        textAlign: "center",
        color: "var(--gc-muted)",
        fontSize: 12,
        border: "1px dashed var(--gc-line)",
        borderRadius: 8,
      }}
    >
      Pas de capture {label}
    </div>
  );
}

export function AuditScreenshotsView({
  clientSlug,
  pageSlug,
  desktopFold,
  desktopFull,
  mobileFold,
  mobileFull,
  otherFiles,
}: Props) {
  const { viewport } = useViewport();
  const fold = viewport === "desktop" ? desktopFold : mobileFold;
  const full = viewport === "desktop" ? desktopFull : mobileFull;
  const label = viewport === "desktop" ? "Desktop" : "Mobile";

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-end",
          marginBottom: 10,
        }}
      >
        <ViewportToggle />
      </div>

      <div className="gc-audit-screens__grid">
        {fold ? (
          <Thumbnail
            src={screenshotUrl(clientSlug, pageSlug, fold)}
            alt={`${label} fold — ${pageSlug}`}
            caption={`${label} · fold`}
            priority
          />
        ) : (
          <EmptySlot label={`${label} fold`} />
        )}
        {full ? (
          <Thumbnail
            src={screenshotUrl(clientSlug, pageSlug, full)}
            alt={`${label} full — ${pageSlug}`}
            caption={`${label} · full`}
          />
        ) : (
          <EmptySlot label={`${label} full`} />
        )}
      </div>

      {otherFiles.length > 0 ? (
        <details className="gc-audit-screens__more">
          <summary>Autres captures ({otherFiles.length})</summary>
          <ul className="gc-audit-screens__list">
            {otherFiles.map((f) => (
              <li key={f}>
                <a
                  href={screenshotUrl(clientSlug, pageSlug, f)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {f}
                </a>
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </div>
  );
}
