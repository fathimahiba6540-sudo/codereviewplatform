import unittest
from types import SimpleNamespace
from backend.app.services.comparison_service import ComparisonService
from backend.app.services.repo_parser import EXTENSION_LANGUAGE_MAP


class TestPhase12Enhancements(unittest.TestCase):

    def test_expanded_language_support(self):
        self.assertEqual(EXTENSION_LANGUAGE_MAP.get(".kt"), "Kotlin")
        self.assertEqual(EXTENSION_LANGUAGE_MAP.get(".swift"), "Swift")
        self.assertEqual(EXTENSION_LANGUAGE_MAP.get(".rs"), "Rust")
        self.assertEqual(EXTENSION_LANGUAGE_MAP.get(".go"), "Go")

    def test_comparison_service_score_deltas(self):
        review_base = SimpleNamespace(
            id="rev-1",
            project_id="proj-100",
            overall_score=75.0,
            security_score=80.0,
            maintainability_score=70.0,
            report_json={
                "scores": {
                    "overall_score": 75.0,
                    "security_score": 80.0,
                    "maintainability_score": 70.0,
                },
                "findings": {
                    "bugs": [{"id": 1}],
                    "security": [{"id": 101}]
                }
            }
        )

        review_target = SimpleNamespace(
            id="rev-2",
            project_id="proj-100",
            overall_score=90.0,
            security_score=95.0,
            maintainability_score=85.0,
            report_json={
                "scores": {
                    "overall_score": 90.0,
                    "security_score": 95.0,
                    "maintainability_score": 85.0,
                },
                "findings": {
                    "bugs": [],
                    "security": []
                }
            }
        )

        diff = ComparisonService.compare_reviews(review_base, review_target)
        self.assertEqual(diff["scores_comparison"]["overall_delta"], 15.0)
        self.assertEqual(diff["status"], "IMPROVED")
        self.assertEqual(diff["findings_summary_diff"]["bugs_diff"], -1)


if __name__ == "__main__":
    unittest.main()
