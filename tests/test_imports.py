
import sys
import os
sys.path.append(os.getcwd())  # FIXME Remove

from lib import importexport  # noqa E402


URZA_GATHERER_CSV = """  # noqa E501
"sep=,"
Name,Type,Color,Rarity,Author,Power,Toughness,Mana cost,Converted mana cost,Count,Foil count,Special foil count,Price,Foil price,Number,Set,Set code,ID,Multiverse ID,Comments,To trade,Condition,Grading,Languages,TCG ID,Cardmarket ID,Scryfall ID
"Demonic Tutor","Sorcery",Black,Uncommon,"Douglas Shuler",0,0,(1)(B),2,1,0,0,19.57‎€,19.57‎€,105,"Revised Edition",3ED,19939,1155,,0,"1xGood","","",1388,5541,881e5922-b464-4a1a-b074-664bd6c0a7f6
"Enlightened Tutor","Instant",White,Uncommon,"Dan Frazier",0,0,(W),1,1,0,0,11.13‎€,11.13‎€,14,"Mirage",MIR,3709,3489,,0,"1xGood","","",5051,8269,cbac1d27-15e2-4e2f-82ab-625a16e096cb
"Mystical Tutor","Instant",Blue,Uncommon,"David O'Connor",0,0,(U),1,1,0,0,3.46‎€,3.46‎€,80,"Mirage",MIR,3571,3351,,0,"1xGood","","",5159,8131,5d98101f-e32a-4a4a-a649-faa920d111ee
"Vampiric Tutor","Instant",Black,Rare,"Gary Leach",0,0,(B),1,1,0,0,27.76‎€,27.76‎€,72,"Visions",VIS,3863,3629,,0,"1xGood","","",5954,8423,0a07cba3-2e8d-48ec-a6f8-4d2edfcd833d
"Worldly Tutor","Instant",Green,Uncommon,"David O'Connor",0,0,(G),1,1,0,0,9.01‎€,9.01‎€,255,"Mirage",MIR,3644,3424,,0,"1xGood","","",5300,8204,f00115bc-b551-4bf5-a121-bebb37201575
"""
URZA_GATHERER_DECKLIST = [
    ['1', '881e5922-b464-4a1a-b074-664bd6c0a7f6'],
    ['1', 'cbac1d27-15e2-4e2f-82ab-625a16e096cb'],
    ['1', '5d98101f-e32a-4a4a-a649-faa920d111ee'],
    ['1', '0a07cba3-2e8d-48ec-a6f8-4d2edfcd833d'],
    ['1', 'f00115bc-b551-4bf5-a121-bebb37201575']
]

MTGA_TXT = """# R_Blast
4 Lightning Bolt
2 Shock
2 Spitting Earth
1 Blaze
1 Breath of Darigaaz
2 Æther Flash
2 Flametongue Kavu
1 Ensnaring Bridge
1 Sulfuric Vortex
2 Flametongue Yearling
"""
MTGA_DECKLIST = [
    [4, 'f29ba16f-c8fb-42fe-aabf-87089cb214a7'],
    [2, '59fa8e8d-bcb8-47bf-b71a-df11c8d0f2c9'],
    [2, 'de1aa8f9-8200-4ddd-9ab5-1a8181cc1792'],
    [1, 'b16d0422-61ea-4039-b1c1-e590ace9156e'],
    [1, 'cbb60f03-7bcf-46a3-9310-c2067d9c5396'],
    [2, '780f9197-e910-4c7a-bb4b-2c4a94903c39'],
    [2, '21a3f8d6-80ff-4292-871e-e19907841448'],
    [1, 'cf825a56-4870-463a-a2ef-eec86be891db'],
    [1, '0463e989-ba32-4a46-a82f-e0d6daf3cd51'],
    [2, '33ab05b5-d6f5-439c-9aed-1a58ceb282ad']
]


def test_CSV_import():
    csvImporter = importexport.CSV_importer()
    csvImporter.loadInput(URZA_GATHERER_CSV)
    assert csvImporter.deckList == URZA_GATHERER_DECKLIST


def test_MTGA_import():
    csvImporter = importexport.MTGA_importer()
    csvImporter.loadInput(MTGA_TXT)
    assert csvImporter.deckList == MTGA_DECKLIST
