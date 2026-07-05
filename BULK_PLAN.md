# Plan: Proper Scryfall Bulk Data Support

## Context

The MTG Organizer app already has a partial bulk-data implementation:

- `mtgorg/constants.py` defines `USE_BULK_FILES = False` and `DEFAULT_BULK_FOLDER_LOCATION = ~/.mtgo/scryfall_bulk`.
- `mtgorg/lib/scryfall.py` has `getBulkData()`, `downloadBulkData()`, and `searchCardsLocal()`.
- `mtgorg/mtgorg_app.py` creates the bulk folder on startup.
- `readme.md` mentions "WIP, added basic support for bulk files".

However, the current implementation has important gaps that make it unreliable and slow. The goal is to finish the support so the app can work with Scryfall's card data (records, search, IDs, reprints, set printings) offline from one bulk file, without hitting API rate limits. Only card images are fetched from Scryfall on demand and cached locally. The online-only mode must remain available for users who cannot or do not want to download bulk files. In every case, the app must enforce Scryfall's rate limits (2 req/s for search/named, 10 req/s for other endpoints).

---

## 1. Bulk Data Selection

Scryfall offers several bulk files:

| Type | Contents | Use case |
|------|----------|----------|
| `default_cards` | Every printed card Scryfall has ever had. | Covers all offline lookups: names, IDs, reprints, set chooser. |
| `oracle_cards` | One record per unique card (Oracle identity). | Smaller, but lacks reprint data; not used by this app. |
| `all_cards` | Same as default but includes digital-only/arena cards. | Larger than `default_cards` for no benefit here. |
| `rulings`, `unique_artwork` | Specialized. | Not needed for core features. |

### Decision

Offer the user a single bulk-file mode choice that maps directly to language coverage:

- **English** — download `default_cards`. Smaller and faster. Sufficient if the user works with English printings only. If a non-English printing is requested while this mode is active, the app falls back to Scryfall online with rate limiting.
- **All languages** — download `all_cards`. Larger, but contains every printed card in every supported language. Required for fully offline non-English printing selection.

The user must be able to switch between these two modes and re-download when switching. The online-only mode remains available for users who do not want to download a bulk file at all.

### Tasks

- [ ] Add a `BULK_DATA_TYPE` constant in `constants.py` (default `"default_cards"`).
- [ ] Add a user-facing setting `bulk_language_mode` with values `"english"` (maps to `default_cards`) and `"all"` (maps to `all_cards`).
- [ ] Update `downloadBulkData()` to respect the selected mode.
- [ ] When `bulk_language_mode = english` and a lookup requests a non-English printing, fall back to online with rate limiting.
- [ ] Validate the selected type against the available list from `https://api.scryfall.com/bulk-data` and fall back to `default_cards` if unavailable.

---

## 2. Download, Update and Storage

### Current state

`downloadBulkData()` downloads the file with `requests`, streams it to disk, and names it after the URL segment (e.g. `default-cards-20230813090443.json`). There is no automatic update, no integrity check, and no handling if the download fails mid-way.

### Proposed design

1. **Metadata file**
   - Store a small JSON (`bulk_info.json`) next to the bulk file with:
     - `type`
     - `download_uri`
     - `updated_at` (ISO timestamp from Scryfall)
     - `size` (bytes)
     - `etag` (if available)
     - `local_path`
2. **Update policy**
   - On startup, if `USE_BULK_FILES` is enabled, query the Scryfall `/bulk-data` endpoint (this is one lightweight request).
   - Compare `updated_at` from Scryfall with the local metadata.
   - If the local file is older than the remote file, download the new one.
   - Keep the previous bulk file until the new one is fully downloaded and validated.
3. **Atomic download**
   - Download to a temporary file (`default-cards-*.json.tmp`).
   - Rename to the final name only after the download completes and JSON parses.
   - Remove old bulk files once the new one is validated, keeping at most two files.
4. **Progress feedback**
   - Expose download progress so the GUI can show a progress bar.
   - Use `requests` streaming with chunked progress reporting.
5. **Rate-limit enforcement during download**
   - The `/bulk-data` endpoint is one lightweight request; apply the 10 req/s rate limiter.
   - The actual bulk download is a single large `GET`; avoid additional requests around it.

### Tasks

- [ ] Create `BulkDataManager` class in `mtgorg/lib/scryfall.py` (or new `mtgorg/lib/bulk.py`) responsible for metadata, download, update, and cleanup.
- [ ] Add `getBulkInfo()` to fetch `/bulk-data` and parse it.
- [ ] Add `needsUpdate()` using `updated_at` comparison.
- [ ] Add `downloadBulkData(type, progress_callback=None)` with atomic `.tmp` + rename.
- [ ] Add `cleanupOldBulkFiles(keep=2)`.
- [ ] Ensure the download uses the registered User-Agent and respects rate limits.

---

## 3. In-Memory Indexing and Caching

### Current state

`getBulkData()` reads the entire JSON file every time it is called. `searchCardsLocal()` does a linear scan over all cards for every lookup. That is slow and repeated across calls.

### Proposed design

1. **Lazy load once per process**
   - Keep the parsed bulk list in a module-level variable.
   - Reload only when the file on disk changes (compare mtime/size).
   - Both `default_cards` and `all_cards` are supported; the active file is determined by the user's language-mode setting.
2. **Build indexes for common lookups**
   - `name -> list of cards` (case-insensitive, exact name matching).
   - `id -> card`.
   - `mtgo_id -> card`.
   - `oracle_id -> list of printings`.
   - `set_code -> list of cards` (optional, for set chooser).
3. **TinyDB / local cache**
   - The comment `TODO load into a tinyDB object ?` exists but probably not needed if we keep the parsed JSON in memory and build dict indexes.
   - For persistence across app restarts, the JSON file itself is the cache.
4. **Memory consideration**
   - `default_cards` is ~150 MB JSON / ~500 MB in Python memory.
   - `all_cards` is larger; evaluate memory usage after indexing, and consider `ijson` or `orjson` if needed.

### Tasks

- [ ] Add `_bulk_data_cache` and `_bulk_indexes` module-level variables in `scryfall.py`.
- [ ] Add `_loadBulkData()` that reads the file, builds indexes, and stores mtime.
- [ ] Add `_isBulkDataStale()` to detect file changes.
- [ ] Refactor `getBulkData()` to return the cached data when fresh.
- [ ] Refactor `searchCardsLocal()` to use the name index.
- [ ] Refactor `getCardById()`, `getCardByMTGOId()` to use id/mtgo indexes.

---

## 4. Search Semantics in Bulk Mode

### Current state

- Exact search filters by `name.lower()`. Good.
- Non-exact search is a slow linear substring scan with no ranking.
- The `set:` filter in `searchCardsOnline` is ignored in bulk mode.

### Proposed design

1. **Exact search**
   - Use the name index.
   - Apply optional filters (`set`, `lang`, `collector_number`) after lookup.
   - Sort by `released_at` descending to keep deterministic behavior consistent with online mode.
2. **Non-exact search**
   - Use substring matching against the name index keys, ranked by length/position.
   - Optionally add fuzzy matching with `fuzzywuzzy` but limit to top N results to keep it fast.
3. **Set filtering**
   - Support `searchDict["set"]` in both local and online modes.
4. **Return consistent API**
   - `searchCards()` already dispatches to local or online. Keep the same return shape: list of `Card` dicts.

### Tasks

- [ ] Implement `_filterCards(cards, searchDict)` for shared filters (set, lang, etc.).
- [ ] Update `searchCardsLocal()` to call the name index and shared filters.
- [ ] Add substring/ranked non-exact search using the index.
- [ ] Ensure sorting matches online mode (newest printing first for exact matches).

---

## 5. Offline-aware Lookup Helpers

The following helpers currently have `USE_BULK_FILES` branches but with limitations:

### `getCardReprints(cardId)`

- Online: walks `prints_search_uri` paginated endpoint.
- Offline: use the `oracle_id` index to find all printings and return their set codes. With `default_cards` this is English-only; with `all_cards` it includes every language.

### `getCardReprintId(cardId, setCode, lang)`

- Online: calls `prints_search_uri` and `ByCodeNumber`.
- Offline: look up all printings by `oracle_id`, filter by `setCode` and `lang`, and return the matching printing.
- If the active mode is `default_cards` (English) and the requested `lang` is not English or is not found locally, fall back to online lookup with rate limiting.

### `getCardById(id)`

- Already supports bulk mode via linear scan. Make it use the id index.

### `getCardByMTGOId(mtgoId)`

- Already supports bulk mode via linear scan. Make it use the mtgo_id index.

### Image fetching

- Bulk files do **not** include card images.
- Card images, thumbnails, and back-face images are always requested from Scryfall on demand (`image_uris`, `card_faces[].image_uris`).
- Cache downloaded images to disk (the app likely already does this). Enforce the 10 req/s limit on image requests.

### Online-only fallback

- If `USE_BULK_FILES` is false, every online call must go through the rate-limited request path.
- When `USE_BULK_FILES` is true, card data lookups are served from bulk; only image requests go online, plus any non-English printing request that cannot be satisfied by `default_cards`.
- Centralize rate-limiting in `utils.py` so both `scrython` requests and direct `requests` calls share the same token bucket.

### Tasks

- [ ] Implement `getCardReprintsLocal(cardId)` using `oracle_id` index.
- [ ] Implement `getCardReprintIdLocal(cardId, setCode, lang)` using `oracle_id` + set filter.
- [ ] Refactor `getCardById()` and `getCardByMTGOId()` to use indexes.
- [ ] Ensure missing cards return `None` instead of raising `IndexError`.

---

## 6. GUI / Settings Integration

### Current state

- `USE_BULK_FILES` is a hard-coded boolean.
- `mtgorg/config.py` exists but is not inspected.

### Proposed design

1. **Config section `[SCRYFALL]`**
   - `use_bulk_files = true/false`
   - `bulk_auto_update = true/false`
   - `bulk_language_mode = english` or `all` (maps to `default_cards` or `all_cards`)
2. **Settings dialog**
   - Add a "Scryfall" tab with:
     - Checkbox "Use offline bulk data (card data only; images still online)"
     - Dropdown "Bulk language coverage" ("English" → `default_cards`, "All languages" → `all_cards`)
     - Checkbox "Auto-update bulk data"
     - Button "Download / Update now" with progress bar
     - Label showing last update and file size
     - Checkbox "Prefer online-only mode" (disables bulk, equivalent to `use_bulk_files = false`)
3. **Startup behavior**
   - If `use_bulk_files` is true and no bulk file exists, prompt the user to download (or auto-download if `bulk_auto_update` is true).
   - If a download is required, show a modal progress dialog.
   - If the user cancels or is offline, keep `use_bulk_files = false` for the current session (online-only fallback) and log a warning.

### Tasks

- [ ] Read/write `USE_BULK_FILES` and bulk settings from config in `config.py`.
- [ ] Add a settings UI section in the existing settings/preferences dialog.
- [ ] Wire the "Download now" button to `BulkDataManager.downloadBulkData()`.
- [ ] Update `mtgorg/mtgorg_app.py` startup flow to handle missing bulk data.

---

## 7. Tests and Rate-limit Avoidance

### Goal

Make import/parser tests independent of live Scryfall so they are fast and stable.

### Proposed design

1. **Use bulk data in tests**
   - Add a `conftest.py` fixture that downloads the `default_cards` bulk file once (if not present) and sets `constants.USE_BULK_FILES = True` for the test session.
   - Optionally support an env var to switch the test fixture to `all_cards`.
   - Cache the bulk file in `~/.mtgo/scryfall_bulk` (shared with the app) or `tests/data` (override via env var).
   - Mark network-heavy tests with `@pytest.mark.slow` or `@pytest.mark.online` so they can be skipped in CI.
2. **Mock path for pure parser tests**
   - For tests that only validate CSV/MTGA/EDHRec parsing, mock `scryfall.searchCards` to return deterministic IDs.
   - Keep a small mapping of card name → fake UUID in `tests/test_imports.py`.
3. **Integration tests**
   - Keep a small number of tests that verify the real bulk lookup works, but run them only when explicitly requested.

### Tasks

- [ ] Add `tests/conftest.py` with a bulk-data fixture and `USE_BULK_FILES = True`.
- [ ] Add a pytest option `--no-bulk` to skip bulk setup.
- [ ] Add `@pytest.mark.online` to tests that hit the network.
- [ ] Convert parser-only tests to mock `scryfall.searchCards`.
- [ ] Re-run `pytest tests/test_imports.py -v` and confirm 12/12 pass without rate limits.

---

## 8. Error Handling and Edge Cases

- [ ] Handle a corrupt bulk file (fail validation, re-download).
- [ ] Handle interrupted downloads (`.tmp` file remains; resume or restart cleanly).
- [ ] Handle missing bulk data when `USE_BULK_FILES = True` (prompt user, then fall back to online-only mode with a warning).
- [ ] Handle unicode card names in the bulk file (the existing comment `! FIXME handle reading of unicode chars : 暴`).
- [ ] Handle cards without `released_at` (use `""` as before).
- [ ] Prevent `IndexError` in `importexport.py` when no card is found; log and skip instead.

---

## 9. Phased Implementation Order

| Phase | Work | Benefit |
|-------|------|---------|
| 1 | Build `BulkDataManager`, atomic download, metadata. | Reliable offline data source. |
| 2 | Add in-memory indexes and refactor `searchCardsLocal`, `getCardById`, `getCardByMTGOId`. | Fast offline lookups. |
| 3 | Implement offline `getCardReprints` / `getCardReprintId` using the active bulk file, with online fallback when `default_cards` cannot satisfy a non-English request. | Set chooser and reprints work offline in the selected language coverage. |
| 4 | Centralize rate limiting for all online paths. | No more 429 errors. |
| 5 | Config/GUI integration (online-only vs. bulk). | User can choose mode. |
| 6 | Test migration to bulk data + mocks. | Eliminate rate-limit flakiness in tests. |
| 7 | Edge cases and cleanup. | Robust offline/online hybrid mode. |

---

## 10. Files to Touch

- `mtgorg/constants.py`
- `mtgorg/lib/scryfall.py`
- `mtgorg/lib/utils.py` (for download progress/rate limiting helpers)
- `mtgorg/config.py`
- `mtgorg/mtgorg_app.py`
- `mtgorg/widgets/` (settings/preferences dialog)
- `tests/conftest.py`
- `tests/test_imports.py`

---

## Design Decisions

1. **Bulk file choices**
   - Offer two modes that map to Scryfall bulk types:
     - `english` → `default_cards` (English printings, smaller).
     - `all` → `all_cards` (all languages, larger).
   - The user can switch and re-download; online-only mode remains available.

2. **What is offline vs. online**
   - **Offline**: card records, names, IDs, search, oracle text, legalities, prices, reprints, and set-specific printings in the selected language coverage (from `default_cards` or `all_cards`).
   - **Online**: card images only, plus missing non-English printings when `english` mode is active, plus everything when `USE_BULK_FILES` is false.

3. **Keep online-only mode**
   - Always available; do not force bulk downloads.
   - When bulk is enabled but missing/corrupt, fall back to online-only for the session and prompt the user to download later.

4. **Rate limiting**
   - Enforce everywhere: `scrython` endpoints (already has `SlowRateLimiter`), direct HTTP via `utils.getUrlData`, image fetches, and the `/bulk-data` metadata request.
   - Use a shared token bucket so the combined request rate never exceeds Scryfall's limits.
