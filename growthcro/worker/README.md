# growthcro.worker — Pipeline-trigger worker daemon

> **Phase A** local Python worker. Polls Supabase `runs` queue and dispatches
> the matching CLI pipeline locally on the dev machine. Cf
> [`DECISIONS_2026-05-14.md`](../../.claude/docs/architecture/DECISIONS_2026-05-14.md)
> §D2 (D2.C-Phase-A).

## Quick start (Mathis-facing)

```bash
# 1. Source Supabase creds + SSL cert fix (Python 3.13 macOS)
set -a; source .env.local; set +a
export SUPABASE_URL="https://${SUPABASE_PROJECT_REF}.supabase.co"
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")

# 2. Run worker
python3 -m growthcro.worker --once     # single iteration (smoke)
python3 -m growthcro.worker            # loop forever, poll 30s
```

When the webapp triggers a run (via `POST /api/runs/capture` etc.), it inserts
a row into Supabase `runs` table with `status='pending'`. The worker picks it
up at the next poll (within 30s by default), executes the matching CLI, and
updates `status='completed'` or `'failed'` with a stdout/stderr tail in
`metadata_json`.

The webapp UI subscribes to Supabase Realtime channel `public:runs` and shows
a live status pill that updates within ~100ms of the worker writing back.

## Architecture

```
Webapp UI <TriggerRunButton>
  ↓ POST /api/runs/capture { client_slug, page_type, url }
Next.js route handler (requireAdmin)
  ↓ Supabase insert into runs (status=pending, type=capture, metadata_json=...)
  ↓ returns { run_id }
Webapp UI mounts <RunStatusPill runId={...} />
  ↓ subscribes Supabase Realtime channel public:runs filtered by run_id
  ↓ live status: pending → running → completed/failed

LOCAL WORKER (this module, growthcro/worker/daemon.py)
  ↓ poll Supabase every 30s
  ↓ pickup pending row, atomically claim (status=running, started_at)
  ↓ dispatch_run() → subprocess.run() → CLI:
  ↓   capture     : python -m growthcro.capture.cli --url X --label Y --page-type Z
  ↓   score       : python -m growthcro.scoring.cli specific X Y
  ↓   recos       : python -m growthcro.recos.cli enrich --client X --page Y
  ↓   gsg         : python -m moteur_gsg.orchestrator --mode M --client X
  ↓   multi_judge : python -m moteur_multi_judge.orchestrator --client X
  ↓   reality     : python -m growthcro.reality.poller --client X
  ↓   geo         : python -m growthcro.geo.runner --client X
  ↓ on completion: UPDATE runs status=completed, output_path, metadata_json.{stdout,stderr,duration,returncode}
  ↓ on failure  : UPDATE runs status=failed, error_message, metadata_json
Supabase Realtime emits update → Webapp UI <RunStatusPill /> updates live
```

## Supabase environment

Required env vars (read via `growthcro.config.get_config().system_env`) :

| Var | Value |
|---|---|
| `SUPABASE_URL` | `https://${SUPABASE_PROJECT_REF}.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | `sb_secret_...` (rotated 2026-05-14) |
| `SSL_CERT_FILE` | (macOS Python 3.13 fix) `$(python3 -c 'import certifi; print(certifi.where())')` |

These typically live in `.env.local` at repo root.

## CLI options

```
python3 -m growthcro.worker --help
  --poll-interval N   Seconds between queue polls (default: 30)
  --batch-limit N     Max pending runs fetched per poll (default: 5)
  --once              Single iteration then exit (debug / CI smoke)
```

## Operational notes

- **Race-safety** : `claim_run()` atomically transitions `pending → running`
  via PostgREST `?status=eq.pending` filter on the PATCH. Two workers racing
  on the same row will only succeed for one — the other gets an empty
  response and skips. Safe to run multiple workers simultaneously (e.g. one
  dedicated to slow capture runs, another to fast score/recos).
- **Graceful shutdown** : SIGINT / SIGTERM sets the running flag to false;
  the worker finishes the in-flight run then exits cleanly.
- **Subprocess timeout** : each CLI invocation is capped at 600s (10 min)
  in `dispatcher.py`. Beyond that, the run is marked failed with
  `error_message="subprocess.TimeoutExpired"`.
- **Stdout/stderr tail** : last ~2KB of each stream are persisted in
  `runs.metadata_json.stdout_tail` / `stderr_tail` for post-mortem.
- **Subprocess inherits env** : the worker's env (including Anthropic key,
  Apify token, Reality creds) propagates to the dispatched CLI.

## Adding a new run type

1. Add to `RunType` Literal in `growthcro/models/runs_models.py`
2. Add the SQL check-constraint value in
   `supabase/migrations/<next>_runs_extend.sql`
3. Add a `RUN_TYPE_TO_CLI[<type>]` entry in `growthcro/worker/dispatcher.py`
4. Extend `build_cli_command()` with the per-type arg mapping
5. Add a Playwright spec smoke test in
   `webapp/tests/e2e/runs-trigger.spec.ts`

## Phase B (deferred) — Fly.io migration

When the dev machine running this worker is no longer always-on, migrate to
a tiny Fly.io VM (eu-central) running the same daemon module under
`fly machine run`. ~$5/mo. Tracked as a separate sub-PRD V2.

## Troubleshooting

- `SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set` → source `.env.local`
- `SSL: CERTIFICATE_VERIFY_FAILED` (macOS Python 3.13) → `export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")`
- Worker logs nothing : check `growthcro.observability.logger` level — set
  `export GROWTHCRO_LOG_LEVEL=DEBUG` for verbose output.
- Run stays in `pending` for >30s : worker not running. Start it via
  `python3 -m growthcro.worker`.
- Run marked failed with `subprocess.TimeoutExpired` : CLI took >10 min;
  either the operation is genuinely slow (Playwright capture of heavy SPA)
  or it's stuck. Increase `SUBPROCESS_TIMEOUT_SEC` in `dispatcher.py` if
  legitimate, or investigate the CLI itself.
