from widgets import onboarding


def test_data_source_requires_choice(qtApp):
    wizard = onboarding.OnboardingWizard()
    page = wizard.dataPage

    assert not page.isComplete()
    page.onChoice("online")
    assert page.isComplete()
    assert page.values()["use_bulk"] is False
    page.onChoice("offline")
    assert page.values()["use_bulk"] is True


def test_onboarding_only_lists_available_themes(qtApp, monkeypatch):
    monkeypatch.setattr(onboarding.constants, "availableThemes", lambda: {"fusion": "Fusion"})

    wizard = onboarding.OnboardingWizard()

    assert [card.key for card in wizard.appearancePage.cards] == ["fusion"]
