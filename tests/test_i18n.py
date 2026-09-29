from rank_everything.i18n import SUPPORTED_LANGUAGES, TRANSLATIONS, translate


def test_supported_languages_have_the_same_keys():
    portuguese_keys = set(TRANSLATIONS["pt-BR"])

    assert set(SUPPORTED_LANGUAGES) == set(TRANSLATIONS)
    assert all(set(strings) == portuguese_keys for strings in TRANSLATIONS.values())


def test_translation_formats_values_and_falls_back_to_portuguese():
    assert translate("en-US", "home.item_many", count=3) == "3 items"
    assert translate("unknown", "home.item_many", count=3) == "3 itens"
