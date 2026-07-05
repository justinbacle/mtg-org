# Remaining work

## 1. Fix Scryfall rate-limit failures

Live tests are hitting the Scryfall 10 req/s limit after the User-Agent registration and 100 ms delay. This makes several tests fail or become flaky.

Options:
- Use scrython's `SlowRateLimiter` for Scryfall API paths that need slower pacing (search/named are 2 req/s, other endpoints are 10 req/s).
- Add a longer/more robust delay between live Scryfall calls, or cache results between calls.
- Mock Scryfall in tests that are about parsing, not about Scryfall resolution.

## 2. Fix `test_CSV_import_MTGManager`

Failure: `IndexError: list index out of range` in `importexport.py:418` when `scryfall.searchCards` returns an empty list (likely rate-limited) for `Arcane Lighthouse` from C14.

- Need to handle empty search results gracefully (error message + skip card) or prevent the rate limit.
- Verify expected `MTG_MANAGER_DECKLIST` IDs once the Scryfall lookup succeeds.

## 3. Fix `test_MTGA_import`

Failure: returns an empty `deckList`. Likely all Scryfall lookups failed due to rate limits.

- Confirm expected `MTGA_DECKLIST` IDs after a successful run.
- Consider mocking `scryfall.searchCards` so the test verifies parser logic independently.

## 4. Fix `test_EDHREC_import`

Changed to test `parseInput(url)` only.
Failure: old URL `0qIYCFl_tMPMnmGV0swWeg` returns 404/no Card Kingdom export link.

- Update `EDHREC_URL` to the new URL: `https://edhrec.com/deckpreview/TV66-4LUHUNBJIO80_f4Rw`.
- Verify `EDHREC_PARSED_NAMES` matches actual parsed output (currently based on the new deck).
- Consider mocking HTTP response for the test so it does not depend on EDHRec being live.

## 5. Improve rate limiting across the codebase

- Apply scrython's rate limiters where appropriate.
- Consider a single shared rate-limited request wrapper in `utils.py` with correct per-endpoint delays.

## 6. Re-run full test suite

After the above, run:

```bash
python -m pytest tests/test_imports.py -v
```

and confirm 12/12 pass.
