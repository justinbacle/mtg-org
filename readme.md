# MTG Organizer

![](/resources/readme/Screenshot_20230622_174225.png)

## Why another card organizer

I've been using MTG Assistant for a bit, it's clunky, outdated, but mostly works. I'd like to help improve it, but I have no wish to learn a new code langage.
I've looked at other solutions, but found them to be either out of date, unmaintained, behind a paywall, or just missing important features.
Hence this "MTG Organizer" project (name will change for sure)

## Features & Current status

Still early development but the basic features are already here

Here are the lists of things I'd like to have included in this project : 

| Feature | Status |
| --- | --- |
| Basic Search through MTG database | Done |
| Advanced Search through MTG database | Planned, not started |
| Support for other languages than EN | POC with French OK|
|Organizing cards in decks & collections| Done |
|Add deck visualizations and tools| Not started|
|Import| MTGA, CSV(Urza Gatherer, and all supported on mtggoldfish), MTGO(.dek) |
|Export| Not started|
|Scan from webcam| Would be nice to have|
|Synchronization / Connection to other DBs|Local TinyDB for now, can be synchronized with a "drive" solution|
|Multiplatform Windows/Linux/Mac| Windows & Linux OK, macOS untested |

## Known issues

- Card data rely on a cache, which is manually stored for now, this cache is not yet updated when a set comes out. Manual solution for now is to clean the cache manually but plan to implement a cache update system that could be triggered when a new set is out.
- Some sets are not displayed properly if the sets icons and fonts are not available, this should be added in an update feature later
- Mana cost is not repported correctly for non-basic mana types (phyrexian, hybrid, ...) as well as for dual sided cards

## Install / Usage

For now, this is not packaged in an executable file, so you have to run it from source code.

Clone this repo, then when in the folder, install dependencies

- windows (with system python or venv activated)
    - > py -m pip install -r requirements.txt
- linux (with a venv already set)
    - >venv/bin/python -m pip install -r requirements.txt
- mac
    - No idea, I don't use a mac

then run the main program

- windows
    - > py mtgorg_app.py
- linux (venv)
    - > venv/bin/python mtgorg_app.py
- mac
    - no idea

## F.A.Q.

- Where are my decks and collection saved ?
    - (currently) your decks and collections are stored in your homefolder in a mtgorg.db file (which is basically a json file) which contains the most minimal data to store your deck

- Where is the cache stored
    - as for above question, the cache is stored in your homefolder, in a mtgorg_cache.db file, feel free to remove this file to clean the cache.

- Search is slow
    - contrary to most other card organizers, this app does not store the entire dataset of card, and only stores data as you request it. This has the added benefit of not needing you to download the entire datasets before starting to organize your decks.
