#!/usr/bin/env python3
"""
deploy_spaces.py — CD (deploy on merge) + EXPORT (seed/refresh blueprints).

TWO MODES (opposite directions):
  --export  WORKSPACE -> REPO : pull live definitions, normalize, write files.
  --deploy  REPO -> WORKSPACE : idempotent upsert from committed blueprints.

Never run --deploy against prod from a laptop. It runs in CD, authenticated as
the service principal, AFTER a human-approved merge.

SAFE UPDATE: --deploy reads the live etag first, then updates with it. If the
live space changed since (a UI edit slipped in), the etagged update FAILS rather
than silently clobbering the out-of-band change — you get told to investigate.
Pass --force to update without an etag (overwrite unconditionally).

Exit codes: 0 ok | 2 setup/config | 4 one or more export/deploy calls failed.
"""

from __future__ import annotations

import argparse
import json
import sys

import databricks_helpers as h
from _core import (ConfigError, PermanentError, TransientError, get_logger)

log = get_logger("drift.deploy")


def export_all(cfg, env, only, adapter) -> int:
    h.GENIE_SPACES_DIR.mkdir(parents=True, exist_ok=True)
    failures = 0
    for name, spec in (cfg.get("genie_spaces") or {}).items():
        if only and name != only:
            continue
        try:
            space_id = h.get_space_id(cfg, name, env)
            live, _etag = adapter.export_space(space_id)
            blueprint = h.normalize_space(live, cfg)
            out = h.GENIE_SPACES_DIR / f"{name}{h.SPACE_SUFFIX}"
            out.write_text(h.canonical_json(blueprint) + "\n")
            log.info("exported space '%s' -> %s", name, out.relative_to(h.REPO_ROOT))
        except (ConfigError, PermanentError, TransientError) as e:
            log.error("export failed for '%s': %s", name, e)
            failures += 1
    log.info("Next: commit exported file(s) on a branch and open a PR "
             "(the L1 gate runs on it).")
    return 4 if failures else 0


def deploy_all(cfg, env, only, adapter, force) -> int:
    ws = cfg["workspace"]
    failures = 0
    for name, spec in (cfg.get("genie_spaces") or {}).items():
        if only and name != only:
            continue
        bp = h.GENIE_SPACES_DIR / f"{name}{h.SPACE_SUFFIX}"
        if not bp.exists():
            log.warning("skip '%s': no blueprint at %s", name, bp)
            continue
        serialized = bp.read_text()  # already a JSON string blueprint
        # Validate it parses before sending.
        try:
            json.loads(serialized)
        except json.JSONDecodeError as e:
            log.error("blueprint for '%s' is not valid JSON: %s", name, e)
            failures += 1
            continue

        spec = spec or {}
        space_id = (spec.get("space_id_by_env") or {}).get(env)
        try:
            if space_id:
                # Read current etag for a safe, concurrency-checked update.
                etag = None
                if not force:
                    try:
                        _live, etag = adapter.export_space(space_id)
                    except PermanentError as e:
                        log.error("could not read '%s' for safe update (%s); "
                                  "use --force to overwrite unconditionally.", name, e)
                        failures += 1
                        continue
                adapter.update_space(space_id, serialized_space=serialized,
                                     warehouse_id=ws["warehouse_id"], etag=etag)
                log.info("updated space '%s' (id=%s, etag=%s)",
                         name, space_id, "yes" if etag else "force")
            else:
                created = adapter.create_space(
                    warehouse_id=ws["warehouse_id"], serialized_space=serialized,
                    title=name)
                new_id = created.get("space_id") or created.get("id")
                log.info("created space '%s' -> id=%s", name, new_id)
                log.warning("RECORD this id under genie_spaces.%s.space_id_by_env.%s "
                            "in config.yaml and commit it.", name, env)
        except (PermanentError, TransientError) as e:
            # An etag conflict surfaces here as PermanentError — that's a
            # GOOD failure: it means the live space changed out-of-band.
            log.error("deploy failed for '%s': %s", name, e)
            log.error("  if this is an etag/conflict error, the live space was "
                      "edited outside the pipeline. Run audit_drift.py, reconcile, "
                      "then redeploy.")
            failures += 1
    return 4 if failures else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="export/deploy Genie space blueprints")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--export", action="store_true", help="workspace -> repo")
    mode.add_argument("--deploy", action="store_true", help="repo -> workspace")
    ap.add_argument("--env", default="dev")
    ap.add_argument("--only", default=None)
    ap.add_argument("--force", action="store_true",
                    help="deploy: skip etag concurrency check (overwrite)")
    args = ap.parse_args(argv)

    cfg = h.load_config()
    adapter = h.DatabricksAdapter(cfg["workspace"]["host"])
    if args.export:
        log.info("EXPORT — pulling spaces from env '%s' into the repo", args.env)
        return export_all(cfg, args.env, args.only, adapter)
    log.info("DEPLOY — pushing repo blueprints into env '%s'%s",
             args.env, " (FORCE)" if args.force else "")
    return deploy_all(cfg, args.env, args.only, adapter, args.force)


def _entry() -> int:
    try:
        return main()
    except ConfigError as e:
        log.error("setup/config error: %s", e)
        return 2
    except Exception as e:
        log.error("unexpected error: %s", e)
        return 2


if __name__ == "__main__":
    sys.exit(_entry())
