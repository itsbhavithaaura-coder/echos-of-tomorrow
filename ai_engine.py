import json
import os
import re
from typing import Any, Dict, List, Tuple

from openai import OpenAI, OpenAIError

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - optional dependency for local dev
    pass


PROBLEM_CHOICES = [
    "Climate & Environmental Protection",
    "Water Scarcity & Conservation",
    "Food Waste & Hunger",
    "Agriculture & Crop Sustainability",
    "Energy Conservation & Electricity Shortages",
    "Traffic Congestion & Urban Planning",
    "Natural Disasters & Emergency Preparedness",
    "Other Real-World Problem",
]

BUDGET_CHOICES = ["Very limited", "Moderate", "Flexible"]
PRIORITY_CHOICES = [
    "Minimize cost",
    "Maximize environmental impact",
    "Help the greatest number of people",
    "Achieve results quickly",
    "Focus on long-term sustainability",
    "Balance cost, impact, and feasibility",
]
STRESS_CHOICES = [
    "No unexpected change",
    "Budget decreases by 50%",
    "Water availability suddenly decreases",
    "The number of people affected doubles",
    "Volunteer availability decreases",
    "Electricity prices increase",
    "A flood warning arrives earlier than expected",
    "The proposed solution takes twice as long as expected",
    "The community does not cooperate as planned",
    "Other change (describe below)",
]

REQUIRED_FIELDS = {
    "name": "name",
    "summary": "summary",
    "assumptions": "assumptions",
    "strategy": "strategy",
    "how_it_works": "how_it_works",
    "resources_required": "resources_required",
    "benefits": "benefits",
    "risks": "risks",
    "affected_stakeholders": "affected_stakeholders",
    "short_term_impacts": "short_term_impacts",
    "long_term_impacts": "long_term_impacts",
    "stress_test_response": "stress_test_response",
    "practical_recommendations": "practical_recommendations",
    "comparison": "comparison",
    "short_term_consequences": "short_term_consequences",
    "long_term_consequences": "long_term_consequences",
    "unintended_consequences": "unintended_consequences",
    "key_assumptions": "key_assumptions",
    "first_step": "first_step",
}


def _safe_text(value: Any, default: str = "Not specified") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned if cleaned else default
    return str(value)


def _extract_json_array(raw_text: str) -> List[Dict[str, Any]]:
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("The AI response was empty.")

    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        text = match.group(0)
    elif text.startswith("{"):
        text = "[" + text + "]"

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"The AI response was not valid JSON: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("The AI response did not return a JSON array.")
    return data


def _normalize_scenario(raw: Dict[str, Any], index: int) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"Scenario {index + 1} is not an object.")

    normalized: Dict[str, Any] = {}
    aliases = {
        "name": ["name", "scenario_name", "title"],
        "summary": ["summary", "executive_summary", "overview"],
        "assumptions": ["assumptions", "key_assumptions", "assumptions_and_uncertainties"],
        "strategy": ["strategy", "proposed_strategy", "approach"],
        "how_it_works": ["how_it_works", "implementation", "how_it_could_be_implemented"],
        "resources_required": ["resources_required", "resources", "needed_resources"],
        "benefits": ["benefits", "potential_benefits", "benefit"],
        "risks": ["risks", "potential_risks", "risk"],
        "affected_stakeholders": ["affected_stakeholders", "stakeholders"],
        "short_term_impacts": ["short_term_impacts", "short_term_consequences", "short_term_effects"],
        "long_term_impacts": ["long_term_impacts", "long_term_consequences", "long_term_effects"],
        "stress_test_response": ["stress_test_response", "stress_response"],
        "practical_recommendations": ["practical_recommendations", "recommendations", "first_step"],
        "comparison": ["comparison", "key_difference", "tradeoff_summary"],
        "short_term_consequences": ["short_term_consequences", "short_term_effects", "short_term_impact"],
        "long_term_consequences": ["long_term_consequences", "long_term_effects", "long_term_impact"],
        "unintended_consequences": ["unintended_consequences", "possible_unintended_consequences", "side_effects"],
        "key_assumptions": ["key_assumptions", "assumptions_and_uncertainties", "assumptions"],
        "first_step": ["first_step", "practical_first_step", "next_step"],
    }

    for canonical, choices in aliases.items():
        value = None
        for key in choices:
            if key in raw and raw.get(key) is not None:
                value = raw.get(key)
                break
        normalized[canonical] = _safe_text(value, f"Not specified for scenario {index + 1}.")

    if not normalized["name"] or normalized["name"].lower() == "not specified":
        normalized["name"] = f"Scenario {index + 1}"

    return normalized


def _scenario_prompt(problem: str, situation: str, budget: str, priority: str, stress: str) -> str:
    return f"""
    You are the scenario engine for Echoes of Tomorrow.
    Create a decision-support tool output for a real-world problem.

    Challenge: {problem}
    Situation: {situation}
    Available budget: {budget}
    Main priority: {priority}
    Stress test assumption: {stress}

    Requirements:
    - Generate exactly three distinct strategies.
        - Make them meaningfully different and specific to the selected challenge and situation. Never introduce an unrelated challenge.
        - Adapt practical recommendations to the selected budget and main priority.
        - Explain how the stress-test assumption changes each scenario and provide a response to it.
    - Use this structure for each scenario object:
      - name
            - summary
            - assumptions
      - strategy
      - how_it_works
      - resources_required
      - benefits
      - risks
            - affected_stakeholders
            - short_term_impacts
            - long_term_impacts
            - stress_test_response
            - practical_recommendations
            - comparison
      - short_term_consequences
      - long_term_consequences
      - unintended_consequences
      - key_assumptions
      - first_step
    - Respect constraints and uncertainty.
    - Do not invent statistics, facts, or verified measurements.
    - Clearly label assumptions and uncertainties.
    - Explain that these are plausible scenarios, not guaranteed predictions.
    - Return ONLY a valid JSON array with exactly three objects.
    """


def _offline_scenarios(
    problem: str,
    situation: str,
    budget: str,
    priority: str,
    stress: str,
) -> List[Dict[str, str]]:
    problem_lower = problem.lower()
    if "traffic" in problem_lower or "urban" in problem_lower:
        if any(term in situation.lower() for term in ("school", "pickup", "pick-up", "student")):
            profile = {
                "focus": "school-zone queues, crossing safety, and reliable bus access",
                "optimistic": "Coordinate school staff and transit operators on a pickup route, protected crossing points, and bus access; expand only if queues and safety improve.",
                "realistic": "Observe one school pickup period, keep the nearest crossing clear, and test one supervised curb or turning change using existing staff.",
                "risk_action": "pause the route change, place staff at the highest-risk crossing, and review school and bus access",
                "risk": "queues may move into residential streets, and pickup changes may disadvantage families with limited schedule flexibility or students needing accessible transport",
                "unintended": "Staggered pickup may conflict with caregiver work schedules or transfer queues to nearby streets.",
                "stakeholders": "students; caregivers; school staff; bus operators; pedestrians; nearby residents; people with disabilities",
            }
        else:
            profile = {
                "focus": "traffic flow, road safety, and reliable trips",
                "optimistic": "Coordinate traffic staff and transit operators on a corridor plan that pairs safer crossings with signal or curb changes; scale after local review.",
                "realistic": "Observe the busiest junction, identify one queue or crossing issue, and test a reversible timing or curb adjustment.",
                "risk_action": "restore the safer layout, check nearby streets, and review crossing access before resuming",
                "risk": "queues may move to nearby streets, and changes could disadvantage pedestrians, disabled travelers, or people with inflexible schedules",
                "unintended": "A faster route for one group may increase cut-through traffic or delay people crossing the road.",
                "stakeholders": "commuters; pedestrians; cyclists; transit riders; nearby residents; local businesses; emergency services",
            }
    elif "water" in problem_lower:
        profile = {
            "focus": "reliable water access and reduced avoidable demand",
            "optimistic": "Coordinate leak repairs and locally suitable conservation with utilities and affected households; expand reuse or storage only after feasibility review.",
            "realistic": "Check the highest-use locations for leaks and focus limited maintenance on essential water services first.",
            "risk_action": "protect essential water services, communicate fair limits, and prioritize urgent household needs",
            "risk": "restrictions may shift costs unevenly or reduce access for people with essential needs",
            "unintended": "Restrictions may shift work to households or reduce water available for small local businesses.",
            "stakeholders": "households; schools; health services; local utilities; farmers; water-system workers",
        }
    elif "food" in problem_lower:
        profile = {
            "focus": "food access and less avoidable food waste",
            "optimistic": "Coordinate demand tracking with safe surplus recovery and a reliable local partner; grow the network only when storage and handling remain safe.",
            "realistic": "Track surplus at one meal period, adjust the next order, and arrange a small safe handoff with an established partner.",
            "risk_action": "protect food safety, notify recipient partners, and focus on donations that remain dependable",
            "risk": "food-safety failures, uneven access, or unreliable donations could harm recipients or partners",
            "unintended": "A new handoff schedule may make food access less predictable for recipients or add work for kitchen staff.",
            "stakeholders": "residents experiencing food insecurity; food providers; volunteers; schools; local organizations; health inspectors",
        }
    elif "agriculture" in problem_lower or "crop" in problem_lower:
        profile = {
            "focus": "farm resilience, crop health, and dependable production",
            "optimistic": "Test locally suitable soil or water practices with participating farmers, then share results before wider adoption.",
            "realistic": "Choose one field-level practice that fits existing equipment and compare it with current routines before expanding.",
            "risk_action": "protect essential farm operations and avoid requiring all farms to adopt the same practice",
            "risk": "new practices may add labor or costs before benefits are clear, especially for smaller farms",
            "unintended": "A practice that suits one farm may not fit another farm's soil, labor, or equipment.",
            "stakeholders": "farmers; farm workers; buyers; local communities; agricultural advisers; food distributors",
        }
    elif "energy" in problem_lower or "electricity" in problem_lower:
        profile = {
            "focus": "reliable electricity and manageable energy costs",
            "optimistic": "Pair efficiency improvements with a continuity plan for critical services, then assess whether local demand flexibility is practical.",
            "realistic": "Identify one avoidable source of peak use and adjust operating times without reducing essential service access.",
            "risk_action": "prioritize critical loads and inform people who depend on powered equipment about planned changes",
            "risk": "conservation measures or outages may disproportionately affect people who rely on powered equipment or services",
            "unintended": "Shifting demand may inconvenience workers or move costs to households with fewer alternatives.",
            "stakeholders": "households; small businesses; utilities; hospitals; schools; energy workers",
        }
    elif "disaster" in problem_lower or "emergency" in problem_lower:
        profile = {
            "focus": "timely warnings, safe evacuation, and continuity of essential services",
            "optimistic": "Coordinate accessible alerts, evacuation support, and service continuity with residents and local responders; review the plan after a drill.",
            "realistic": "Check one alert channel and one evacuation route, then document who needs help and who is responsible for contacting them.",
            "risk_action": "use the agreed alert trigger and prioritize residents who need transport or accessible warnings",
            "risk": "communication gaps or inaccessible plans may leave some residents without timely support",
            "unintended": "A warning plan relying on one channel may miss residents with limited connectivity or language access.",
            "stakeholders": "residents; emergency responders; health services; schools; local government; mutual-aid groups",
        }
    elif "climate" in problem_lower or "environment" in problem_lower:
        situation_lower = situation.lower()
        if any(term in situation_lower for term in ("flood", "stormwater", "runoff", "heavy rain", "drain")):
            profile = {
                "focus": "stormwater runoff and flood exposure around the area you described",
                "optimistic": "Coordinate drain maintenance and resident reports, then assess whether a small rain garden or permeable surface can safely hold runoff without shifting it downstream.",
                "realistic": "Map where water collects, report blocked drains, and keep existing drainage paths clear before considering construction.",
                "risk_action": "move safe drain checks earlier, notify exposed households, and do not redirect flow without downstream review",
                "risk": "heavy rain may exceed local drainage capacity, and a poorly placed intervention could move water toward downstream homes",
                "unintended": "Drain clearing or added storage may shift maintenance burdens or change where water collects in the park.",
                "stakeholders": "nearby households; park users; maintenance crews; downstream residents; emergency services; municipal planners",
            }
        elif any(term in situation_lower for term in ("heat", "hot", "shade", "heatwave")):
            profile = {
                "focus": "heat exposure and access to shade in the area you described",
                "optimistic": "Coordinate shade, water access, and heat-safety checks at the most exposed locations, then assess whether durable tree or surface changes are suitable.",
                "realistic": "Prioritize existing shaded spaces and safe access during the hottest periods before adding new infrastructure.",
                "risk_action": "extend access to existing cool spaces and check on people most exposed to heat",
                "risk": "temporary shade may not protect people outdoors for long periods, and new planting takes time to mature",
                "unintended": "New trees or shade structures may require water, maintenance, or placement trade-offs in shared spaces.",
                "stakeholders": "outdoor workers; older adults; children; nearby residents; park users; public health services; maintenance crews",
            }
        elif any(term in situation_lower for term in ("air quality", "smoke", "emissions", "pollution")):
            profile = {
                "focus": "local air-quality exposure around the source described",
                "optimistic": "Coordinate source checks, clear public updates, and exposure-reduction measures with the affected site and health services.",
                "realistic": "Identify when and where exposure is most noticeable, communicate practical precautions, and refer suspected violations to the responsible agency.",
                "risk_action": "issue clear exposure updates and prioritize sensitive groups while authorities assess the source",
                "risk": "informal observations may not establish pollutant levels, and exposure-reduction steps can be harder for people without flexible schedules",
                "unintended": "Changing activity at one location may shift emissions or disturbance to another neighborhood.",
                "stakeholders": "nearby residents; outdoor workers; children; people with respiratory conditions; local businesses; public health and environment agencies",
            }
        else:
            profile = {
                "focus": "the specific local climate or environmental pressure described",
                "optimistic": "Work with the affected site and nearby residents to address the identified pressure, then expand only after local review confirms the approach fits.",
                "realistic": "Document where and when the described issue occurs, then test one low-cost action at the most affected location.",
                "risk_action": "protect the most exposed people or site first and avoid shifting impacts to a neighboring area",
                "risk": "a local action may not address the underlying cause, and shifting activity could move the burden to another site",
                "unintended": "A visible improvement at one site may conceal unresolved effects elsewhere or create extra maintenance work.",
                "stakeholders": "nearby residents; site users; local businesses; maintenance teams; public services; affected habitats",
            }
    else:
        profile = {
            "focus": f"the main outcome described for {problem}",
            "optimistic": "Coordinate the affected service providers and community on a targeted pilot, then expand only when local feedback supports it.",
            "realistic": "Map the immediate bottleneck and test one small change with the people directly affected.",
            "risk_action": "protect essential access first and pause changes that could shift harm to another group",
            "risk": "a narrow response may shift costs or leave less-visible groups underserved",
            "unintended": "A process change may add work for staff or make access less predictable for some users.",
            "stakeholders": "people directly affected; service providers; local organizations; public agencies; nearby communities",
        }

    budget_guidance = {
        "very limited": "use existing staff, simple observations, and reversible changes; defer capital work until local evidence supports it",
        "moderate": "phase spending and reserve some capacity for monitoring, access needs, and adjustment",
        "flexible": "stage any durable investment and verify local needs and maintenance capacity before scaling",
    }.get(budget.lower(), "match scope to available resources and verify local costs before committing")
    priority_lower = priority.lower()
    if "cost" in priority_lower or "budget" in priority_lower:
        priority_guidance = "keep recurring costs visible and avoid permanent work before the pilot is reviewed"
    elif "quick" in priority_lower or "fast" in priority_lower:
        priority_guidance = "start with a reversible action that can be checked promptly, without skipping safety or access review"
    elif "safety" in priority_lower:
        priority_guidance = "address the highest safety exposure before optimizing convenience or throughput"
    elif "environment" in priority_lower or "sustain" in priority_lower:
        priority_guidance = "favor actions that can be maintained over time and review for shifted environmental effects"
    elif "greatest number" in priority_lower or "people" in priority_lower:
        priority_guidance = "include groups with limited access when choosing where and how to apply the intervention"
    else:
        priority_guidance = f"use '{priority}' as the deciding criterion when selecting among locally feasible actions"

    stress_active = bool(stress and stress.lower() != "no unexpected change")
    stress_label = stress.strip() if stress_active else "No additional stress-test assumption was selected"
    situation_context = situation.strip()
    if len(situation_context) > 260:
        situation_context = situation_context[:257].rsplit(" ", 1)[0] + "..."

    variants = [
        {
            "name": "Optimistic Future",
            "strategy": profile["optimistic"],
            "assumptions": "Partners coordinate, affected groups can participate, and local checks show the change is safe to expand.",
            "benefits": f"Could improve {profile['focus']} while creating evidence and shared ownership for future decisions.",
            "risks": f"The approach needs coordination and may not transfer to every location; {profile['risk']}.",
            "short": "A coordinated pilot can show early changes and reveal what needs adjustment before wider use.",
            "long": "If local reviews continue to support it, the intervention could become a maintained part of planning for this specific issue.",
            "unintended": profile["unintended"],
            "stress_response": (
                f"If {stress_label}, use the pilot's review trigger to {profile['risk_action']}."
                if stress_active
                else f"{stress_label}; if conditions worsen, {profile['risk_action']}."
            ),
            "recommendation": f"With a {budget} budget, {budget_guidance}. To prioritize {priority}, {priority_guidance}. Begin with: {profile['optimistic']}",
            "difference": "Highest potential reach; depends most on coordination, monitoring, and successful expansion.",
        },
        {
            "name": "Realistic Future",
            "strategy": profile["realistic"],
            "assumptions": f"Existing staff and local partners can support one bounded action; results may be gradual. The decision priority is {priority}.",
            "benefits": "Creates a manageable first step, keeps the plan adjustable, and makes resource use easier to review.",
            "risks": f"A small intervention may not address the full cause; {profile['risk']}.",
            "short": "A focused pilot can start with existing capacity and provide observations for the next decision.",
            "long": "Continued reviews can show whether to maintain, revise, or stop the action without assuming the problem is solved.",
            "unintended": profile["unintended"],
            "stress_response": (
                f"If {stress_label}, narrow the pilot and {profile['risk_action']}."
                if stress_active
                else f"{stress_label}; keep within baseline capacity and, if conditions worsen, {profile['risk_action']}."
            ),
            "recommendation": f"With a {budget} budget, {budget_guidance}. To prioritize {priority}, {priority_guidance}. Begin with: {profile['realistic']}",
            "difference": "Most bounded and easiest to evaluate; accepts slower or narrower improvements to preserve feasibility.",
        },
        {
            "name": "Risk Scenario",
            "strategy": f"Protect essential access to {profile['focus']} and prepare to pause or revise the main intervention if conditions worsen.",
            "assumptions": f"The stress-test condition ({stress_label}) strains the plan; capacity or partner availability may fall at the same time.",
            "benefits": "Makes failure conditions visible early and gives decision-makers a way to protect essential needs.",
            "risks": f"The intervention may need to pause, leaving the original problem partly unresolved; {profile['risk']}.",
            "short": "Staff may need to activate a fallback, notify affected groups, and focus limited capacity on the highest-risk locations.",
            "long": "If the stress persists, delayed improvements and uneven impacts may continue; contingency planning reduces uncertainty but cannot remove it.",
            "unintended": "A strict fallback may preserve essential service while delaying improvements for people outside the highest-priority group.",
            "stress_response": (
                f"Stress assumption: {stress_label}. Contingency: "
                f"{profile.get('risk_action', 'pause expansion and protect essential access while reviewing the plan')}."
            ),
            "recommendation": f"With a {budget} budget, define a fallback before committing funds. To prioritize {priority}, {priority_guidance}. Set a review trigger for: {stress_label}.",
            "difference": "Lowest planned reach under disruption; prioritizes harm reduction and continuity over expansion.",
        },
    ]

    scenarios = []
    for variant in variants:
        summary = (
            f"For {profile['focus']}, this path responds to the situation you described: {situation_context} "
            f"It is scoped for a {budget} budget and the priority '{priority}'. "
            "Illustrative scenario, not a prediction."
        )
        scenarios.append(
            {
                "name": variant["name"],
                "summary": summary,
                "assumptions": variant["assumptions"],
                "strategy": variant["strategy"],
                "how_it_works": variant["strategy"],
                "resources_required": budget_guidance,
                "benefits": variant["benefits"],
                "risks": variant["risks"],
                "affected_stakeholders": profile["stakeholders"],
                "short_term_impacts": variant["short"],
                "long_term_impacts": variant["long"],
                "stress_test_response": variant["stress_response"],
                "practical_recommendations": variant["recommendation"],
                "short_term_consequences": variant["short"],
                "long_term_consequences": variant["long"],
                "unintended_consequences": variant["unintended"],
                "key_assumptions": variant["assumptions"],
                "first_step": variant["recommendation"],
                "comparison": variant["difference"],
            }
        )
    return scenarios


def _offline_stress_test(
    original_scenarios: List[Dict[str, Any]], stress_change: str, source: str
) -> Dict[str, Any]:
    strategies = []
    for scenario in original_scenarios:
        strategies.append(
            {
                "name": scenario.get("name", "Scenario"),
                "feasibility": "Uncertain; review under the changed condition",
                "reason": f"The offline assessment cannot verify local capacity under this assumption: {stress_change}.",
                "new_risks": scenario.get("risks", "The changed condition may create new risks."),
                "required_resources": scenario.get("resources_required", "Reassess available resources."),
                "adaptations": scenario.get("practical_recommendations", "Review the plan with affected stakeholders."),
                "tradeoffs": "Preserving essential services may require delaying expansion or shifting limited resources.",
            }
        )
    return {
        "headline": "Offline stress-test assessment",
        "summary": f"Illustrative reassessment for the assumption: {stress_change}. Validate this assessment against local evidence before acting.",
        "strategies": strategies,
        "source": source,
    }


def generate_scenarios(
    problem: str,
    situation: str,
    budget: str,
    priority: str,
    stress: str,
    include_metadata: bool = False,
) -> Any:
    if not situation or not situation.strip():
        raise ValueError("Please describe the situation before generating scenarios.")

    if not problem or not problem.strip():
        raise ValueError("Please choose a problem category before generating scenarios.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        scenarios = _offline_scenarios(problem, situation, budget, priority, stress)
        return (scenarios, "offline-demo") if include_metadata else scenarios

    try:
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a careful scenario-planning assistant. Return only valid JSON arrays with the required structure and no extra commentary."},
                {"role": "user", "content": _scenario_prompt(problem, situation, budget, priority, stress)},
            ],
            temperature=0.7,
            max_tokens=2500,
        )
        content = response.choices[0].message.content
        data = _extract_json_array(content)
        scenarios = [_normalize_scenario(item, idx) for idx, item in enumerate(data[:3])]
        if len(scenarios) != 3:
            raise ValueError("The model did not return exactly three scenarios.")
    except (OpenAIError, TypeError, ValueError) as exc:
        scenarios = _offline_scenarios(problem, situation, budget, priority, stress)
        return (scenarios, "offline-demo-api-error") if include_metadata else scenarios

    source = "live-openai"
    return (scenarios, source) if include_metadata else scenarios


def generate_stress_test(
    problem: str,
    situation: str,
    budget: str,
    priority: str,
    original_scenarios: List[Dict[str, Any]],
    stress_change: str,
) -> Dict[str, Any]:
    if not stress_change or stress_change == "No unexpected change":
        return {
            "headline": "No stress test was requested.",
            "summary": "Select a changed assumption to re-evaluate the strategies.",
            "strategies": [],
            "source": "not-run",
        }

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _offline_stress_test(original_scenarios, stress_change, "offline-demo")

    try:
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        original_summary = json.dumps(original_scenarios, ensure_ascii=True, indent=2)
        prompt = f"""
            Reassess the following strategies under a changed condition.

            Challenge: {problem}
            Situation: {situation}
            Original budget: {budget}
            Priority: {priority}
            Changed assumption: {stress_change}

            Existing strategies:
            {original_summary}

            Explain:
            - Which strategy remains feasible.
            - Which strategy becomes less effective.
            - What new risks appear.
            - What resources are now required.
            - What adaptations could help.
            - Which trade-offs have changed.
            - Label this as a hypothetical stress test and clearly note uncertainty.

            Return ONLY valid JSON with keys:
            {
              "headline": "...",
              "summary": "...",
              "strategies": [
                {
                  "name": "...",
                  "feasibility": "Feasible / Less effective / Uncertain",
                  "reason": "...",
                  "new_risks": "...",
                  "required_resources": "...",
                  "adaptations": "...",
                  "tradeoffs": "..."
                }
              ]
            }
            """
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Return only valid JSON with the exact structure requested."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        if not isinstance(parsed, dict) or "strategies" not in parsed:
            raise ValueError("The model response did not include stress-test strategies.")
        parsed["source"] = "live-openai"
        return parsed
    except (OpenAIError, TypeError, ValueError) as exc:
        return _offline_stress_test(original_scenarios, stress_change, "offline-demo-api-error")


def get_ripple_effects(problem: str) -> List[str]:
    problem_lower = (problem or "").lower()
    if "food" in problem_lower:
        return [
            "Reducing food waste can reduce disposal costs and improve resource efficiency, but it may require stronger demand forecasting and food-safety procedures.",
            "Redistribution can support students who need meals, but it depends on storage timing, local rules, and reliable coordination.",
            "A more disciplined waste plan may reduce unnecessary purchases and improve canteen budgeting, while also requiring more staff time for tracking and adjustments.",
        ]
    if "water" in problem_lower:
        return [
            "Lower water demand can cut costs and reduce stress on local systems, but it may require behavioral change or new infrastructure.",
            "Water efficiency measures can improve resilience during shortages, yet they may shift burdens across households or seasons.",
            "Conservation might create operational trade-offs, such as maintenance costs or changes in service timing for different groups.",
        ]
    if "climate" in problem_lower or "environment" in problem_lower:
        return [
            "Environmental actions can reduce pressure on ecosystems, but they may require behavior changes or upfront investment in infrastructure.",
            "Short-term reductions in harm may not be enough to address long-term climate or ecological risks without continued monitoring and adaptation.",
        ]
    return [
        "A decision can create both immediate benefits and longer-term knock-on effects across budgets, local stakeholders, and operational capacity.",
        "The impacts depend on how well the plan is coordinated, monitored, and adapted over time.",
    ]
