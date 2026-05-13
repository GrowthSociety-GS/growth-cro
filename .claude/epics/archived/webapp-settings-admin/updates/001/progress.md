# T001 — Page + tabs layout + Sidebar link

**Status** : done

## Files
- NEW `webapp/apps/shell/app/settings/page.tsx` — Server Component, loads user + members + counts in parallel.
- NEW `webapp/apps/shell/components/settings/SettingsTabs.tsx` — client component, URL hash router (`#account|#team|#usage|#api`).
- NEW `webapp/apps/shell/components/settings/AccountTab.tsx` — created (filled by T002).
- NEW `webapp/apps/shell/components/settings/TeamTab.tsx` — created (filled by T002).
- NEW `webapp/apps/shell/components/settings/UsageTab.tsx` — created (filled by T003).
- NEW `webapp/apps/shell/components/settings/ApiTab.tsx` — created (filled by T003).
- EDIT `webapp/apps/shell/components/Sidebar.tsx` — add `{ label: "Settings", href: "/settings", hint: "Admin" }`.
- EDIT `webapp/apps/shell/app/globals.css` — `.gc-settings*` styles (vertical nav + responsive collapse).

## Notes
- Default tab `account` when hash absent or unknown.
- `useEffect` on `hashchange` keeps tab state in sync if user copies/pastes a `#team` URL.
- Tab content components are passed as `ReactNode` props so the server page can decide what to pre-compute.
