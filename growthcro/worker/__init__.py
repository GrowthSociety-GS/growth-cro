"""growthcro.worker — Phase A pipeline-trigger worker daemon (Sprint 2, task 002).

Poll-based bridge between the Next.js webapp and the Python CLI pipelines.
Reads pending rows from the Supabase `runs` queue, dispatches to the matching
CLI invocation, updates status + logs back to Supabase, leverages Realtime
to notify the webapp UI.

See `growthcro/worker/README.md` for operational instructions.
"""

from growthcro.worker.dispatcher import RUN_TYPE_TO_CLI, build_cli_command, dispatch_run

__all__ = ["RUN_TYPE_TO_CLI", "build_cli_command", "dispatch_run"]
