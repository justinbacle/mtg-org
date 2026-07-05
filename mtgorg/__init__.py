from scrython.base import ScrythonRequestHandler

# Register a custom User-Agent for all Scryfall API requests.
ScrythonRequestHandler.set_user_agent(
    "MTGOrganizer/1.0 (https://github.com/justinmtg/mtg-org)"
)
