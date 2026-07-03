# Napkin Runbook

## Curation Rules
- Re-prioritize on every read.
- Keep recurring, high-value notes only.
- Max 10 items per category.
- Each item includes date + "Do instead".

## Execution & Validation (Highest Priority)
1. **[2026-07-03] `regions/` is 8.3 GB locally (EBD files, gitignored) — never glob/grep it blindly**
   Do instead: target specific subpaths like `regions/<county>/config.json`; never `grep -r regions/`.
2. **[2026-07-03] Pipeline outputs are local-only until pushed**
   Do instead: after any pipeline run, commit `regions/<county>/` outputs and `<county>/data/` and push to main to trigger deploy.
3. **[2026-07-03] `scripts/test_species_code_generation.py` fails on main (pre-existing)**
   Do instead: don't treat that one failing suite as caused by your change; the other 6 suites should pass. Spawn-task filed 2026-07-03.
4. **[2026-07-03] Preview via `.claude/launch.json` server "flightcall-static" (python http.server :8642)**
   Do instead: use preview_start with that config to verify landing page and county apps; pages need a server (fetch of counties.json/data fails on file://).

## Domain Behavior Guardrails
1. **[2026-07-03] `counties.json` is the single source of truth (cards, map, deploy)**
   Do instead: to launch/scaffold counties edit the manifest (or run `scripts/new_county.py`); never hand-edit index.html cards, SVG statuses, or the deploy workflow county list.
2. **[2026-07-03] County app dirs must stay byte-identical to canonical `washtenaw/`**
   Do instead: edit the app only in `washtenaw/`, then run `python3 scripts/sync_counties.py`; verify with `--check`.
3. **[2026-07-03] County pages get their name from `js/county.js` hooks**
   Do instead: use `[data-county-line]`, `[data-county-name]`, `title[data-county-title]` markup hooks — never hardcode a county name in county app HTML.
4. **[2026-07-03] ONE valley-season definition: `VALLEY_WINTER_WEEKS`/`VALLEY_SUMMER_WEEKS` in constants.py**
   Do instead: label a valley's season only via `classify_valley_season`/`valley_is_winter` in valley_detection.py; never re-hardcode winter/summer week ranges (that mismatch swapped spring/fall labels). Classify persists valleys to the CSV; timing reuses them — don't re-`detect_valleys` in the timing stage.
5. **[2026-07-03] Regenerate all live counties from committed intermediates (no EBD needed)**
   Do instead: after pipeline logic changes, loop live counties running classify→timing→merge then `cp regions/<c>/<c>_species_data.json <c>/data/`; verify via git diff that only intended species changed and category totals hold.

## User Directives
1. **[2026-07-03] Always commit and push after completing tasks; check README.md for needed updates**
   Do instead: end every task with README check + commit + push.
