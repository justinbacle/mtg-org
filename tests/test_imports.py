
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


MTGO_DEK = """<?xml version="1.0" encoding="UTF-8"?>
<Deck xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NetDeckID>0</NetDeckID>
  <PreconstructedDeckID>0</PreconstructedDeckID>
  <Cards CatID="49370" Quantity="4" Sideboard="false" Name="Blur Sliver" Annotation="0"/>
  <Cards CatID="49367" Quantity="2" Sideboard="false" Name="Bonescythe Sliver" Annotation="0"/>
  <Cards CatID="53444" Quantity="3" Sideboard="false" Name="Diffusion Sliver" Annotation="0"/>
  <Cards CatID="25855" Quantity="4" Sideboard="false" Name="Gemhide Sliver" Annotation="0"/>
  <Cards CatID="49359" Quantity="4" Sideboard="false" Name="Manaweft Sliver" Annotation="0"/>
  <Cards CatID="49830" Quantity="2" Sideboard="false" Name="Megantic Sliver" Annotation="0"/>
  <Cards CatID="49579" Quantity="4" Sideboard="false" Name="Predatory Sliver" Annotation="0"/>
  <Cards CatID="49512" Quantity="3" Sideboard="false" Name="Sentinel Sliver" Annotation="0"/>
  <Cards CatID="26383" Quantity="4" Sideboard="false" Name="Sinew Sliver" Annotation="0"/>
  <Cards CatID="49471" Quantity="2" Sideboard="false" Name="Striking Sliver" Annotation="0"/>
  <Cards CatID="53616" Quantity="2" Sideboard="false" Name="Belligerent Sliver" Annotation="0"/>
  <Cards CatID="80335" Quantity="4" Sideboard="false" Name="Lead the Stampede" Annotation="0"/>
  <Cards CatID="49415" Quantity="2" Sideboard="false" Name="Hive Stirrings" Annotation="0"/>
  <Cards CatID="79632" Quantity="16" Sideboard="false" Name="Forest" Annotation="0"/>
  <Cards CatID="53622" Quantity="4" Sideboard="false" Name="Sliver Hive" Annotation="0"/>
  <Cards CatID="53756" Quantity="1" Sideboard="true" Name="Sliver Hivelord" Annotation="0"/>
  <Cards CatID="49355" Quantity="4" Sideboard="true" Name="Galerider Sliver" Annotation="0"/>
</Deck>
"""
MTGO_DEK_DECKLIST = [
    [4, '63227937-86cc-45e0-9e9e-8c7ab80cbaef'],
    [2, 'a26bb68b-1830-470a-8cea-91edc7db0c57'],
    [3, 'fb110a55-c8f9-4627-82c2-edb10db4f380'],
    [4, 'f09135b0-fd57-4205-aa74-c9869946c264'],
    [4, 'fe45433b-e124-44d7-9463-dada39310148'],
    [2, '46d7778f-b436-418b-9454-8a53a1c87d4b'],
    [4, 'a2e37de8-66a1-4afa-aa6f-1151f849dfa8'],
    [3, '74c28560-e6ac-4be9-a253-22c4613b0d90'],
    [4, '6cd2ed50-cd9a-45d9-a59a-6279be1ab308'],
    [2, '4ee9254b-3d98-4477-a82e-1450cf3ee96e'],
    [2, 'b78b8268-b090-4012-a3ba-5daab491f78d'],
    [4, '9e76b676-c7a3-4de6-a78d-3059a0df83f2'],
    [2, 'e4399e19-d05d-4bb3-9aff-c4133ddd2850'],
    [16, '32af9f41-89e2-4e7a-9fec-fffe79cae077'],
    [4, '91cef7ce-aa9f-4659-ac24-394c5ab9f77c'],
    [1, 'ba4106de-20c7-48cf-8a36-8c6913b46c89'],
    [4, '425f5d1b-9989-4fd1-88e2-6c3108aefa0b']
]


def test_CSV_import():
    importer = importexport.CSV_importer()
    importer.loadInput(URZA_GATHERER_CSV)
    assert importer.deckList == URZA_GATHERER_DECKLIST


def test_MTGA_import():
    importer = importexport.MTGA_importer()
    importer.loadInput(MTGA_TXT)
    assert importer.deckList == MTGA_DECKLIST


def test_MTGO_DEK_import():
    importer = importexport.MTGO_DEK_importer()
    importer.loadInput(MTGO_DEK)
    assert importer.deckList == MTGO_DEK_DECKLIST
