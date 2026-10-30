
from google.adk.agents import Agent

def calculate_travel_emissions(mode: str, km: float) -> dict:
    """Calculate travel emissions using illustrative factors."""
    factors = {
        "bus": 0.10,
        "car": 0.20,
        "bike": 0.10,
        "train": 0.04
    }

    mode = mode.lower().strip()

    if mode not in factors:
        return {"error": "Unsupported travel mode"}

    if km < 0:
        return {"error": "Distance cannot be negative"}

    emissions = round(km * factors[mode], 3)

    return {
        "mode": mode,
        "distance_km": km,
        "emissions_kg_co2e": emissions,
        "factor": factors[mode],
        "factor_source": "Illustrative hackathon assumption"
    }


root_agent = Agent(
    name="carbon_coach",
    model="gemini-3.8-flash",
    description="AI carbon footprint calculator",
    instruction="""
    You are Carbon Coach, an AI sustainability assistant.

    Calculate carbon emissions from travel activities.

    Always use calculate_travel_emissions for calculations.
    Never invent emission numbers.
    Explain that emission factors are illustrative assumptions.
    Be friendly and provide practical sustainability tips.
    """,
    tools=[calculate_travel_emissions]
)
