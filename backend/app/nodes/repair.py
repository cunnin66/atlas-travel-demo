# REPAIR / RE-PLANNER
# mutates choices (airport/hotel/day order) and re-executes only affected steps

import uuid
from typing import List

from app.nodes.base import BaseNode
from app.schemas.agent import AgentState, PlanStep


class RepairNode(BaseNode):
    def __call__(self, state: AgentState):
        print(f"---REPAIR NODE ({state['session_id']})---")
        violations = state.get("violations", [])
        current_plan = state.get("plan", [])

        if not violations:
            print("No violations found, nothing to repair")
            return {"plan": current_plan}

        print(f"Processing {len(violations)} violations: {violations}")

        # Generate repair tasks based on violations
        repair_tasks = self._generate_repair_tasks(violations, state)

        # Add repair tasks to the existing plan
        updated_plan = current_plan + repair_tasks

        print(f"Added {len(repair_tasks)} repair tasks to plan")

        return {"plan": updated_plan}

    def _generate_repair_tasks(
        self, violations: List[str], state: AgentState
    ) -> List[PlanStep]:
        """Generate repair tasks based on the violations found"""
        repair_tasks = []

        for violation in violations:
            violation_lower = violation.lower()

            # Budget-related repairs
            if "budget" in violation_lower or "cost" in violation_lower:
                repair_tasks.append(
                    {
                        "id": str(uuid.uuid4()),
                        "depends_on": [],
                        "tool": "budget_optimizer",
                        "args": {
                            "violation": violation,
                            "action": "reduce_costs",
                            "target": "activities_and_accommodations",
                        },
                    }
                )

            # Date/scheduling conflicts
            elif "day" in violation_lower and (
                "conflict" in violation_lower or "activities" in violation_lower
            ):
                repair_tasks.append(
                    {
                        "id": str(uuid.uuid4()),
                        "depends_on": [],
                        "tool": "schedule_optimizer",
                        "args": {
                            "violation": violation,
                            "action": "redistribute_activities",
                            "target": "daily_schedule",
                        },
                    }
                )

            # Location feasibility issues
            elif "location" in violation_lower or "feasible" in violation_lower:
                repair_tasks.append(
                    {
                        "id": str(uuid.uuid4()),
                        "depends_on": [],
                        "tool": "location_optimizer",
                        "args": {
                            "violation": violation,
                            "action": "cluster_activities",
                            "target": "geographic_proximity",
                        },
                    }
                )

            # Weather-related issues
            elif "weather" in violation_lower or "outdoor" in violation_lower:
                repair_tasks.append(
                    {
                        "id": str(uuid.uuid4()),
                        "depends_on": [],
                        "tool": "weather_adapter",
                        "args": {
                            "violation": violation,
                            "action": "substitute_activities",
                            "target": "weather_appropriate_alternatives",
                        },
                    }
                )

            # Preference mismatches
            elif (
                "kid-friendly" in violation_lower
                or "museum" in violation_lower
                or "preference" in violation_lower
            ):
                repair_tasks.append(
                    {
                        "id": str(uuid.uuid4()),
                        "depends_on": [],
                        "tool": "preference_aligner",
                        "args": {
                            "violation": violation,
                            "action": "align_with_preferences",
                            "target": "activity_selection",
                        },
                    }
                )

            # Date range violations
            elif "date" in violation_lower and (
                "exceed" in violation_lower or "available" in violation_lower
            ):
                repair_tasks.append(
                    {
                        "id": str(uuid.uuid4()),
                        "depends_on": [],
                        "tool": "date_adjuster",
                        "args": {
                            "violation": violation,
                            "action": "compress_itinerary",
                            "target": "trip_duration",
                        },
                    }
                )

            # Generic repair task for unhandled violations
            else:
                repair_tasks.append(
                    {
                        "id": str(uuid.uuid4()),
                        "depends_on": [],
                        "tool": "generic_fixer",
                        "args": {
                            "violation": violation,
                            "action": "analyze_and_fix",
                            "target": "itinerary_optimization",
                        },
                    }
                )

        return repair_tasks
