"""Deterministic stand-in for the Scryfall-backed lookups used by the importers.

The real functions require network access and quickly exhaust Scryfall's rate
limits when the whole test suite runs. These fakes keep parser tests focused on
parsing while retaining the real Scryfall IDs the tests assert on.
"""

SETS = [
    {"code": "mma", "name": "Modern Masters"},
    {"code": "ths", "name": "Theros"},
    {"code": "rtr", "name": "Return to Ravnica"},
    {"code": "mbs", "name": "Mirrodin Besieged"},
    {"code": "isd", "name": "Innistrad"},
    {"code": "gtc", "name": "Gatecrash"},
    {"code": "ktk", "name": "Khans of Tarkir"},
    {"code": "frf", "name": "Fate Reforged"},
    {"code": "tmp", "name": "Tempest"},
    {"code": "6ed", "name": "Classic Sixth Edition"},
    {"code": "mm3", "name": "Modern Masters 2017"},
    {"code": "zen", "name": "Zendikar"},
    {"code": "exp", "name": "Zendikar Expeditions"},
    {"code": "emn", "name": "Eldritch Moon"},
    {"code": "hou", "name": "Hour of Devastation"},
    {"code": "wwk", "name": "Worldwake"},
    {"code": "c14", "name": "Commander 2014"},
    {"code": "tst", "name": "Test Set"},
]

CARDS = [
    {"name": "Aether Vial", "set": "mma", "id": "6774c646-76d4-4991-a7f3-b753ef200ce5"},
    {"name": "Anax and Cymede", "set": "ths", "id": "63cb977e-bd42-43b1-83d1-124e7a413aca"},
    {"name": "Angel of Serenity", "set": "rtr", "id": "f10d82f7-7759-457e-a9bb-f9a5bd968f82"},
    {"name": "Ashen Rider", "set": "ths", "id": "602e43b1-1b1c-4eb1-be0a-61b673646c6f"},
    {"name": "Black Sun's Zenith", "set": "mbs", "id": "03bdcf52-50b8-42c0-9665-931d83f5f314"},
    {"name": "Snapcaster Mage", "set": "isd", "id": "9e5b279e-4670-4a1e-87d0-3cab7e4f9e58"},
    {"name": "Breeding Pool", "set": "gtc", "id": "ece3bcdd-cb33-4923-b919-ba57a327d3cd"},
    {"name": "Rattleclaw Mystic", "set": "ktk", "id": "4fb6c2e0-eeaa-4d60-aab7-2b8c739a9278"},
    {"name": "Opulent Palace", "set": "ktk", "id": "21326575-80b9-4a4e-a93c-6880ec6575d5"},
    {"name": "Tasigur the Golden Fang", "set": "frf", "id": "81f93ac5-d149-4ccf-8b99-13ecf3190c29"},
    {"name": "Abandon Hope", "set": "tmp", "id": "942cf220-472c-48f6-8f60-993939ea5ab8"},
    {"name": "Abduction", "set": "6ed", "id": "63c82bef-50d6-4d25-bc3f-dda2826fc99c"},
    {"name": "Advent of the Wurm", "set": "mm3", "id": "ba3b5e35-5448-4115-a9c5-6ac14013c904"},
    {"name": "Verdant Catacombs", "set": "zen", "id": "7abd2723-2851-4f1a-b2d0-dfcb526472c3"},
    {"name": "Graven Cairns", "set": "exp", "id": "a3028c5b-2f81-4aee-9455-ebb0bd81ccaa"},
    {"name": "Olivia Voldaren", "set": "isd", "id": "ed750692-ba6a-4a89-ad6d-92fda7edc2cb"},
    {"name": "Abandon Reason", "set": "emn", "id": "18c0b3b3-bb62-42c5-9869-386af0540a9b"},
    {"name": "Abandoned Sarcophagus", "set": "hou", "id": "c191fb87-f111-4ac2-a52a-3af103a9314e"},
    {"name": "Amulet of Vigor", "set": "wwk", "id": "997bc933-ac30-477b-a4e1-5333b796a99d"},
    {"name": "Arcane Lighthouse", "set": "c14", "id": "977e3112-b141-44c0-9e8d-d7a0b93092b9"},
    {"name": "Lightning Bolt", "set": "tst", "id": "7673784e-db4b-43a1-8d55-1bb9fc1e284f"},
    {"name": "Shock", "set": "tst", "id": "b23900fb-efe9-43ab-9f67-4545dd01fb9c"},
    {"name": "Spitting Earth", "set": "tst", "id": "de1aa8f9-8200-4ddd-9ab5-1a8181cc1792"},
    {"name": "Blaze", "set": "tst", "id": "b16d0422-61ea-4039-b1c1-e590ace9156e"},
    {"name": "Breath of Darigaaz", "set": "tst", "id": "cbb60f03-7bcf-46a3-9310-c2067d9c5396"},
    {"name": "Aether Flash", "set": "tst", "id": "780f9197-e910-4c7a-bb4b-2c4a94903c39"},
    {"name": "Flametongue Kavu", "set": "tst", "id": "1b3a5139-3341-409e-be33-184897c7398e"},
    {"name": "Ensnaring Bridge", "set": "tst", "id": "cf825a56-4870-463a-a2ef-eec86be891db"},
    {"name": "Sulfuric Vortex", "set": "tst", "id": "3253a624-50cc-4a8a-9b0c-9902aa53775f"},
    {"name": "Flametongue Yearling", "set": "tst", "id": "33ab05b5-d6f5-439c-9aed-1a58ceb282ad"},
]

MTGO_IDS = {
    49370: "63227937-86cc-45e0-9e9e-8c7ab80cbaef",
    49367: "a26bb68b-1830-470a-8cea-91edc7db0c57",
    53444: "fb110a55-c8f9-4627-82c2-edb10db4f380",
    25855: "f09135b0-fd57-4205-aa74-c9869946c264",
    49359: "fe45433b-e124-44d7-9463-dada39310148",
    49830: "46d7778f-b436-418b-9454-8a53a1c87d4b",
    49579: "a2e37de8-66a1-4afa-aa6f-1151f849dfa8",
    49512: "74c28560-e6ac-4be9-a253-22c4613b0d90",
    26383: "6cd2ed50-cd9a-45d9-a59a-6279be1ab308",
    49471: "4ee9254b-3d98-4477-a82e-1450cf3ee96e",
    53616: "b78b8268-b090-4012-a3ba-5daab491f78d",
    80335: "9e76b676-c7a3-4de6-a78d-3059a0df83f2",
    49415: "e4399e19-d05d-4bb3-9aff-c4133ddd2850",
    79632: "32af9f41-89e2-4e7a-9fec-fffe79cae077",
    53622: "91cef7ce-aa9f-4659-ac24-394c5ab9f77c",
    53756: "ba4106de-20c7-48cf-8a36-8c6913b46c89",
    49355: "425f5d1b-9989-4fd1-88e2-6c3108aefa0b",
}


def _cardsById(cardId: str) -> list[dict]:
    return [card for card in CARDS if card["id"] == cardId]


def searchCards(searchDict: dict, exact: bool = False) -> list[dict]:
    name = searchDict.get("name", "").lower()
    setCode = searchDict.get("set")
    matches = []
    for card in CARDS:
        if card["name"].lower() != name:
            continue
        if setCode is not None and card["set"].lower() != setCode.lower():
            continue
        matches.append(dict(card))
    return matches


def getSets(force: bool = False) -> list[dict]:
    return [dict(setData) for setData in SETS]


def getCardById(cardId: str) -> dict | None:
    matches = _cardsById(cardId)
    return dict(matches[0]) if matches else None


def getCardReprints(cardId: str) -> list[str]:
    return sorted({card["set"] for card in _cardsById(cardId)})


def getCardPrintings(cardId: str) -> list[dict]:
    matches = _cardsById(cardId)
    return [dict(card) for card in matches] if matches else []


def getCardByMTGOId(mtgoId: int) -> dict | None:
    cardId = MTGO_IDS.get(mtgoId)
    if cardId is None:
        return None
    return {"id": cardId, "set": "tst", "name": f"mtgo-{mtgoId}"}
