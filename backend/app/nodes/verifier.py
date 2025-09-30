from datetime import datetime
from typing import List

from app.nodes.base import BaseNode
from app.schemas.agent import AgentState
from langchain_core.messages import HumanMessage

# Verifier / Critic
# checks the itinerary/partial plan against constraints, writes violations into state
# 1. Budget
# 2. Feasibility
# 3. Weather sensitivity
# 4. Preference fit (kid_friendly, mueseum, neighborhood safety/noise level)

VERIFICATION_RULES = [
    "Ensure the planned itinerary is less than the budget constraint",
    "Ensure that the itinerary does not exceed the date constraints",
    "Ensure that no activities are scheduled at the same time",
    "Ensure that activities on the same day are sufficiently co-located",
    "If the trip is less than 10 days away, ensure that the itinerary activities are weather appropriate",
    "Ensure the chosen activities and locations fit the user's preferences",
]


class VerifierNode(BaseNode):
    def __call__(self, state: AgentState):
        print(f"---VERIFIER NODE ({state['session_id']})---")

        # Clear any existing violations before verification
        violations = []

        itinerary = state.get("itinerary", {})
        constraints = state.get("constraints", {})

        # Check if we have an itinerary to validate
        if not itinerary or not itinerary.get("days"):
            violations.append("No itinerary found to validate")
            return {"violations": violations}

        # Validate against constraints
        violations.extend(self._check_budget_constraints(itinerary, constraints))
        violations.extend(self._check_date_constraints(itinerary, constraints))
        violations.extend(self._check_activity_conflicts(itinerary))
        violations.extend(self._check_location_feasibility(itinerary))
        violations.extend(self._check_weather_appropriateness(itinerary, constraints))
        violations.extend(self._check_preference_fit(itinerary, constraints))

        print(f"Found {len(violations)} violations: {violations}")

        return {"violations": violations}

    def _check_budget_constraints(
        self, itinerary: dict, constraints: dict
    ) -> List[str]:
        """Check if itinerary exceeds budget constraints"""
        violations = []

        budget = constraints.get("budget")
        total_cost = itinerary.get("total_cost_usd")

        if budget and total_cost and total_cost > budget:
            violations.append(
                f"Total cost ${total_cost:.2f} exceeds budget of ${budget:.2f}"
            )

        return violations

    def _check_date_constraints(self, itinerary: dict, constraints: dict) -> List[str]:
        """Check if itinerary fits within date constraints"""
        violations = []

        start_date = constraints.get("start_date")
        end_date = constraints.get("end_date")
        days = itinerary.get("days", [])

        if start_date and end_date and days:
            # Check if number of days fits within the date range
            try:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                max_days = (end - start).days + 1

                if len(days) > max_days:
                    violations.append(
                        f"Itinerary has {len(days)} days but only {max_days} days available between {start_date} and {end_date}"
                    )
            except (ValueError, AttributeError):
                # If date parsing fails, skip this check
                pass

        return violations

    def _check_activity_conflicts(self, itinerary: dict) -> List[str]:
        """Check for time conflicts within the same day"""
        violations = []

        days = itinerary.get("days", [])
        for day_idx, day in enumerate(days):
            activities = day.get("activities", [])
            # Simple check - if we have more than 8 activities in a day, flag as potential conflict
            if len(activities) > 8:
                violations.append(
                    f"Day {day_idx + 1} has {len(activities)} activities which may cause scheduling conflicts"
                )

        return violations

    def _check_location_feasibility(self, itinerary: dict) -> List[str]:
        """Check if activities on the same day are geographically feasible"""
        violations = []

        days = itinerary.get("days", [])
        for day_idx, day in enumerate(days):
            activities = day.get("activities", [])
            locations = [
                activity.get("location")
                for activity in activities
                if activity.get("location")
            ]

            # If we have activities with very different location types, flag as potential issue
            if len(locations) > 5:  # More than 5 different locations in one day
                violations.append(
                    f"Day {day_idx + 1} has activities in {len(locations)} different locations which may not be feasible"
                )

        return violations

    def _check_weather_appropriateness(
        self, itinerary: dict, constraints: dict
    ) -> List[str]:
        """Check if activities are weather appropriate for the time of year"""
        violations = []

        # This is a simplified check - in a real implementation, you'd integrate with weather APIs
        start_date = constraints.get("start_date")
        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                # Check if trip is within 10 days
                days_until_trip = (start - datetime.now()).days
                if 0 <= days_until_trip <= 10:
                    # Flag for weather check - in real implementation, check actual weather
                    days = itinerary.get("days", [])
                    for day_idx, day in enumerate(days):
                        activities = day.get("activities", [])
                        outdoor_activities = [
                            a
                            for a in activities
                            if "outdoor" in a.get("description", "").lower()
                            or "park" in a.get("name", "").lower()
                        ]
                        if outdoor_activities:
                            violations.append(
                                f"Day {day_idx + 1} has outdoor activities - verify weather conditions for {start_date}"
                            )
            except (ValueError, AttributeError):
                pass

        return violations

    def _check_preference_fit(self, itinerary: dict, constraints: dict) -> List[str]:
        """Check if activities match user preferences"""
        violations = []

        preferences = constraints.get("preferences", {})
        if not preferences:
            return violations

        days = itinerary.get("days", [])

        # Check for kid-friendly requirements
        if preferences.get("kid_friendly") and days:
            for day_idx, day in enumerate(days):
                activities = day.get("activities", [])
                adult_only_keywords = ["bar", "nightclub", "casino", "adult"]
                for activity in activities:
                    activity_text = f"{activity.get('name', '')} {activity.get('description', '')}".lower()
                    if any(keyword in activity_text for keyword in adult_only_keywords):
                        violations.append(
                            f"Day {day_idx + 1} includes activities that may not be kid-friendly"
                        )
                        break

        # Check for museum preferences
        if preferences.get("museums") and days:
            museum_found = False
            for day in days:
                activities = day.get("activities", [])
                for activity in activities:
                    if (
                        "museum" in activity.get("name", "").lower()
                        or "museum" in activity.get("description", "").lower()
                    ):
                        museum_found = True
                        break
                if museum_found:
                    break

            if not museum_found:
                violations.append(
                    "No museums included despite user preference for museums"
                )

        return violations
