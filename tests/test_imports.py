from mtgorg.lib import importexport  # noqa E402


URZA_GATHERER_CSV = """
"sep=,"
Name,Type,Color,Rarity,Author,Power,Toughness,Mana cost,Converted mana cost,Count,Foil count,Special foil count,Price,Foil price,Number,Set,Set code,ID,Multiverse ID,Comments,To trade,Condition,Grading,Languages,TCG ID,Cardmarket ID,Scryfall ID
"Demonic Tutor","Sorcery",Black,Uncommon,"Douglas Shuler",0,0,(1)(B),2,1,0,0,19.57‎€,19.57‎€,105,"Revised Edition",3ED,19939,1155,,0,"1xGood","","",1388,5541,881e5922-b464-4a1a-b074-664bd6c0a7f6
"Enlightened Tutor","Instant",White,Uncommon,"Dan Frazier",0,0,(W),1,1,0,0,11.13‎€,11.13‎€,14,"Mirage",MIR,3709,3489,,0,"1xGood","","",5051,8269,cbac1d27-15e2-4e2f-82ab-625a16e096cb
"Mystical Tutor","Instant",Blue,Uncommon,"David O'Connor",0,0,(U),1,1,0,0,3.46‎€,3.46‎€,80,"Mirage",MIR,3571,3351,,0,"1xGood","","",5159,8131,5d98101f-e32a-4a4a-a649-faa920d111ee
"Vampiric Tutor","Instant",Black,Rare,"Gary Leach",0,0,(B),1,1,0,0,27.76‎€,27.76‎€,72,"Visions",VIS,3863,3629,,0,"1xGood","","",5954,8423,0a07cba3-2e8d-48ec-a6f8-4d2edfcd833d
"Worldly Tutor","Instant",Green,Uncommon,"David O'Connor",0,0,(G),1,1,0,0,9.01‎€,9.01‎€,255,"Mirage",MIR,3644,3424,,0,"1xGood","","",5300,8204,f00115bc-b551-4bf5-a121-bebb37201575
"""  # noqa E501
URZA_GATHERER_DECKLIST = [
    ["1", "881e5922-b464-4a1a-b074-664bd6c0a7f6"],
    ["1", "cbac1d27-15e2-4e2f-82ab-625a16e096cb"],
    ["1", "5d98101f-e32a-4a4a-a649-faa920d111ee"],
    ["1", "0a07cba3-2e8d-48ec-a6f8-4d2edfcd833d"],
    ["1", "f00115bc-b551-4bf5-a121-bebb37201575"],
]

MTG_STUDIO_CSV = """Name,Edition,Qty,Foil
Aether Vial,MMA,1,No
Anax and Cymede,THS,4,Yes
"""
MTG_STUDIO_DECKLIST = [
    ["1", "6774c646-76d4-4991-a7f3-b753ef200ce5"],
    ["4", "63cb977e-bd42-43b1-83d1-124e7a413aca"],
]

DECKBOX_CSV = """Count,Tradelist Count,Name,Edition,Card Number,Condition,Language,Foil,Signed,Artist Proof,Altered Art,Mis,
4,4,Angel of Serenity,Return to Ravnica,1,Near Mint,English,,,,,,,,
1,1,Ashen Rider,Theros,187,Near Mint,English,,,,,,,,
1,0,Anax and Cymede,Theros,186,Near Mint,English,foil,,,,,,,
"""  # noqa E501
DECKBOX_DECKLIST = [
    ["4", "f10d82f7-7759-457e-a9bb-f9a5bd968f82"],
    ["1", "602e43b1-1b1c-4eb1-be0a-61b673646c6f"],
    ["1", "63cb977e-bd42-43b1-83d1-124e7a413aca"],
]

DECKED_BUILDER_CSV = """Total Qty,Reg Qty,Foil Qty,Card,Set,Mana Cost,Card Type,Color,Rarity,Mvid,Single Price,Single Foil Price,Total Price,Price Source,Notes
3,2,1,Black Sun's Zenith,Mirrodin Besieged,XBB,Sorcery,Black,Rare,214061,1.00,6.25,7.25,cardshark,
1,1,0,Snapcaster Mage,Innistrad,1U,Creature  - Human Wizard,Blue,Rare,227676,26.60,115.00,141.60,cardshark,
"""  # noqa E501
DECKED_BUILDER_DECKLIST = [
    [1, "03bdcf52-50b8-42c0-9665-931d83f5f314"],
    [1, "9e5b279e-4670-4a1e-87d0-3cab7e4f9e58"],
]

PUCATRADE_CSV = """Count,Name,Edition,Rarity,Expansion Symbol,Points,Foil,Condition,Language,Status,Entered Date,Updated Date,Exported Date
1,Breeding Pool,Gatecrash,RARE,GTC,1009,0,"Near Mint","English",NOT FOR TRADE,"11/19/2014","11/29/2014","11/30/2014",19632
8,Rattleclaw Mystic,Khans of Tarkir,RARE,KTK,194,0,"Near Mint","English",HAVE,"11/29/2014","11/29/2014","11/30/2014",25942
1,Opulent Palace,Khans of Tarkir,UNCOMMON,KTK,461,1,"Near Mint","English",HAVE,"11/29/2014","11/29/2014","11/30/2014",25928
1,Tasigur the Golden Fang,Fate Reforged,RARE,FRF,1045,1,"Near Mint","English",HAVE,"1/24/2015","1/24/2015","2/03/2015",270
1,Tasigur the Golden Fang,Fate Reforged,RARE,FRF,1045,1,"Near Mint","English",HAVE,"1/24/2015","1/24/2015","2/03/2015",270
"""  # noqa E501
PUCATRADE_DECKLIST = [
    ["1", "ece3bcdd-cb33-4923-b919-ba57a327d3cd"],
    ["8", "4fb6c2e0-eeaa-4d60-aab7-2b8c739a9278"],
    ["1", "21326575-80b9-4a4e-a93c-6880ec6575d5"],
    ["1", "81f93ac5-d149-4ccf-8b99-13ecf3190c29"],
    ["1", "81f93ac5-d149-4ccf-8b99-13ecf3190c29"],
]

MTG_GOLDFISH_CSV = """"Card","Set","Quantity","Price","Condition","Language","Foil","Signed"
"Abandon Hope","Tempest",2,0.24,M,en,No,No
"Abduction","Classic Sixth Edition",1,0.33,M,en,No,No
"Advent of the Wurm","Modern Masters 2017",1,0.99,M,en,Yes,No
"Advent of the Wurm","Modern Masters 2017",3,0.35,M,en,No,No"""
MTG_GOLDFISH_DECKLIST = [
    ["2", "942cf220-472c-48f6-8f60-993939ea5ab8"],
    ["1", "63c82bef-50d6-4d25-bc3f-dda2826fc99c"],
    ["1", "ba3b5e35-5448-4115-a9c5-6ac14013c904"],
    ["3", "ba3b5e35-5448-4115-a9c5-6ac14013c904"],
]

TCGPLAYER_CSV = """Quantity,Name,Simple Name,Set,Card Number,Set Code,Printing,Condition,Language,Rarity,Product ID,SKU
1,Verdant Catacombs,Verdant Catacombs,Zendikar,229,ZEN,Normal,Near Mint,English,Rare,33470,315319
1,Graven Cairns,Graven Cairns,Zendikar Expeditions,28,EXP,Foil,Near Mint,English,Mythic,110729,3042202
1,Olivia Voldaren,Olivia Voldaren,Innistrad,215,ISD,Foil,Near Mint,English,Mythic,52181,500457
"""
TCGPLAYER_DECKLIST = [
    ["1", "7abd2723-2851-4f1a-b2d0-dfcb526472c3"],
    ["1", "a3028c5b-2f81-4aee-9455-ebb0bd81ccaa"],
    ["1", "ed750692-ba6a-4a89-ad6d-92fda7edc2cb"],
]

DECKSTATS_CSV = '''amount,card_name,is_foil,is_pinned,set_id,set_code
1,"Abandon Reason",0,0,147,"EMN"
2,"Abandoned Sarcophagus",0,0,187,"HOU"'''
DECKSTATS_DECKLIST = [
    [1, "18c0b3b3-bb62-42c5-9869-386af0540a9b"],
    [1, "c191fb87-f111-4ac2-a52a-3af103a9314e"],
]


MTG_MANAGER_CSV = """Quantity,Name,Code,PurchasePrice,Foil,Condition,Language,PurchaseDate
1,"Amulet of Vigor",WWK,18.04,0,0,0,5/6/2018
1,"Arcane Lighthouse",C14,3.83,0,0,0,5/6/2018"""
MTG_MANAGER_DECKLIST = [
    ["1", "997bc933-ac30-477b-a4e1-5333b796a99d"],
    ["1", "977e3112-b141-44c0-9e8d-d7a0b93092b9"],
]


def test_CSV_import_Urza():
    importer = importexport.CSV_importer()
    importer.loadInput(URZA_GATHERER_CSV)
    assert importer.deckList == URZA_GATHERER_DECKLIST


def test_CSV_import_MtgStudio():
    importer = importexport.CSV_importer()
    importer.loadInput(MTG_STUDIO_CSV)
    assert importer.deckList == MTG_STUDIO_DECKLIST


def test_CSV_import_DeckBox():
    importer = importexport.CSV_importer()
    importer.loadInput(DECKBOX_CSV)
    assert importer.deckList == DECKBOX_DECKLIST


def test_CSV_import_DeckedBuilder():
    importer = importexport.CSV_importer()
    importer.loadInput(DECKED_BUILDER_CSV)
    assert importer.deckList == DECKED_BUILDER_DECKLIST


def test_CSV_import_Pucatrade():
    importer = importexport.CSV_importer()
    importer.loadInput(PUCATRADE_CSV)
    assert importer.deckList == PUCATRADE_DECKLIST


def test_CSV_import_MtgGoldfish():
    importer = importexport.CSV_importer()
    importer.loadInput(MTG_GOLDFISH_CSV)
    assert importer.deckList == MTG_GOLDFISH_DECKLIST


def test_CSV_import_TcgPlayer():
    importer = importexport.CSV_importer()
    importer.loadInput(TCGPLAYER_CSV)
    assert importer.deckList == TCGPLAYER_DECKLIST


def test_CSV_import_Deckstats():
    importer = importexport.CSV_importer()
    importer.loadInput(DECKSTATS_CSV)
    assert importer.deckList == DECKSTATS_DECKLIST


def test_CSV_import_MTGManager():
    importer = importexport.CSV_importer()
    importer.loadInput(MTG_MANAGER_CSV)
    assert importer.deckList == MTG_MANAGER_DECKLIST


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
    [4, "77c6fa74-5543-42ac-9ead-0e890b188e99"],
    [2, "298747bb-eb40-4b58-bb22-4ac2bc1d795c"],
    [2, "de1aa8f9-8200-4ddd-9ab5-1a8181cc1792"],
    [1, "b16d0422-61ea-4039-b1c1-e590ace9156e"],
    [1, "cbb60f03-7bcf-46a3-9310-c2067d9c5396"],
    [2, "780f9197-e910-4c7a-bb4b-2c4a94903c39"],
    [2, "1b3a5139-3341-409e-be33-184897c7398e"],
    [1, "67a052ea-d717-4c01-87bb-9e4d7f66785e"],
    [1, "3253a624-50cc-4a8a-9b0c-9902aa53775f"],
    [2, "33ab05b5-d6f5-439c-9aed-1a58ceb282ad"],
]


def test_MTGA_import():
    importer = importexport.MTGA_importer()
    importer.loadInput(MTGA_TXT)
    assert importer.deckList == MTGA_DECKLIST


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
    [4, "63227937-86cc-45e0-9e9e-8c7ab80cbaef"],
    [2, "a26bb68b-1830-470a-8cea-91edc7db0c57"],
    [3, "fb110a55-c8f9-4627-82c2-edb10db4f380"],
    [4, "f09135b0-fd57-4205-aa74-c9869946c264"],
    [4, "fe45433b-e124-44d7-9463-dada39310148"],
    [2, "46d7778f-b436-418b-9454-8a53a1c87d4b"],
    [4, "a2e37de8-66a1-4afa-aa6f-1151f849dfa8"],
    [3, "74c28560-e6ac-4be9-a253-22c4613b0d90"],
    [4, "6cd2ed50-cd9a-45d9-a59a-6279be1ab308"],
    [2, "4ee9254b-3d98-4477-a82e-1450cf3ee96e"],
    [2, "b78b8268-b090-4012-a3ba-5daab491f78d"],
    [4, "9e76b676-c7a3-4de6-a78d-3059a0df83f2"],
    [2, "e4399e19-d05d-4bb3-9aff-c4133ddd2850"],
    [16, "32af9f41-89e2-4e7a-9fec-fffe79cae077"],
    [4, "91cef7ce-aa9f-4659-ac24-394c5ab9f77c"],
    [1, "ba4106de-20c7-48cf-8a36-8c6913b46c89"],
    [4, "425f5d1b-9989-4fd1-88e2-6c3108aefa0b"],
]


def test_MTGO_DEK_import():
    importer = importexport.MTGO_DEK_importer()
    importer.loadInput(MTGO_DEK)
    assert importer.deckList == MTGO_DEK_DECKLIST


EDHREC_URL = "https://edhrec.com/deckpreview/0qIYCFl_tMPMnmGV0swWeg"

EDHREC_PLAYLIST = [
    [1, "c5f9326a-2a41-45b3-97c3-548f0bdc0882"],
    [1, "c9045fcb-b633-4c35-8058-6234311551ae"],
    [1, "169356e0-46dc-4096-8e66-36726454f104"],
    [1, "882be812-fc76-4493-abe2-2101603399ce"],
    [1, "8dae6f88-cfc1-4f5b-afc7-b8c88e28bf24"],
    [1, "10ce686a-eecd-4b32-a882-9a6ca3274ae6"],
    [1, "eb40c41c-f5f9-4323-b6ac-e28e405909d0"],
    [1, "28d92b13-8b23-4c78-b690-c5d9ca835809"],
    [1, "80b5b7e1-52c2-4453-b3c0-efe2cebad6ce"],
    [1, "0f375bb9-1294-4f43-8f0c-504ed6cfb7d0"],
    [1, "147a0ccf-3408-48c7-b4a8-6d81aed39f18"],
    [1, "9738d616-b38f-4968-89d6-805ae368e2d4"],
    [1, "9dda1e1c-b330-42e0-8547-97e2afc7615f"],
    [1, "75994e0b-b0c7-4b0d-8f48-4be303429bd6"],
    [1, "e203daaf-bd68-4251-9106-00299b3ad662"],
    [1, "b76f2de1-ea17-40b0-8d90-4c4369516eff"],
    [1, "46eff31d-f460-48f2-aab7-8b9b89cd87fe"],
    [1, "10caa17e-3892-435a-8f48-f3d6e4619114"],
    [1, "99eed556-06b8-4063-8d72-24f010dd372e"],
    [1, "c643146f-da7b-4cc0-b874-4accad99ccce"],
    [1, "9bfaa187-580f-4bb7-bc9b-0d3998098833"],
    [1, "e19cd136-0541-4db0-997f-20a58ec8d028"],
    [1, "45d3fc69-6c5e-4ede-9f8d-c1cee096a78a"],
    [1, "a9e2bb08-9be0-4046-9c22-7b132ce5f506"],
    [1, "84a9485a-d356-4cbe-b257-b62008a21328"],
    [1, "33ca68a6-474e-4d86-bffa-ee4bddb4a3cf"],
    [1, "eb2e9534-2eda-4e41-8a87-181e5eb8c328"],
    [1, "bdb27a86-0fbd-4123-9c8e-630c855d5e9e"],
    [1, "2a84a604-7b05-4716-bcd8-40d2acdb76e8"],
    [1, "473fb06e-5c71-4370-a5d7-7753d84d0fd6"],
    [1, "e09ff04d-cdcc-4798-b89a-9ad08ef52ad9"],
    [1, "0ee79399-715c-4c46-9fa1-e76b1087f009"],
    [1, "c0ffb58f-459a-4965-b1d6-a25442baf9c2"],
    [1, "fa0e1874-d172-42dd-bebc-5e2c2d3e0b6d"],
    [1, "46db3811-db1d-4f69-8143-a93f64d0297b"],
    [1, "fc6eb9f3-0f7b-4623-806e-5e604a05d470"],
    [1, "feb7ad1b-4466-48f7-b46d-cc83d4e22b51"],
    [1, "f9c69d75-651f-4b75-b65d-79999d2069f6"],
    [1, "194c6ee7-c220-41a5-bf44-5e1d8d92879b"],
    [1, "721df547-d777-4247-b130-a4e247445b04"],
    [1, "c4e83abd-6f15-491e-9253-90af9f6f1025"],
    [1, "2f5689e2-d8a2-442b-8027-f89686adcb67"],
    [1, "65c7067d-61ec-4558-b0d4-0048d2d86743"],
    [1, "f2a3107d-bb96-45c6-97ac-b6c6b84cbad4"],
    [1, "8296a455-21d5-498e-9029-2bdf0da855a8"],
    [1, "bf4797b0-4d0a-433f-b891-b14f96fd1484"],
    [1, "382bfdec-ba99-4bf4-8461-34eee979f9dc"],
    [1, "2b5df03d-2463-468b-b444-d946eeb1c96d"],
    [1, "4f92d5e6-6834-47d4-8c1e-7eb425954bd3"],
    [1, "e9e40e2a-e447-4754-a98b-5521e546781f"],
    [1, "40e21394-146e-4648-b81e-63659c0c4764"],
    [1, "206c8529-56df-4ed9-97bc-6c9b5e2a04c4"],
    [1, "cd349f95-3eae-4ef2-abf8-e911bb8e93e5"],
    [1, "b45c4bbf-2c61-4d49-96c8-34a0fb0d6d02"],
    [1, "64a2809e-c441-416c-90ff-6fb1e246dff3"],
    [1, "ad135475-d1f6-4e78-a536-6bf61204c739"],
    [1, "b91dadcb-31e9-43b0-b425-c9311af3e9d7"],
    [1, "0a353fed-e01c-4eaf-afb5-446644628284"],
    [1, "8a605ce4-ede6-44dd-a2ea-e953902be6bd"],
    [1, "eb3ef4da-27c0-4364-a198-f70bea869d9b"],
    [1, "2167439d-792d-471e-9137-ee46dbf7a82d"],
    [1, "a7782044-616e-4d4f-b38f-93320ba19797"],
    [1, "22b01c98-c24b-4255-921f-4820f3d395ea"],
    [1, "bca35012-ecfa-475f-b405-d3143ce99eef"],
    [1, "b3784eff-ab7b-4fd4-9a07-fbc852d116bf"],
    [1, "d96266b3-a7cb-40ce-a328-ac13719fe5f0"],
    [1, "ab1d1461-1625-4163-aacd-a939f4871fad"],
    [1, "96feebe2-0a6b-4df8-8e7d-ee0bb82ac0c1"],
    [1, "cd68c02d-aa09-47ee-b989-65965e82b9f3"],
    [1, "2f4a85ee-235c-448c-b75b-808a70ed95d2"],
    [1, "36298771-c671-4307-b8b6-31e3ead75be2"],
    [1, "07e73142-a8c0-4bd5-8ab4-cd10e572a975"],
    [1, "a1e048e0-19d2-4076-892d-f8b3104dee37"],
    [1, "fff13d77-8133-4328-b91e-efce229bc331"],
    [1, "029e0450-ceb1-484d-8a18-e769defac428"],
    [1, "71d13f19-482b-4a2e-9692-b7d7caf2f9f5"],
    [1, "70fd0439-294b-454c-b2af-e814b85f4590"],
    [1, "edfd90ee-a142-4a80-b383-802bbee2cef1"],
]


def test_EDHREC_import():
    importer = importexport.EDHRec_importer()
    importer.loadInput(EDHREC_URL)
    assert importer.deckList == EDHREC_PLAYLIST
