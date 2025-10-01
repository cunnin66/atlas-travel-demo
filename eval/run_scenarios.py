#!/usr/bin/env python3
"""
Evaluation scenarios runner for Atlas Travel Advisor

This script runs various test scenarios to evaluate the AI agent's performance
in travel planning and recommendation tasks.
"""

import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Load .env from parent directory (project root)
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment variables from {env_path}")
    else:
        print("No .env file found in parent directory")
except ImportError:
    print("python-dotenv not installed. Install with: pip install python-dotenv")
    print("Falling back to system environment variables")

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


class ScenarioRunner:
    """Runner for evaluation scenarios"""

    def __init__(self, scenarios_file: str = "scenarios.yml"):
        self.scenarios_file = scenarios_file
        self.scenarios = []
        self.evaluation_criteria = []

    def load_scenarios(self) -> List[Dict[str, Any]]:
        """Load scenarios from YAML file"""
        scenarios_path = Path(__file__).parent / self.scenarios_file

        if not scenarios_path.exists():
            raise FileNotFoundError(f"Scenarios file not found: {scenarios_path}")

        with open(scenarios_path, "r") as f:
            data = yaml.safe_load(f)

        self.scenarios = data.get("scenarios", [])
        self.evaluation_criteria = data.get("evaluation_criteria", [])

        print(
            f"Loaded {len(self.scenarios)} scenarios and {len(self.evaluation_criteria)} evaluation criteria"
        )
        return self.scenarios

    def _create_test_user_and_db(self):
        """Create a test user and database session for evaluation"""
        # Import models after setting up database URL
        from app.models.base import BaseModel
        from app.models.org import Org
        from app.models.user import User

        # Create SQLite engine for testing
        test_db_url = "sqlite:///./test_eval.db"
        engine = create_engine(test_db_url, echo=False)

        # Create all tables
        BaseModel.metadata.create_all(bind=engine)

        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        try:
            # Create or get test organization
            test_org = db.query(Org).filter(Org.name == "Test Org").first()
            if not test_org:
                test_org = Org(name="Test Org", domain="test.com")
                db.add(test_org)
                db.commit()
                db.refresh(test_org)

            # Create or get test user
            test_user = db.query(User).filter(User.email == "test@test.com").first()
            if not test_user:
                test_user = User(
                    email="test@test.com",
                    full_name="Test User",
                    hashed_password="dummy_hash",
                    org_id=test_org.id,
                    is_active=True,
                )
                db.add(test_user)
                db.commit()
                db.refresh(test_user)

            return test_user, db
        except Exception as e:
            db.close()
            raise e

    def _create_prompt_from_scenario(self, scenario: Dict[str, Any]) -> str:
        """Convert scenario input to natural language prompt"""
        input_data = scenario.get("input", {})

        prompt_parts = []

        # Add destination
        if "destination" in input_data:
            prompt_parts.append(f"I want to plan a trip to {input_data['destination']}")

        # Add duration
        if "duration" in input_data:
            prompt_parts.append(f"for {input_data['duration']} days")

        # Add group size
        if "group_size" in input_data:
            group_size = input_data["group_size"]
            if group_size == 1:
                prompt_parts.append("traveling solo")
            else:
                prompt_parts.append(f"for {group_size} people")

        # Add budget
        if "budget" in input_data:
            prompt_parts.append(f"with a budget of ${input_data['budget']}")

        # Add preferences
        preferences = input_data.get("preferences", {})
        if preferences:
            pref_parts = []

            if "interests" in preferences:
                interests = ", ".join(preferences["interests"])
                pref_parts.append(f"interested in {interests}")

            if "accommodation_type" in preferences:
                pref_parts.append(
                    f"preferring {preferences['accommodation_type']} accommodations"
                )

            if "group_type" in preferences:
                pref_parts.append(f"this is a {preferences['group_type']} trip")

            if "ages" in preferences:
                ages = preferences["ages"]
                pref_parts.append(f"with travelers aged {', '.join(map(str, ages))}")

            if "activity_level" in preferences:
                pref_parts.append(
                    f"with {preferences['activity_level']} activity level"
                )

            if "travel_style" in preferences:
                pref_parts.append(f"preferring {preferences['travel_style']}")

            if "budget_priority" in preferences:
                pref_parts.append(
                    f"prioritizing budget for {preferences['budget_priority']}"
                )

            if pref_parts:
                prompt_parts.append(". ".join(pref_parts))

        return ". ".join(prompt_parts) + "."

    async def run_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single evaluation scenario"""
        scenario_name = scenario.get("name", "Unknown")
        print(f"\n--- Running scenario: {scenario_name} ---")

        try:
            # Set up test environment
            test_user, db = self._create_test_user_and_db()

            # Import and create agent service
            from app.schemas.agent import PlanRequest
            from app.services.agent_service import AgentService

            agent_service = AgentService(test_user, db)

            # Convert scenario to prompt
            prompt = self._create_prompt_from_scenario(scenario)
            print(f"Generated prompt: {prompt}")

            # Create plan request (using destination_id=1 as default)
            plan_request = PlanRequest(destination_id=1, prompt=prompt)

            # Execute the agent workflow
            print("Executing agent workflow...")
            plan_response = await agent_service.create_travel_plan(plan_request)

            # Evaluate the response
            evaluation_result = self._evaluate_response(scenario, plan_response)

            # Clean up
            db.close()

            return {
                "scenario_name": scenario_name,
                "status": "completed",
                "prompt": prompt,
                "plan_response": plan_response.model_dump(),
                "evaluation": evaluation_result,
                "passed": evaluation_result["overall_pass"],
            }

        except Exception as e:
            print(f"Error running scenario {scenario_name}: {str(e)}")
            return {
                "scenario_name": scenario_name,
                "status": "failed",
                "error": str(e),
                "passed": False,
            }

    def _evaluate_response(
        self, scenario: Dict[str, Any], plan_response
    ) -> Dict[str, Any]:
        """Evaluate the agent response against scenario expectations"""
        expected_outputs = scenario.get("expected_outputs", [])

        # Extract text content for evaluation
        answer_text = plan_response.answer_markdown.lower()
        itinerary_text = str(plan_response.itinerary.model_dump()).lower()
        combined_text = f"{answer_text} {itinerary_text}"

        # Check each expected output
        checks = []
        for expected in expected_outputs:
            expected_lower = expected.lower()

            # Simple keyword/phrase matching
            found = False
            if any(keyword in combined_text for keyword in expected_lower.split()):
                found = True

            checks.append(
                {
                    "expected": expected,
                    "found": found,
                    "details": f"Looking for: '{expected}' in response",
                }
            )

        # Calculate pass rate
        passed_checks = sum(1 for check in checks if check["found"])
        total_checks = len(checks)
        pass_rate = passed_checks / total_checks if total_checks > 0 else 0

        # Overall pass threshold (70% of expected outputs must be found)
        overall_pass = pass_rate >= 0.7

        # Additional quality checks
        quality_checks = self._perform_quality_checks(scenario, plan_response)

        return {
            "expected_output_checks": checks,
            "passed_checks": passed_checks,
            "total_checks": total_checks,
            "pass_rate": pass_rate,
            "quality_checks": quality_checks,
            "overall_pass": overall_pass and quality_checks["overall_quality_pass"],
        }

    def _perform_quality_checks(
        self, scenario: Dict[str, Any], plan_response
    ) -> Dict[str, Any]:
        """Perform additional quality checks on the response"""
        input_data = scenario.get("input", {})
        itinerary = plan_response.itinerary

        checks = {
            "has_itinerary": len(itinerary.days) > 0,
            "correct_duration": True,  # Default to true
            "has_budget_info": itinerary.total_cost_usd is not None,
            "has_activities": False,
            "response_not_empty": len(plan_response.answer_markdown.strip()) > 0,
        }

        # Check duration matches request
        if "duration" in input_data and len(itinerary.days) > 0:
            expected_days = input_data["duration"]
            actual_days = len(itinerary.days)
            # Allow some flexibility (±1 day)
            checks["correct_duration"] = abs(actual_days - expected_days) <= 1

        # Check if there are activities
        total_activities = sum(len(day.activities) for day in itinerary.days)
        checks["has_activities"] = total_activities > 0

        # Check budget adherence if budget was specified
        if "budget" in input_data and itinerary.total_cost_usd:
            budget = input_data["budget"]
            actual_cost = itinerary.total_cost_usd
            # Allow 20% over budget
            checks["within_budget"] = actual_cost <= budget * 1.2
        else:
            checks["within_budget"] = True  # No budget constraint

        # Overall quality pass (most checks should pass)
        quality_score = sum(1 for check in checks.values() if check)
        total_quality_checks = len(checks)
        quality_pass_rate = quality_score / total_quality_checks

        return {
            "checks": checks,
            "quality_score": quality_score,
            "total_quality_checks": total_quality_checks,
            "quality_pass_rate": quality_pass_rate,
            "overall_quality_pass": quality_pass_rate >= 0.8,
        }

    async def run_all_scenarios(self) -> List[Dict[str, Any]]:
        """Run all evaluation scenarios"""
        if not self.scenarios:
            self.load_scenarios()

        results = []

        for i, scenario in enumerate(self.scenarios, 1):
            print(f"\n=== Running scenario {i}/{len(self.scenarios)} ===")
            result = await self.run_scenario(scenario)
            results.append(result)

            # Print immediate result
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            print(f"Result: {status}")

            if result["status"] == "failed":
                print(f"Error: {result.get('error', 'Unknown error')}")

        return results

    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate evaluation report"""
        if not results:
            return "No results to report."

        # Calculate summary statistics
        total_scenarios = len(results)
        passed_scenarios = sum(1 for r in results if r["passed"])
        failed_scenarios = total_scenarios - passed_scenarios
        pass_rate = (passed_scenarios / total_scenarios) * 100

        # Generate report
        report_lines = [
            "=" * 60,
            "ATLAS TRAVEL ADVISOR - EVALUATION REPORT",
            "=" * 60,
            f"Total Scenarios: {total_scenarios}",
            f"Passed: {passed_scenarios} ({pass_rate:.1f}%)",
            f"Failed: {failed_scenarios}",
            "",
            "SCENARIO RESULTS:",
            "-" * 40,
        ]

        # Add individual scenario results
        for result in results:
            scenario_name = result["scenario_name"]
            status = "PASS" if result["passed"] else "FAIL"

            report_lines.append(f"{scenario_name}: {status}")

            if result["status"] == "failed":
                report_lines.append(f"  Error: {result.get('error', 'Unknown error')}")
            elif "evaluation" in result:
                eval_data = result["evaluation"]
                passed_checks = eval_data.get("passed_checks", 0)
                total_checks = eval_data.get("total_checks", 0)
                if total_checks > 0:
                    check_rate = (passed_checks / total_checks) * 100
                    report_lines.append(
                        f"  Expected outputs: {passed_checks}/{total_checks} ({check_rate:.1f}%)"
                    )

                quality_data = eval_data.get("quality_checks", {})
                quality_score = quality_data.get("quality_score", 0)
                total_quality = quality_data.get("total_quality_checks", 0)
                if total_quality > 0:
                    quality_rate = (quality_score / total_quality) * 100
                    report_lines.append(
                        f"  Quality checks: {quality_score}/{total_quality} ({quality_rate:.1f}%)"
                    )

            report_lines.append("")

        # Add detailed failure analysis
        failed_results = [r for r in results if not r["passed"]]
        if failed_results:
            report_lines.extend(["FAILURE ANALYSIS:", "-" * 40])

            for result in failed_results:
                report_lines.append(f"\n{result['scenario_name']}:")

                if result["status"] == "failed":
                    report_lines.append(
                        f"  System Error: {result.get('error', 'Unknown')}"
                    )
                elif "evaluation" in result:
                    eval_data = result["evaluation"]

                    # Show failed expected output checks
                    for check in eval_data.get("expected_output_checks", []):
                        if not check["found"]:
                            report_lines.append(f"  ❌ Missing: {check['expected']}")

                    # Show failed quality checks
                    quality_checks = eval_data.get("quality_checks", {}).get(
                        "checks", {}
                    )
                    for check_name, passed in quality_checks.items():
                        if not passed:
                            report_lines.append(f"  ❌ Quality issue: {check_name}")

        report_lines.extend(
            [
                "",
                "=" * 60,
                f"OVERALL RESULT: {'PASS' if pass_rate >= 70 else 'FAIL'} ({pass_rate:.1f}%)",
                "=" * 60,
            ]
        )

        return "\n".join(report_lines)


async def main():
    """Main evaluation runner"""
    # Set up environment variables if needed
    if not os.getenv("DATABASE_URL"):
        print("Warning: DATABASE_URL not set. Using default SQLite database.")
        os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    elif "db:5432" in os.getenv("DATABASE_URL", ""):
        print("Detected Docker DATABASE_URL. Switching to SQLite for local testing.")
        os.environ["DATABASE_URL"] = "sqlite:///./test.db"

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is required.")
        sys.exit(1)

    runner = ScenarioRunner()

    print("Loading evaluation scenarios...")
    try:
        scenarios = runner.load_scenarios()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Running {len(scenarios)} scenarios...")
    results = await runner.run_all_scenarios()

    print("\nGenerating evaluation report...")
    report = runner.generate_report(results)

    print("\nEvaluation complete!")
    print(report)

    # Save report to file
    report_file = Path(__file__).parent / "evaluation_report.txt"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())
