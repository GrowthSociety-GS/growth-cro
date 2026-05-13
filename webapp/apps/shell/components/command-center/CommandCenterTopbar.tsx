// Command Center topbar — title + subtitle + 2 actions (V26 parity).
// Server Component, mono-concern: render header only.
// SP-2 webapp-command-center-view (V26 parity).

export function CommandCenterTopbar() {
  return (
    <div className="gc-topbar">
      <div className="gc-title">
        <h1>Command Center</h1>
        <p>
          Fleet, priorités et client focus. Audit, recos et GSG sur le même rail produit. Reality
          reste dormant tant qu&apos;il n&apos;y a pas de données réelles.
        </p>
      </div>
      <div className="gc-toolbar">
        <a
          href="/deliverables/GrowthCRO-V26-WebApp.html"
          className="gc-btn gc-btn--ghost"
          target="_blank"
          rel="noopener noreferrer"
        >
          Open V26 archive
        </a>
        <a href="/gsg" className="gc-btn gc-btn--primary">
          Copy GSG brief
        </a>
      </div>
    </div>
  );
}
