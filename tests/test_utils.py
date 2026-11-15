from lib import utils


def test_half_mana_symbols():
    assert utils.setManaText("{HW}") == "1⁄2w"
    assert utils.setManaText("{HU}") == "1⁄2u"
    assert utils.setManaText("{HB}") == "1⁄2b"
    assert utils.setManaText("{HR}") == "1⁄2r"
    assert utils.setManaText("{HG}") == "1⁄2g"


def test_gleemax_mana_symbol():
    assert utils.setManaText("{1000000}") == "1000000"


def test_phyrexian_uses_generic_glyph():
    assert utils.setManaText("{W/P}") == "p"


def test_get_card_mana_cost_prefers_top_level_split_cost():
    card = {
        "mana_cost": "{1}{R} // {1}{U}",
        "card_faces": [{"mana_cost": "{1}{R}"}, {"mana_cost": "{1}{U}"}],
    }
    assert utils.getCardManaCost(card) == "{1}{R} // {1}{U}"


def test_get_card_mana_cost_uses_first_face_for_transform():
    card = {
        "mana_cost": None,
        "card_faces": [{"mana_cost": "{U}"}, {"mana_cost": ""}],
    }
    assert utils.getCardManaCost(card) == "{U}"


def test_set_mana_text_uses_fraction_slashes_for_split_cards():
    assert utils.setManaText("{1}{R} // {1}{U}") == "1r ⁄⁄ 1u"
