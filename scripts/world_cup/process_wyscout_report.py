#!/usr/bin/env python3
"""Process a Wyscout match report PDF into validated CSV outputs."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from football_analytics.processors import WyscoutReportProcessor
from football_analytics.utils import setup_logging
from football_analytics.utils.logging_utils import get_logger


setup_logging()
logger = get_logger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse a Wyscout match report PDF into normalized CSV files"
    )
    parser.add_argument("--pdf", required=True, help="Path to the Wyscout report PDF")
    parser.add_argument(
        "--output-dir",
        default="data/processed/wyscout",
        help="Directory where parsed report outputs will be written",
    )
    parser.add_argument(
        "--match-id",
        default=None,
        help="Optional stable match id; inferred from date/team names by default",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Return a non-zero exit code unless the parse is publication-ready",
    )
    parser.add_argument(
        "--fail-on-critical",
        action="store_true",
        help=(
            "Return a non-zero exit code unless critical match-story metrics "
            "(shots/goals/xG/PsxG/on-target) are ready"
        ),
    )
    parser.add_argument(
        "--summary-json",
        action="store_true",
        help="Write a compact machine-readable validation summary to stdout",
    )
    args = parser.parse_args()

    processor = WyscoutReportProcessor()
    result = processor.parse_pdf(args.pdf, match_id=args.match_id)
    out_dir = processor.save_result(result, args.output_dir)

    report = result.validation_report
    logger.info("Output directory: %s", out_dir)
    logger.info("Validation status: %s", report["status"])
    logger.info("Quality score: %s/100", report["quality_score"])
    logger.info("Analysis ready: %s", report["analysis_ready"])
    logger.info("Publication ready: %s", report["publication_ready"])
    logger.info("Critical metrics ready: %s", report["critical_metrics_ready"])
    logger.info("Quarantined tables: %s", report["quarantined_tables"] or "none")
    if report.get("critical_findings"):
        logger.info(
            "Critical findings: %s",
            [issue["check_id"] for issue in report["critical_findings"]],
        )

    if report["issues"]:
        logger.info("Validation issues:")
        for issue in report["issues"]:
            logger.info(
                "  [%s] %s: %s",
                issue["severity"].upper(),
                issue["check_id"],
                issue["message"],
            )

    if args.summary_json:
        summary = {
            "schema_version": report["schema_version"],
            "match_id": report["match_id"],
            "status": report["status"],
            "quality_score": report["quality_score"],
            "analysis_ready": report["analysis_ready"],
            "publication_ready": report["publication_ready"],
            "critical_metrics_ready": report["critical_metrics_ready"],
            "critical_findings_count": len(report["critical_findings"]),
            "critical_finding_check_ids": [
                issue["check_id"] for issue in report["critical_findings"]
            ],
            "critical_tables": report["critical_tables"],
            "quarantined_tables": report["quarantined_tables"],
            "severity_counts": report["severity_counts"],
            "output_dir": str(out_dir),
        }
        print(json.dumps(summary, ensure_ascii=False))

    if report["status"] == "FAIL":
        return 1
    if args.fail_on_warnings and not report["publication_ready"]:
        return 1
    if args.fail_on_critical and not report["critical_metrics_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
