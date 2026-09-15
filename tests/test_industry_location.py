from growx_crawl.core.industry import IndustryProfileRegistry
from growx_crawl.core.location import LocationPlanner, LocationRegistry
from growx_crawl.scoring.scorer import LeadScorer


def test_industry_profile_registry():
    jewel_prof = IndustryProfileRegistry.get_profile("jewellery")
    assert jewel_prof.name == "Jewellery"
    assert "gold" in jewel_prof.positive_keywords

    mfg_prof = IndustryProfileRegistry.get_profile("manufacturing")
    assert mfg_prof.name == "Manufacturing"
    assert "factory" in mfg_prof.positive_keywords

    # Dynamic fallback profile for un-registered query
    custom_prof = IndustryProfileRegistry.get_profile("solar panel installation")
    assert custom_prof.name == "Solar Panel Installation"
    assert len(custom_prof.search_terms) > 0


def test_location_planner_multi_city():
    locs = LocationPlanner.plan_locations(locations="Hyderabad,Vijayawada,Bengaluru")
    assert len(locs) == 3
    assert locs[0].city == "Hyderabad"
    assert locs[1].city == "Vijayawada"
    assert locs[2].city == "Bengaluru"


def test_location_planner_state():
    locs = LocationPlanner.plan_locations(state="Telangana")
    assert len(locs) >= 2
    cities = [l.city for l in locs]
    assert "Hyderabad" in cities
    assert "Warangal" in cities


def test_location_planner_country():
    locs = LocationPlanner.plan_locations(country="India", top_cities=10)
    assert len(locs) == 10
