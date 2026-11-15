# Remaining work

## Done

- Scryfall rate limiting: direct HTTP requests now share scrython's per-endpoint
  global limiters (2 req/s for search/named/random/collection, 10 req/s for other
  endpoints). Non-200 responses are logged instead of surfacing as `KeyError`.
- Import tests no longer hit Scryfall or the real `~/.mtgo` cache. Deterministic
  fixtures live in `tests/fake_scryfall.py`; set `MTGORG_TEST_ONLINE=1` to run
  against the live API.
- `test_EDHREC_import` uses a local HTML fixture because live EDHRec deck URLs
  expire/404.
- `test_MTGA_import` and `test_CSV_import_MTGManager` pass reliably.
- `pytest`: 12/12 pass; flake8 clean.

## Next: offline bulk data

See `BULK_PLAN.md`. The highest-value next step is phases 1-2:

1. `BulkDataManager` with metadata, atomic download, update check, cleanup.
2. In-memory indexes for bulk data and refactored local lookups.

After that, integrate the setting into the GUI and add bulk-mode tests.
