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
- First SQLite bulk-index build shows a progress dialog.
- Non-exact bulk search falls back to fuzzy name matching when substring search
  finds nothing.
- Bulk searches are prefetched in SQLite using indexed columns (CMC, power,
  toughness, loyalty, rarity, type, colors, oracle text, legality, game, price),
  then filtered in Python. Added explicit loyalty coverage.
- Search requests and result counts are written to the status log.
- Art/oracle tag searches fall back to online Scryfall in bulk mode; Include
  Extras is disabled there because bulk data cannot reproduce Scryfall's extras
  filtering.
- Card searches run in a background thread with a status message and wait
  cursor, so the GUI no longer freezes.
- Fixed the CMC search operator/value handling.
- Status bar messages are clickable and open a live session-log viewer.
- Search dropdowns ignore mouse-wheel changes, and Enter triggers search from
  every text field (including CMC, power, toughness, and loyalty).
- Packaging metadata fixed and runtime/dev requirements split.
- Decks support main/sideboard/commander sections, including MTGA and MTGO
  sideboard/commander import parsing.
- Deck format metadata controls which sections are available, with validation
  warnings for deck size, sideboard limits, commander count, and singleton rules.
- Main, sideboard, and commander are shown simultaneously in one grouped table
  with section header rows and a single scrollbar. Commander is listed first;
  collections show only the main list. Section headers follow the active theme.
- Cards can be added to Main, Commander, or Sideboard from the viewer's
  right-click Add menu, and moved between sections with the row context menu.
- Export formats: Cardmarket (flat), MTG Arena text, MTGO `.dek`, and plain text
  with sections. Commander/sideboard inclusion is optional.
- Search results are capped by a configurable limit (default 100), with a
  truncation notice when more cards match.
- Table columns are capped and elided instead of expanding for long names/types.
- Default printing order now prefers booster-available, normal set types and
  regular variants; collector/memorabilia/promo-only printings sort last.
  Supplemental insert sets (The List, Special Guests) are demoted too.

## Optional follow-ups

- Run Pyright in CI (config exists, but it needs the venv/stub setup first).
- Decide on and add a project licence.
- Optionally test/measure the `all_cards` mode end-to-end.
- Add drag/drop to move cards between deck sections.
- Improve format validation edge cases (partners/backgrounds, companions, colour identity).
