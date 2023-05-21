# Resets all data to test data

import connector

import constants

db = connector.getDB()
db.drop_tables()

db.table(constants.DECKS_TABLE_NAME).insert(
    {
        "name": "deckname1",
        "cardList": [
            "8afceb13-877a-4256-9ba6-851b6924ffd9"
        ]
    }
)

db.table(constants.COLLECTION_TABLE_NAME).insert(
    {
        "name": "collection1",
        "cardList": [
            "7f3dd06a-a085-4157-a90d-b0ed4974d756"
        ]
    }
)
