class Collection(dict):
    def __init__(self) -> None:
        self["Name"] = "Test collection"


class Deck(Collection):
    def __init__(self):
        super().__init__()
        self["Name"] = "Test Deck"
