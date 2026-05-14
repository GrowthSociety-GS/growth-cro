// AuditScreenshotsPanel — render desktop + mobile fold thumbnails for the
// audited page, sourced from `data/captures/<client>/<page>/screenshots/`.
//
// FR-2b (pivot 2026-05-13) → Sprint 6 / Task 005 (2026-05-14) : added
// dual-viewport toggle (💻 Desktop / 📱 Mobile) via the shared `useViewport`
// hook. The server component still owns the file inventory (no client-side
// fs/Supabase calls) ; we hand the picks down to a small client island
// (`AuditScreenshotsView`) that switches the highlighted thumbnail.
//
// Mono-concern : the server wrapper does I/O ; the inner client component
// does rendering + viewport state. Native `target="_blank"` link still
// opens the full PNG.

import { Card } from "@growthcro/ui";
import {
  getScreenshotsForPageOrCanonical,
  pickFoldScreenshots,
} from "@/lib/captures-fs";
import { AuditScreenshotsView } from "./AuditScreenshotsView";

type Props = {
  clientSlug: string;
  pageSlug: string;
};

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
      <AuditScreenshotsView
        clientSlug={clientSlug}
        pageSlug={pageSlug}
        desktopFold={picks.desktopFold}
        desktopFull={picks.desktopFull}
        mobileFold={picks.mobileFold}
        mobileFull={picks.mobileFull}
        otherFiles={ordered.slice(2)}
      />
    </Card>
  );
}
