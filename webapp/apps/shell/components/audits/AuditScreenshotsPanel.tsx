// AuditScreenshotsPanel — render desktop + mobile fold thumbnails for the
// audited page, sourced from `data/captures/<client>/<page>/screenshots/`.
//
// FR-2b (pivot 2026-05-13). Server-rendered: the file inventory is fetched
// at render time via `listScreenshotsForPage()` (which is server-only). The
// `<img>` tags point at `/api/screenshots/<client>/<page>/<filename>` which
// streams the PNG with a 1h cache header.
//
// Mono-concern : only renders. No state, no client interaction beyond a
// native `target="_blank"` link to open the full PNG.

import { Card } from "@growthcro/ui";
import {
  getScreenshotsForPageOrCanonical,
  pickFoldScreenshots,
} from "@/lib/captures-fs";

type Props = {
  clientSlug: string;
  pageSlug: string;
};

function screenshotUrl(
  clientSlug: string,
  pageSlug: string,
  filename: string
): string {
  // Relative URL — same origin. `encodeURIComponent` defends against unusual
  // slug shapes even though the API route re-validates server-side.
  return `/api/screenshots/${encodeURIComponent(clientSlug)}/${encodeURIComponent(
    pageSlug
  )}/${encodeURIComponent(filename)}`;
}

function Thumbnail({
  src,
  alt,
  caption,
}: {
  src: string;
  alt: string;
  caption: string;
}) {
  return (
    <a
      className="gc-audit-screens__thumb"
      href={src}
      target="_blank"
      rel="noopener noreferrer"
    >
      {/* eslint-disable-next-line @next/next/no-img-element -- raw PNG served via /api/screenshots, no next/image optimisation needed */}
      <img loading="lazy" src={src} alt={alt} />
      <span className="gc-audit-screens__caption">{caption}</span>
    </a>
  );
}

export function AuditScreenshotsPanel({ clientSlug, pageSlug }: Props) {
  // FS list when available (dev local), canonical 8 filenames as prod fallback
  // (Supabase Storage backend). The /api/screenshots route 302-redirects to
  // Supabase Storage URLs when configured; missing objects 404 gracefully.
  const filenames = getScreenshotsForPageOrCanonical(clientSlug, pageSlug);
  const picks = pickFoldScreenshots(filenames);

  // Reorder so fold variants appear first, then the rest (deduped).
  const seen = new Set<string>();
  const ordered: string[] = [];
  for (const f of [
    picks.desktopFold,
    picks.mobileFold,
    picks.desktopFull,
    picks.mobileFull,
  ]) {
    if (f && !seen.has(f)) {
      seen.add(f);
      ordered.push(f);
    }
  }
  for (const f of filenames) {
    if (!seen.has(f)) {
      seen.add(f);
      ordered.push(f);
    }
  }

  if (ordered.length === 0) {
    return (
      <Card title="Captures">
        <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
          Pas de captures disponibles pour cette page.
        </p>
        <p style={{ color: "var(--gc-muted)", fontSize: 11, marginTop: 6 }}>
          Attendu : <code>data/captures/{clientSlug}/{pageSlug}/screenshots/*.png</code>
        </p>
      </Card>
    );
  }

  return (
    <Card
      title="Captures"
      actions={
        <span className="gc-pill gc-pill--soft">
          {ordered.length} fichier{ordered.length > 1 ? "s" : ""}
        </span>
      }
    >
      <div className="gc-audit-screens__grid">
        {picks.desktopFold ? (
          <Thumbnail
            src={screenshotUrl(clientSlug, pageSlug, picks.desktopFold)}
            alt={`Desktop fold — ${pageSlug}`}
            caption="Desktop · fold"
          />
        ) : null}
        {picks.mobileFold ? (
          <Thumbnail
            src={screenshotUrl(clientSlug, pageSlug, picks.mobileFold)}
            alt={`Mobile fold — ${pageSlug}`}
            caption="Mobile · fold"
          />
        ) : null}
      </div>
      {ordered.length > 2 ? (
        <details className="gc-audit-screens__more">
          <summary>
            Autres captures ({ordered.length - 2})
          </summary>
          <ul className="gc-audit-screens__list">
            {ordered.slice(2).map((f) => (
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
    </Card>
  );
}
