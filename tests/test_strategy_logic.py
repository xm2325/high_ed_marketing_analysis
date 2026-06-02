from src.strategy_logic import ConversionScenario, simulate_offer_holder_conversion, make_access_outreach_scenario

def test_conversion_scenario_uses_contacted_share():
    out = simulate_offer_holder_conversion(ConversionScenario(1000, 0.30, 0.50, 2, 3, 1))
    assert out['baseline_firms'] == 300
    assert out['additional_firms'] == 30
    assert out['scenario_firms'] == 330

def test_conversion_scenario_is_capped():
    out = simulate_offer_holder_conversion(ConversionScenario(100, 0.95, 1.0, 20, 20, 20))
    assert out['scenario_firms'] == 100

def test_access_scenario():
    out = make_access_outreach_scenario(1000, 0.5, 0.1, 4)
    assert out['baseline_attendees'] == 100
    assert out['additional_attendees'] == 20
