import json
import os
from unittest.mock import Mock, patch

from ai_engine import OpenAIError, generate_scenarios


def test_generate_scenarios_returns_three_structured_items():
    scenario = {
        "name": "A practical pathway",
        "summary": "A staged pilot informed by local conditions.",
        "assumptions": "Stakeholders can participate in a small pilot.",
        "strategy": "Use a measured pilot before expanding.",
        "how_it_works": "Track current conditions and adjust the pilot.",
        "resources_required": "Staff time and basic monitoring.",
        "benefits": "Creates evidence for the next decision.",
        "risks": "The pilot may not represent every location.",
        "affected_stakeholders": "Residents, service providers, and local agencies.",
        "short_term_impacts": "A small test begins.",
        "long_term_impacts": "The approach can be refined over time.",
        "stress_test_response": "Adjust the pilot if the assumption occurs.",
        "practical_recommendations": "Choose one location for the pilot.",
        "comparison": "A bounded pilot with an evidence-led expansion path.",
        "short_term_consequences": "A small test begins.",
        "long_term_consequences": "The approach can be refined over time.",
        "unintended_consequences": "Tracking may add staff workload.",
        "key_assumptions": "The pilot context is representative.",
        "first_step": "Choose one location for the pilot.",
    }
    response = Mock()
    response.choices = [
        Mock(message=Mock(content=json.dumps([dict(scenario, name=f"Path {index}") for index in range(1, 4)])))
    ]

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch("ai_engine.OpenAI") as openai:
        openai.return_value.chat.completions.create.return_value = response
        scenarios, source = generate_scenarios(
            problem="Food Waste & Hunger",
            situation="Our college canteen discards surplus food.",
            budget="Very limited",
            priority="Reduce food waste while keeping costs low.",
            stress="Budget drops by 50%",
            include_metadata=True,
        )

    assert isinstance(scenarios, list)
    assert len(scenarios) == 3
    assert source == "live-openai"

    for item in scenarios:
        assert set(item.keys()) >= {
            "name",
            "summary",
            "assumptions",
            "strategy",
            "how_it_works",
            "resources_required",
            "benefits",
            "risks",
            "affected_stakeholders",
            "short_term_impacts",
            "long_term_impacts",
            "stress_test_response",
            "practical_recommendations",
            "comparison",
            "short_term_consequences",
            "long_term_consequences",
            "unintended_consequences",
            "key_assumptions",
            "first_step",
        }
        assert isinstance(item["name"], str)
        assert item["name"].strip()


def test_generate_scenarios_without_api_key_returns_complete_offline_paths():
    situation = "Traffic backs up near the school during afternoon pickup, creating unsafe crossings."
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
        scenarios, source = generate_scenarios(
            problem="Traffic Congestion & Urban Planning",
            situation=situation,
            budget="Very limited",
            priority="Improve safety quickly",
            stress="The number of people affected doubles",
            include_metadata=True,
        )

    assert source == "offline-demo"
    assert [scenario["name"] for scenario in scenarios] == [
        "Optimistic Future",
        "Realistic Future",
        "Risk Scenario",
    ]
    required_fields = {
        "summary",
        "assumptions",
        "benefits",
        "risks",
        "affected_stakeholders",
        "short_term_impacts",
        "long_term_impacts",
        "stress_test_response",
        "practical_recommendations",
        "comparison",
    }
    for scenario in scenarios:
        assert required_fields <= scenario.keys()
        content = " ".join(str(value) for value in scenario.values()).lower()
        assert "traffic" in content
        assert "very limited" in content
        assert "improve safety quickly" in content
        assert "doubles" in content
        assert situation.lower() in content
        assert "very limited" in scenario["practical_recommendations"].lower()
        assert "improve safety quickly" in scenario["practical_recommendations"].lower()
        assert "doubles" in scenario["stress_test_response"].lower()
        assert "school" in scenario["strategy"].lower()
        assert "flood" not in scenario["strategy"].lower()
        assert "illustrative scenario, not a prediction" in scenario["summary"].lower()


def test_climate_scenarios_are_specific_to_local_flooding():
    situation = "After heavy rain, stormwater floods the neighborhood park and reaches nearby homes."
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
        scenarios, source = generate_scenarios(
            problem="Climate & Environmental Protection",
            situation=situation,
            budget="Very limited",
            priority="Protect residents near the park",
            stress="Heavy rainfall arrives earlier than expected",
            include_metadata=True,
        )

    assert source == "offline-demo"
    assert [scenario["name"] for scenario in scenarios] == [
        "Optimistic Future",
        "Realistic Future",
        "Risk Scenario",
    ]
    assert len({scenario["strategy"] for scenario in scenarios}) == 3
    for scenario in scenarios:
        assert any(term in scenario["strategy"].lower() for term in ("stormwater", "runoff", "drainage", "flood"))
        assert "heavy rainfall arrives earlier than expected" in scenario["stress_test_response"].lower()
        assert "protect residents near the park" in scenario["practical_recommendations"].lower()
        assert "very limited" in scenario["practical_recommendations"].lower()
        assert "traffic" not in scenario["strategy"].lower()
        assert "illustrative scenario, not a prediction" in scenario["summary"].lower()


def test_openai_api_error_falls_back_to_offline_scenarios():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch("ai_engine.OpenAI") as openai:
        openai.return_value.chat.completions.create.side_effect = OpenAIError("insufficient quota")
        scenarios, source = generate_scenarios(
            problem="Traffic Congestion & Urban Planning",
            situation="Traffic queues delay buses near the station.",
            budget="Moderate",
            priority="Improve reliability",
            stress="Transit demand doubles",
            include_metadata=True,
        )

    assert source == "offline-demo-api-error"
    assert [scenario["name"] for scenario in scenarios] == [
        "Optimistic Future",
        "Realistic Future",
        "Risk Scenario",
    ]


if __name__ == "__main__":
    test_generate_scenarios_returns_three_structured_items()
    test_generate_scenarios_without_api_key_returns_complete_offline_paths()
    test_climate_scenarios_are_specific_to_local_flooding()
    test_openai_api_error_falls_back_to_offline_scenarios()
    print(json.dumps({"status": "ok"}, indent=2))
