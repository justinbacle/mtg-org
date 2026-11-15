# Remaining work

## Done

- Scryfall rate limiting: direct HTTP requests share scrython's per-endpoint
  global limiters, and non-200 responses are logged instead of raising `KeyError`.
- Import tests no longer hit Scryfall or the real `~/.mtgo` cache. Deterministic
  fixtures live in `tests/fake_scryfall.py`; set `MTGORG_TEST_ONLINE=1` for live runs.
- EDHREC parsing test uses a local HTML fixture.
- Offline bulk-data support (see `BULK_PLAN.md`): manager, indexes, offline
  search/lookups, config keys, Settings > Scryfall dialog, startup prompt/fallback.
- Bulk download, index, lookup, filter, and config tests added.
- Bulk data now uses a SQLite disk-backed cache (`default-cards-cache.sqlite3`)
  instead of holding every card in memory. Current `default_cards` stays around
  60-80 MB RSS after the one-time build.
- Opt-in live bulk test added (`MTGORG_TEST_LIVE_BULK=1`).
- Printing/variant selector added, with regular nonfoil printings preferred by
  default and explicit showcase/promo/foil-only selection available.
- Keyrune auto-refresh when set icons are missing, with set-code fallback.
- Settings dialog shows cache/database sizes and can clear caches/bulk index.
- Bulk-mode card images now load/download correctly.
- Packaging metadata fixed and runtime/dev requirements split.

## Optional follow-ups

- Add fuzzy ranking for non-exact bulk search if substring ranking is not enough.
- Add a `--no-bulk` pytest option (tests currently use mocked Scryfall fixtures).
- Show progress while the first SQLite bulk index is built (~10 s).
- Run Pyright in CI (config exists, but it is not wired into workflows).
- Decide on and add a project licence.
- Optionally test/measure the `all_cards` mode end-to-end.
