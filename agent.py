
from datetime import date, timedelta
from google.adk.agents import Agent
from google.adk.tools import ToolContext

# DEMO emission factors only.
# Replace with published, region-specific factors
# before claiming real-world accuracy.
# Travel: kg CO2e per passenger-km
TRAVEL = {
    "bus": 0.10,
    "car": 0.20,
    "bike": 0.10,
    "train": 0.04,
    "walking": 0.0,
    "cycling": 0.0
}

# kg CO2e per kWh
ELECTRICITY_FACTOR = 0.70

# Illustrative kg CO2e per meal
FOOD = {
    "vegetarian": 1.0,
    "chicken": 2.0,
    "beef": 5.0
}

# Illustrative kg CO2e per kg of waste
WASTE = {
    "landfill": 0.50,
    "recycled": 0.10
}


def calculate_travel_emissions(mode: str, km: float) -> dict:
    """Calculate emissions for travel in passenger-km."""
    mode = mode.lower().strip()
    if mode not in TRAVEL or km < 0:
        return {"error": "Invalid travel mode or distance"}
    return {
        "category": "travel",
        "details": f"{mode} {km}",
        "kg_co2e": round(TRAVEL[mode] * km, 3),
        "factor": TRAVEL[mode],
        "basis": "illustrative demo assumption"
    }


def calculate_electricity_emissions(kwh: float) -> dict:
    """Calculate electricity emissions using energy in kWh."""
    if kwh < 0:
        return {"error": "kWh cannot be negative"}
    return {
        "category": "electricity",
        "details": f"{kwh} kWh",
        "kg_co2e": round(kwh * ELECTRICITY_FACTOR, 3),
        "factor": ELECTRICITY_FACTOR,
        "basis": "illustrative demo assumption"
    }


def calculate_food_emissions(meal_type: str) -> dict:
    """Calculate illustrative emissions for a meal."""
    meal_type = meal_type.lower().strip()
    if meal_type not in FOOD:
        return {"error": "Unknown meal type"}
    return {
        "category": "food",
        "details": meal_type,
        "kg_co2e": FOOD[meal_type],
        "basis": "illustrative demo assumption"
    }


def calculate_waste_emissions(
    disposal_type: str, kg: float
) -> dict:
    """Calculate illustrative waste disposal emissions."""
    disposal_type = disposal_type.lower().strip()
    if disposal_type not in WASTE or kg < 0:
        return {"error": "Invalid waste type or weight"}
    return {
        "category": "waste",
        "details": f"{disposal_type} {kg} kg",
        "kg_co2e": round(WASTE[disposal_type] * kg, 3),
        "basis": "illustrative demo assumption"
    }


def log_activity(
    category: str,
    details: str,
    kg_co2e: float,
    tool_context: ToolContext
) -> dict:
    """Save a previously calculated activity in session state."""
    if category not in ["travel", "electricity", "food", "waste"]:
        return {"error": "Invalid category"}
    if kg_co2e < 0:
        return {"error": "Invalid emissions"}

    activities = list(
        tool_context.state.get("activities", [])
    )

    record = {
        "date": date.today().isoformat(),
        "category": category,
        "details": details,
        "kg_co2e": round(kg_co2e, 3)
    }

    activities.append(record)
    tool_context.state["activities"] = activities

    return {
        "status": "saved",
        "record": record,
        "total_activities": len(activities)
    }


def get_summary(period: str, tool_context: ToolContext) -> dict:
    """Show logged totals for today, week or all time."""
    period = period.lower().strip()
    if period not in ["today", "week", "all"]:
        return {"error": "Use today, week or all"}

    today = date.today()
    activities = tool_context.state.get("activities", [])
    selected = []

    for activity in activities:
        activity_date = date.fromisoformat(activity["date"])

        if period == "all":
            selected.append(activity)
        elif period == "today" and activity_date == today:
            selected.append(activity)
        elif period == "week" and (
            today - timedelta(days=6)
            <= activity_date <= today
        ):
            selected.append(activity)

    total = round(
        sum(item["kg_co2e"] for item in selected), 3
    )

    return {
        "period": period,
        "total_kg_co2e": total,
        "activity_count": len(selected),
        "activities": selected
    }


def suggest_reductions(tool_context: ToolContext) -> dict:
    """Calculate savings from alternative travel choices."""
    activities = tool_context.state.get("activities", [])
    suggestions = []

    for activity in activities:
        if activity["category"] != "travel":
            continue

        parts = activity["details"].split()
        if len(parts) != 2:
            continue

        try:
            mode = parts[0].lower()
            km = float(parts[1])
        except ValueError:
            continue

        if mode not in TRAVEL:
            continue

        alternatives = ["bus", "train", "cycling"]

        best = min(
            alternatives,
            key=lambda item: TRAVEL[item]
        )

        if TRAVEL[best] < TRAVEL[mode]:
            saving = round(
                (TRAVEL[mode] - TRAVEL[best]) * km, 3
            )
            suggestions.append({
                "original_trip": activity["details"],
                "suggestion": f"Use {best} instead of {mode}",
                "estimated_saving_kg_co2e": saving,
                "basis": "illustrative factors"
            })

    return {"suggestions": suggestions}


root_agent = Agent(
    name="carbon_coach",
    model="gemini-3.8-flash",
    description="AI-powered carbon footprint tracker and coach",
    instruction="""
You are Carbon Coach, an AI sustainability assistant.

You help students, households and campuses understand
and reduce their carbon footprint.

MANDATORY RULES:

1. Understand everyday activities in natural language.
2. Call Python calculation tools for emissions.
3. Never invent emissions, factors, totals or savings.
4. After calculating a new activity, call log_activity
   exactly once with the returned category, details
   and kg_co2e.
5. Never log a calculation that returned an error.
6. For summaries, call get_summary.
7. For recommendations, call suggest_reductions.
8. Clearly say factors are illustrative demo assumptions.
9. If electricity usage is given only in hours,
   ask for kWh or power consumption in watts.
10. Never assume a transport mode if it is ambiguous.
11. Support English, Telugu and Hindi.
12. Do not claim that walking or cycling is feasible
    for every journey.
13. Do not fabricate comparisons with average users.
14. Display results clearly with units of kg CO2e.
15. Do not save hypothetical comparison trips unless
    the user explicitly asks to log them.
""",
    tools=[
        calculate_travel_emissions,
        calculate_electricity_emissions,
        calculate_food_emissions,
        calculate_waste_emissions,
        log_activity,
        get_summary,
        suggest_reductions
    ]
)
