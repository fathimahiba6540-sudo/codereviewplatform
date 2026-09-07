from typing import Dict, Any, List


class ComparisonService:
    """Service to compare review reports, calculate score deltas, and compute findings diffs."""

    @classmethod
    def compare_reviews(cls, review_base: Review, review_target: Review) -> Dict[str, Any]:
        """Compare two review records and calculate score changes and findings diff."""

        report_base = review_base.report_json or {}
        report_target = review_target.report_json or {}

        scores_base = report_base.get("scores", {})
        scores_target = report_target.get("scores", {})

        overall_base = scores_base.get("overall_score", 0.0)
        overall_target = scores_target.get("overall_score", 0.0)
        delta_overall = round(overall_target - overall_base, 2)

        security_base = scores_base.get("security_score", 0.0)
        security_target = scores_target.get("security_score", 0.0)
        delta_security = round(security_target - security_base, 2)

        maintainability_base = scores_base.get("maintainability_score", 0.0)
        maintainability_target = scores_target.get("maintainability_score", 0.0)
        delta_maintainability = round(maintainability_target - maintainability_base, 2)

        # Categorized findings diff
        findings_base = report_base.get("findings", {})
        findings_target = report_target.get("findings", {})

        bugs_base = len(findings_base.get("bugs", []))
        bugs_target = len(findings_target.get("bugs", []))
        delta_bugs = bugs_target - bugs_base

        sec_base = len(findings_base.get("security", []))
        sec_target = len(findings_target.get("security", []))
        delta_sec = sec_target - sec_base

        return {
            "base_review_id": review_base.id,
            "target_review_id": review_target.id,
            "project_id": review_base.project_id,
            "scores_comparison": {
                "base_overall_score": overall_base,
                "target_overall_score": overall_target,
                "overall_delta": delta_overall,
                "security_delta": delta_security,
                "maintainability_delta": delta_maintainability,
            },
            "findings_summary_diff": {
                "bugs_diff": delta_bugs,
                "security_vulnerabilities_diff": delta_sec,
                "base_total_bugs": bugs_base,
                "target_total_bugs": bugs_target,
                "base_total_security": sec_base,
                "target_total_security": sec_target,
            },
            "status": "IMPROVED" if delta_overall > 0 else ("DEGRADED" if delta_overall < 0 else "UNCHANGED")
        }
