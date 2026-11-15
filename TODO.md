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

## Optional follow-ups

- Add an opt-in live bulk-download integration test.
- Measure `all_cards` memory usage; consider `orjson` or `ijson`.
- Add fuzzy ranking for non-exact bulk search if substring ranking is not enough.
- Add a `--no-bulk` pytest option (tests currently use mocked Scryfall fixtures).
