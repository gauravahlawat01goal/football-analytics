"""Wyscout match report PDF processing.

This module turns Wyscout match-report PDFs into normalized dataframes plus a
validation report. The parser is intentionally conservative: raw values and page
evidence are retained, and reconciliation checks flag mismatches between report
sections instead of silently trusting one extraction path.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ..utils.logging_utils import get_logger


SECTION_BY_COMPACT_TITLE = {
    "MATCHSHEET": "match_sheet",
    "POSITIONS": "positions",
    "MATCHDYNAMICS": "match_dynamics",
    "TEAMSTATS": "team_stats",
    "PLAYERSTATS": "player_stats",
    "GOALKEEPERINMATCH": "goalkeeper",
    "SHOTS": "shots",
    "PASSES": "passes",
    "DUELS": "duels",
    "LOSSES": "losses",
    "RECOVERIES": "recoveries",
    "DRIBBLES": "dribbles",
    "KEYPASSES": "key_passes",
    "CROSSES": "crosses",
    "FOULS": "fouls",
    "GROUNDDUELS": "ground_duels",
    "AERIALDUELS": "aerial_duels",
    "GLOSSARY": "glossary",
}

EXPECTED_SECTIONS = {
    "match_sheet",
    "positions",
    "match_dynamics",
    "team_stats",
    "player_stats",
    "goalkeeper",
    "shots",
    "passes",
    "duels",
    "losses",
    "recoveries",
    "dribbles",
    "key_passes",
    "crosses",
    "fouls",
    "ground_duels",
    "aerial_duels",
    "glossary",
}

NORMALIZED_SECTIONS = {
    "match_sheet",
    "team_stats",
    "player_stats",
    "shots",
}

NORMALIZED_TABLES = {
    "match_summary",
    "team_stats",
    "player_stats",
    "shots",
    "shot_totals",
}

# Bumped to 2 when the table-level readiness/criticality layer was added.
SCHEMA_VERSION = 2

# Tables whose correctness underpins the match story (shots, goals, xG, PsxG,
# on-target). ``critical_metrics_ready`` is governed solely by these.
CRITICAL_TABLES = ["team_stats", "player_stats", "shots", "shot_totals"]

# Empty normalized tables that destroy credibility-critical numbers.
CRITICAL_EMPTY_TABLES = {"team_stats", "player_stats", "shots", "shot_totals"}

# Team-stat metrics whose mis-attribution corrupts goals / xG / shots / on-target.
CRITICAL_TEAM_METRICS = {
    "Goals",
    "xG",
    "Shots / on target",
    "Shots on post / blocked / wide",
    "From penalty area / on target",
    "Outside penalty area / on target",
}

# parse_status values that mean a row yielded no usable structured data.
HARD_FAILURE_STATUSES = {"failed", "failed_missing_values"}

# Single source of truth for which normalized table an issue scopes to and
# whether it is a credibility-critical match-story check. Issues not listed here
# keep the ValidationIssue defaults (table=None, criticality="standard"). The
# check_ids ``table_not_empty`` and ``team_stat_rows_attributed`` are classified
# dynamically from their details (see ``_classify_issues``).
ISSUE_POLICY: dict[str, tuple[str | None, str]] = {
    # Shots table: every shot / xG / PsxG / on-target reconciliation is critical.
    "shot_rows_parse_cleanly": ("shots", "critical"),
    "shot_page_total_matches_team_shots": ("shots", "critical"),
    "shot_page_on_goal_matches_team_on_target": ("shots", "critical"),
    "shot_page_goals_match_team_goals": ("shots", "critical"),
    "shot_page_xg_matches_team_xg": ("shots", "critical"),
    "shot_rows_match_shot_page_total": ("shots", "critical"),
    "shot_rows_xg_sum_to_shot_page_xg": ("shots", "critical"),
    "shot_rows_psxg_sum_to_shot_page_psxg": ("shots", "critical"),
    "shot_page_result_buckets_sum_to_total": ("shots", "critical"),
    "shot_page_blocked_matches_team_blocked": ("shots", "critical"),
    "shot_page_wide_matches_team_wide": ("shots", "critical"),
    "shot_numbers_unique": ("shots", "critical"),
    "shot_numbers_monotonic": ("shots", "critical"),
    "shot_numbers_complete": ("shots", "critical"),
    "shot_type_allowed": ("shots", "critical"),
    "shot_player_matches_known_players": ("shots", "critical"),
    "critical_shot_total_field_present": ("shot_totals", "critical"),
    # Player reconciliation that drives goals / xG / on-target claims.
    "critical_player_metric_present": ("player_stats", "critical"),
    "player_goals_sum_to_team_goals": ("player_stats", "critical"),
    "player_xg_sums_to_team_xg": ("player_stats", "critical"),
    "player_shots_sum_to_team_shots": ("player_stats", "critical"),
    "player_table_rows_parse_cleanly": ("player_stats", "standard"),
    # Team-stat reconciliation / attribution.
    "critical_team_metric_present": ("team_stats", "critical"),
    "score_matches_team_goals": ("team_stats", "critical"),
    "possession_sums_to_100": ("team_stats", "standard"),
    "fouls_suffered_are_symmetric": ("team_stats", "standard"),
    # Structural (not scoped to a single normalized table).
    "sections_present": (None, "standard"),
}

TEAM_STAT_CATEGORIES = {
    "Goals": "general",
    "xG": "general",
    "Shots / on target": "general",
    "Shots on post / blocked / wide": "general",
    "From penalty area / on target": "general",
    "Outside penalty area / on target": "general",
    "Average shot distance (m)": "general",
    "Corners": "general",
    "Free kicks": "general",
    "Offsides": "general",
    "Fouls / suffered": "general",
    "Yellow / red cards": "general",
    "Total / with shots": "attacks",
    "Positional attacks / with shots": "attacks",
    "Counterattacks": "attacks",
    "Free kicks / with shots": "attacks",
    "Corners / with shots": "attacks",
    "Sliding tackles": "defence",
    "Interceptions": "defence",
    "Clearances": "defence",
    "Passes allowed per def. action (PPDA)": "defence",
    "Recoveries / low / medium / high": "transitions",
    "Opponent half recoveries": "transitions",
    "Losses / low / medium / high": "transitions",
    "Total duels / won": "duels",
    "Offensive duels / won": "duels",
    "Defensive duels / won": "duels",
    "Loose ball duels / won": "duels",
    "Aerial duels / won": "duels",
    "Challenge intensity": "duels",
    "Dribbles / successful": "duels",
    "Possession %": "possession",
    "Pure possession time": "possession",
    "Number of possessions": "possession",
    "Possessions reaching opponent half": "possession",
    "Possessions reaching opponent penalty area": "possession",
    "Average possession duration": "possession",
    "Dead time": "possession",
    "Short (0-10 sec)": "open_play_possessions",
    "Medium (10-20 sec)": "open_play_possessions",
    "Long (20-45 sec)": "open_play_possessions",
    "Very long (45+ sec)": "open_play_possessions",
    "Total passes / accurate": "passes",
    "Forward passes / accurate": "passes",
    "Back passes / accurate": "passes",
    "Lateral passes / accurate": "passes",
    "Progressive passes / accurate": "passes",
    "Long passes / accurate": "passes",
    "Passes to final third / accurate": "passes",
    "Average pass to final third length (m)": "passes",
    "Passes to penalty area / accurate": "passes",
    "Smart passes / accurate": "passes",
    "Shot assists": "passes",
    "Through passes / accurate": "passes",
    "Crosses / accurate": "passes",
    "Crosses: low / high / blocked": "passes",
    "Deep completions": "passes",
    "Match tempo": "passes",
    "Average pass length (m)": "passes",
}

TEAM_STAT_METRICS = sorted(TEAM_STAT_CATEGORIES, key=len, reverse=True)
GLOBAL_TEAM_STAT_METRICS = {"Dead time"}

ALLOWED_SHOT_TYPES = {
    "Left foot",
    "Right foot",
    "Head",
    "Other",
    "Left foot, after corner",
    "Right foot, after corner",
    "Head, after corner",
}

PLAYER_SUMMARY_SPECS = [
    ("goals_xg", False),
    ("assists_xa", False),
    ("actions_successful", True),
    ("shots_on_target", True),
    ("passes_accurate", True),
    ("crosses_accurate", True),
    ("dribbles_successful", True),
    ("duels_won", True),
    ("losses_own_half", False),
    ("recoveries_opponent_half", False),
    ("touches_in_penalty_area", False),
    ("offsides", False),
    ("yellow_red_cards", False),
]

PLAYER_PASSING_SPECS = [
    ("forward_passes_accurate", True),
    ("back_passes_accurate", True),
    ("lateral_passes_accurate", True),
    ("short_medium_passes_accurate", True),
    ("long_passes_accurate", True),
    ("progressive_passes_accurate", True),
    ("passes_to_final_third_accurate", True),
    ("through_passes_accurate", True),
    ("deep_completions", False),
    ("key_passes", False),
    ("second_third_assists", False),
    ("shot_assists", False),
    ("average_pass_length", False),
]


@dataclass
class PageText:
    """Extracted text for one PDF page."""

    page_number: int
    section: str
    default_text: str
    layout_text: str


@dataclass
class ValidationIssue:
    """One parser validation issue.

    ``table`` scopes the issue to a normalized table so downstream consumers can
    reason about per-table readiness. ``criticality`` marks credibility-critical
    match-story checks (shots, goals, xG, PsxG, on-target) as ``"critical"`` so
    they surface as first-class findings rather than being buried in generic
    warnings. ``affects_publication`` is retained for forward compatibility; the
    strict publication gate still treats every warning as blocking.

    The four leading fields and their JSON keys are unchanged; the new fields are
    additive with defaults so existing call sites keep working.
    """

    check_id: str
    severity: str
    message: str
    details: dict[str, Any]
    table: str | None = None
    criticality: str = "standard"
    affects_publication: bool = True


@dataclass
class WyscoutReportResult:
    """Parsed Wyscout report result."""

    match_id: str
    metadata: dict[str, Any]
    pages: list[PageText]
    dataframes: dict[str, pd.DataFrame]
    validation_report: dict[str, Any]


class WyscoutReportProcessor:
    """Parse and validate Wyscout match report PDFs."""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def parse_pdf(self, pdf_path: str | Path, match_id: str | None = None) -> WyscoutReportResult:
        """Parse a Wyscout report PDF into normalized dataframes and validations."""
        pdf_path = Path(pdf_path)
        pages, pdf_metadata = self._extract_pages(pdf_path)
        metadata = self._parse_match_metadata(pages, pdf_metadata, pdf_path)
        metadata["source_pdf"] = str(pdf_path)
        metadata["source_sha256"] = self._sha256(pdf_path)

        inferred_match_id = match_id or self._make_match_id(metadata, pdf_path)
        metadata["match_id"] = inferred_match_id
        metadata["normalized_tables"] = sorted(NORMALIZED_TABLES)
        metadata["normalized_sections"] = sorted(NORMALIZED_SECTIONS)
        metadata["non_normalized_sections"] = sorted(EXPECTED_SECTIONS - NORMALIZED_SECTIONS)

        team_stats = self._parse_team_stats(pages, metadata)
        player_stats = self._parse_player_stats(pages, metadata)
        shots, shot_totals = self._parse_shots(pages, metadata, player_stats)
        match_summary = pd.DataFrame([metadata])

        dataframes = {
            "match_summary": match_summary,
            "team_stats": team_stats,
            "player_stats": player_stats,
            "shots": shots,
            "shot_totals": shot_totals,
        }
        validation_report = self._validate(metadata, pages, dataframes)

        return WyscoutReportResult(
            match_id=inferred_match_id,
            metadata=metadata,
            pages=pages,
            dataframes=dataframes,
            validation_report=validation_report,
        )

    def save_result(self, result: WyscoutReportResult, output_dir: str | Path) -> Path:
        """Save parsed dataframes, raw page evidence, and validation report."""
        out_dir = Path(output_dir) / result.match_id
        out_dir.mkdir(parents=True, exist_ok=True)

        for name, df in result.dataframes.items():
            df.to_csv(out_dir / f"{name}.csv", index=False, encoding="utf-8")

        raw_pages = [asdict(page) for page in result.pages]
        (out_dir / "raw_pages.json").write_text(
            json.dumps(raw_pages, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (out_dir / "validation_report.json").write_text(
            json.dumps(result.validation_report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (out_dir / "metadata.json").write_text(
            json.dumps(result.metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        self.logger.info("Saved Wyscout report outputs to %s", out_dir)
        return out_dir

    def _extract_pages(self, pdf_path: Path) -> tuple[list[PageText], dict[str, Any]]:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf is required to parse Wyscout PDFs") from exc

        reader = PdfReader(str(pdf_path))
        pdf_metadata = {
            str(key).lstrip("/"): str(value)
            for key, value in (reader.metadata or {}).items()
        }
        pdf_metadata["page_count"] = len(reader.pages)

        pages = []
        for index, page in enumerate(reader.pages, start=1):
            default_text = page.extract_text() or ""
            try:
                layout_text = page.extract_text(extraction_mode="layout") or ""
            except Exception as exc:  # pragma: no cover - depends on PDF internals
                self.logger.warning("Layout extraction failed on page %s: %s", index, exc)
                layout_text = ""

            pages.append(
                PageText(
                    page_number=index,
                    section=self._detect_section(default_text, layout_text, index),
                    default_text=default_text,
                    layout_text=layout_text,
                )
            )

        return pages, pdf_metadata

    def _parse_match_metadata(
        self,
        pages: list[PageText],
        pdf_metadata: dict[str, Any],
        pdf_path: Path,
    ) -> dict[str, Any]:
        page_one = pages[0].default_text if pages else ""
        lines = self._lines(page_one)

        home_team = away_team = None
        home_score = away_score = None
        match_date = competition = None

        score_idx = None
        score_pattern = re.compile(r"^(\d+)\s*[–-]\s*(\d+)$")
        for idx, line in enumerate(lines):
            match = score_pattern.match(line)
            if match:
                score_idx = idx
                home_score = int(match.group(1))
                away_score = int(match.group(2))
                break

        if score_idx is not None and score_idx >= 2:
            home_team = lines[score_idx - 2]
            away_team = lines[score_idx - 1]
            if score_idx + 1 < len(lines):
                date_competition = lines[score_idx + 1]
                date_match = re.match(r"(\d{2}/\d{2}/\d{4})\s+(.*)", date_competition)
                if date_match:
                    match_date = self._iso_date(date_match.group(1))
                    competition = date_match.group(2)

        if not home_team or not away_team:
            fallback = self._parse_header_score(pages)
            home_team = home_team or fallback.get("home_team")
            away_team = away_team or fallback.get("away_team")
            home_score = home_score if home_score is not None else fallback.get("home_score")
            away_score = away_score if away_score is not None else fallback.get("away_score")

        return {
            "source": "wyscout_report_pdf",
            "pdf_title": pdf_metadata.get("Title"),
            "pdf_producer": pdf_metadata.get("Producer"),
            "page_count": pdf_metadata.get("page_count"),
            "file_name": pdf_path.name,
            "parsed_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "competition": competition,
            "match_date": match_date,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
        }

    def _parse_header_score(self, pages: list[PageText]) -> dict[str, Any]:
        header_pattern = re.compile(r"(.+?)\s+(\d+)\s*[–-]\s*(\d+)\s+(.+?)\s*(?:\(|$)")
        for page in pages:
            for line in self._lines(page.default_text):
                match = header_pattern.match(line)
                if match:
                    return {
                        "home_team": match.group(1).strip(),
                        "home_score": int(match.group(2)),
                        "away_score": int(match.group(3)),
                        "away_team": match.group(4).strip(),
                    }
        return {}

    def _parse_team_stats(self, pages: list[PageText], metadata: dict[str, Any]) -> pd.DataFrame:
        page = self._first_page_for_section(pages, "team_stats")
        if page is None:
            return pd.DataFrame()

        rows: list[dict[str, Any]] = []
        home_team = metadata.get("home_team")
        away_team = metadata.get("away_team")

        for line in self._lines(page.default_text):
            for metric in TEAM_STAT_METRICS:
                if line == metric or not line.startswith(f"{metric} "):
                    continue

                rest = line[len(metric) :].strip()
                values = self._split_team_values(metric, rest)
                category = TEAM_STAT_CATEGORIES[metric]

                if metric in GLOBAL_TEAM_STAT_METRICS and len(values) == 1:
                    rows.append(
                        self._value_row(
                            metadata,
                            source_page=page.page_number,
                            table_name="team_stats",
                            category=category,
                            metric=metric,
                            team=None,
                            opponent=None,
                            raw_value=values[0],
                        )
                    )
                    break

                if len(values) == 2:
                    rows.append(
                        self._value_row(
                            metadata,
                            source_page=page.page_number,
                            table_name="team_stats",
                            category=category,
                            metric=metric,
                            team=home_team,
                            opponent=away_team,
                            raw_value=values[0],
                        )
                    )
                    rows.append(
                        self._value_row(
                            metadata,
                            source_page=page.page_number,
                            table_name="team_stats",
                            category=category,
                            metric=metric,
                            team=away_team,
                            opponent=home_team,
                            raw_value=values[1],
                        )
                    )
                    break

                rows.append(
                    self._value_row(
                        metadata,
                        source_page=page.page_number,
                        table_name="team_stats",
                        category=category,
                        metric=metric,
                        team=None,
                        opponent=None,
                        raw_value=rest,
                        parse_status="failed",
                    )
                )
                break

        return pd.DataFrame(rows)

    def _parse_player_stats(
        self,
        pages: list[PageText],
        metadata: dict[str, Any],
    ) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []
        player_pages = [page for page in pages if page.section == "player_stats"]

        for page in player_pages:
            lines = self._lines(page.default_text)
            team = self._detect_page_team(lines, metadata)
            if not team:
                self.logger.warning("Could not detect player-stats team on page %s", page.page_number)
                continue

            group = self._detect_player_stat_group(lines)
            specs = PLAYER_PASSING_SPECS if group == "passing" else PLAYER_SUMMARY_SPECS

            for line in self._player_table_lines(lines):
                parsed = self._parse_player_table_line(line, specs)
                if not parsed:
                    continue
                base = {
                    "match_id": metadata.get("match_id"),
                    "source": metadata.get("source"),
                    "source_page": page.page_number,
                    "team": team,
                    "opponent": self._opponent(team, metadata),
                    "player_number": parsed["player_number"],
                    "player_name": parsed["player_name"],
                    "minutes_played": parsed["minutes_played"],
                    "stat_group": group,
                    "parse_status": parsed["parse_status"],
                    "raw_line": line,
                    "unparsed_tail": parsed["unparsed_tail"],
                    "expected_metric_count": parsed["expected_metric_count"],
                    "parsed_metric_count": parsed["parsed_metric_count"],
                }
                for metric, raw_value in parsed["values"].items():
                    value_fields = self._parse_value(raw_value)
                    rows.append(
                        {
                            **base,
                            "metric": metric,
                            "raw_value": raw_value,
                            **value_fields,
                        }
                    )

        return pd.DataFrame(rows)

    def _parse_shots(
        self,
        pages: list[PageText],
        metadata: dict[str, Any],
        player_stats: pd.DataFrame | None = None,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        shot_rows: list[dict[str, Any]] = []
        total_rows: list[dict[str, Any]] = []
        known_players = self._known_players_by_team(player_stats) if player_stats is not None else {}

        for page in [page for page in pages if page.section == "shots"]:
            lines = self._lines(page.default_text)
            team = self._detect_page_team(lines, metadata)
            if not team:
                continue

            shot_total = self._parse_shot_total(lines)
            if shot_total:
                total_rows.append(
                    {
                        "match_id": metadata.get("match_id"),
                        "source_page": page.page_number,
                        "team": team,
                        "opponent": self._opponent(team, metadata),
                        **shot_total,
                    }
                )

            for expected_shot_number, raw_line in enumerate(self._shot_table_lines(lines), start=1):
                cleaned = self._clean_repeated_fragments(raw_line)
                parsed = self._parse_shot_line(
                    cleaned,
                    expected_shot_number=expected_shot_number,
                    known_players=known_players.get(str(team)),
                )
                base = {
                    "match_id": metadata.get("match_id"),
                    "source_page": page.page_number,
                    "team": team,
                    "opponent": self._opponent(team, metadata),
                    "raw_line": raw_line,
                    "cleaned_line": cleaned,
                }
                if parsed:
                    shot_rows.append({**base, **parsed, "parse_status": "parsed"})
                else:
                    shot_rows.append(
                        {
                            **base,
                            "shot_number": None,
                            "player_number": None,
                            "player_name": None,
                            "minute": None,
                            "shot_type": None,
                            "xg": None,
                            "psxg": None,
                            "parse_status": "failed",
                        }
                    )

        return pd.DataFrame(shot_rows), pd.DataFrame(total_rows)

    def _validate(
        self,
        metadata: dict[str, Any],
        pages: list[PageText],
        dataframes: dict[str, pd.DataFrame],
    ) -> dict[str, Any]:
        issues: list[ValidationIssue] = []
        sections_found = {page.section for page in pages}
        missing_sections = sorted(EXPECTED_SECTIONS - sections_found)
        if missing_sections:
            issues.append(
                ValidationIssue(
                    "sections_present",
                    "warning",
                    "Expected report sections were not detected.",
                    {"missing_sections": missing_sections},
                )
            )

        team_stats = dataframes["team_stats"]
        player_stats = dataframes["player_stats"]
        shot_totals = dataframes["shot_totals"]
        shots = dataframes["shots"]

        for table_name, severity in [
            ("team_stats", "error"),
            ("player_stats", "error"),
            ("shots", "warning"),
            ("shot_totals", "warning"),
        ]:
            if dataframes[table_name].empty:
                issues.append(
                    ValidationIssue(
                        "table_not_empty",
                        severity,
                        "Expected parsed table is empty.",
                        {"table": table_name},
                    )
                )

        self._validate_critical_metric_presence(metadata, pages, team_stats, player_stats, shot_totals, issues)
        self._validate_score_vs_goals(metadata, team_stats, issues)
        self._validate_player_xg_and_goals(metadata, team_stats, player_stats, issues)
        self._validate_player_shots(metadata, team_stats, player_stats, issues)
        self._validate_player_parse_status(player_stats, issues)
        self._validate_shot_parse_status(shots, issues)
        self._validate_shot_page_totals(team_stats, shot_totals, shots, issues)
        self._validate_shot_aggregates(team_stats, shot_totals, shots, issues)
        self._validate_shot_rows(shot_totals, shots, player_stats, issues)
        self._validate_team_stat_attribution(metadata, team_stats, issues)
        self._validate_possession_and_symmetry(team_stats, issues)

        self._classify_issues(issues)

        severity_counts = {
            "error": sum(issue.severity == "error" for issue in issues),
            "warning": sum(issue.severity == "warning" for issue in issues),
        }
        analysis_ready = severity_counts["error"] == 0
        publication_ready = analysis_ready and severity_counts["warning"] == 0
        quality_score = max(0, 100 - severity_counts["error"] * 25 - severity_counts["warning"] * 5)
        if severity_counts["error"]:
            status = "FAIL"
        elif severity_counts["warning"]:
            status = "PASS_WITH_WARNINGS"
        else:
            status = "PASS"

        table_readiness = self._build_table_readiness(dataframes, issues)
        metric_readiness = self._build_metric_readiness(dataframes, issues)
        quarantined_tables = sorted(
            name
            for name, entry in table_readiness.items()
            if entry["readiness"] != "publication"
        )
        critical_findings = [
            self._json_safe(asdict(issue)) for issue in issues if issue.criticality == "critical"
        ]
        critical_metrics_ready = self._critical_metrics_ready(table_readiness, issues)

        return {
            "schema_version": SCHEMA_VERSION,
            "match_id": metadata.get("match_id"),
            "status": status,
            "quality_score": quality_score,
            "severity_counts": severity_counts,
            "analysis_ready": analysis_ready,
            "publication_ready": publication_ready,
            "critical_metrics_ready": critical_metrics_ready,
            "critical_tables": list(CRITICAL_TABLES),
            "quarantined_tables": quarantined_tables,
            "table_readiness": table_readiness,
            "metric_readiness": metric_readiness,
            "critical_findings": critical_findings,
            "sections_found": sorted(sections_found),
            "normalized_tables": sorted(NORMALIZED_TABLES),
            "normalized_sections": sorted(NORMALIZED_SECTIONS),
            "detected_but_not_normalized_sections": sorted(
                (sections_found & EXPECTED_SECTIONS) - NORMALIZED_SECTIONS
            ),
            "issues": [self._json_safe(asdict(issue)) for issue in issues],
        }

    def _validate_critical_metric_presence(
        self,
        metadata: dict[str, Any],
        pages: list[PageText],
        team_stats: pd.DataFrame,
        player_stats: pd.DataFrame,
        shot_totals: pd.DataFrame,
        issues: list[ValidationIssue],
    ) -> None:
        teams = [team for team in [metadata.get("home_team"), metadata.get("away_team")] if team]

        if self._has_columns(team_stats, "team", "metric"):
            for team in teams:
                for metric in ["Goals", "xG", "Shots / on target"]:
                    rows = team_stats[
                        (team_stats["team"] == team) & (team_stats["metric"] == metric)
                    ]
                    if rows.empty or not self._critical_team_metric_is_usable(rows.iloc[0], metric):
                        issues.append(
                            ValidationIssue(
                                "critical_team_metric_present",
                                "warning",
                                "Critical team metric was missing or not usable for a team.",
                                {
                                    "team": team,
                                    "metric": metric,
                                    "reason": "missing_row"
                                    if rows.empty
                                    else "missing_or_unusable_value",
                                    "raw_value": (
                                        None if rows.empty else rows.iloc[0].get("raw_value")
                                    ),
                                },
                            )
                        )

        if self._has_columns(player_stats, "team", "stat_group", "metric"):
            for team in teams:
                for metric in ["goals_xg", "shots_on_target"]:
                    rows = player_stats[
                        (player_stats["team"] == team)
                        & (player_stats["stat_group"] == "summary")
                        & (player_stats["metric"] == metric)
                    ]
                    if rows.empty:
                        issues.append(
                            ValidationIssue(
                                "critical_player_metric_present",
                                "warning",
                                "Critical player summary metric was not parsed for a team.",
                                {"team": team, "metric": metric},
                            )
                        )

        shots_pages_present = any(page.section == "shots" for page in pages)
        if not shots_pages_present or not self._has_columns(shot_totals, "team"):
            return

        required_fields = ["total", "on_goal", "goals", "xg_total", "psxg_total"]
        for team in teams:
            rows = shot_totals[shot_totals["team"] == team]
            if rows.empty:
                issues.append(
                    ValidationIssue(
                        "critical_shot_total_field_present",
                        "warning",
                        "Shots page totals were not parsed for a team.",
                        {"team": team, "field": "__row__"},
                    )
                )
                continue
            row = rows.iloc[0]
            for field in required_fields:
                if field not in rows.columns or self._number(row.get(field)) is None:
                    issues.append(
                        ValidationIssue(
                            "critical_shot_total_field_present",
                            "warning",
                            "Critical Shots page total field was not parsed for a team.",
                            {"team": team, "field": field},
                        )
                    )

    def _validate_shot_parse_status(
        self,
        shots: pd.DataFrame,
        issues: list[ValidationIssue],
    ) -> None:
        """Flag shot rows that failed to parse, independent of any totals check.

        This is a direct, first-class signal: even when the Shots page totals are
        absent (so the row-count reconciliation cannot run), an unparsed shot row
        means a credibility-critical number may be missing or wrong.
        """
        if not self._has_columns(shots, "parse_status"):
            return

        failed = shots[shots["parse_status"] != "parsed"]
        if failed.empty:
            return

        evidence_columns = ["raw_line", "cleaned_line", "source_page", "team", "parse_status"]
        rows = []
        for _, row in failed.iterrows():
            rows.append(
                {column: row.get(column) for column in evidence_columns if column in shots.columns}
            )

        issues.append(
            ValidationIssue(
                "shot_rows_parse_cleanly",
                "warning",
                "One or more shot rows failed to parse cleanly.",
                {"failed_count": int(len(failed)), "rows": rows},
                table="shots",
                criticality="critical",
            )
        )

    def _classify_issues(self, issues: list[ValidationIssue]) -> None:
        """Stamp each issue with its table scope and criticality (see ISSUE_POLICY)."""
        for issue in issues:
            if issue.check_id == "table_not_empty":
                table = issue.details.get("table")
                issue.table = table
                issue.criticality = "critical" if table in CRITICAL_EMPTY_TABLES else "standard"
            elif issue.check_id == "team_stat_rows_attributed":
                issue.table = "team_stats"
                issue.criticality = (
                    "critical"
                    if issue.details.get("metric") in CRITICAL_TEAM_METRICS
                    else "standard"
                )
            elif issue.check_id in ISSUE_POLICY:
                issue.table, issue.criticality = ISSUE_POLICY[issue.check_id]

    def _build_table_readiness(
        self,
        dataframes: dict[str, pd.DataFrame],
        issues: list[ValidationIssue],
    ) -> dict[str, dict[str, Any]]:
        """Per-table readiness/confidence so consumers can gate article claims."""
        table_names = list(NORMALIZED_TABLES)
        for issue in issues:
            if issue.table and issue.table not in table_names:
                table_names.append(issue.table)

        readiness: dict[str, dict[str, Any]] = {}
        for table_name in sorted(table_names):
            df = dataframes.get(table_name)
            row_count = int(len(df)) if isinstance(df, pd.DataFrame) else 0
            failed_rows = self._count_failed_rows(df)

            table_issues = [issue for issue in issues if issue.table == table_name]
            issue_check_ids = sorted({issue.check_id for issue in table_issues})
            critical_issue_check_ids = sorted(
                {issue.check_id for issue in table_issues if issue.criticality == "critical"}
            )
            has_error = any(issue.severity == "error" for issue in table_issues)
            has_critical_warning = any(
                issue.severity == "warning" and issue.criticality == "critical"
                for issue in table_issues
            )
            has_standard_warning = any(
                issue.severity == "warning" and issue.criticality == "standard"
                for issue in table_issues
            )

            reasons = []
            if has_error:
                reasons.append("error-level issue(s)")
            if failed_rows:
                reasons.append(f"{failed_rows} row(s) failed to parse")

            if has_error or failed_rows:
                confidence, level = "none", "raw_only"
            elif has_critical_warning:
                confidence, level = "low", "analysis_only"
                reasons.append("critical match-story warning(s)")
            elif has_standard_warning:
                confidence, level = "low", "analysis_only"
                reasons.append("non-critical warning(s)")
            else:
                confidence, level = "high", "publication"

            readiness[table_name] = {
                "confidence": confidence,
                "readiness": level,
                "fit_for_article_claims": level == "publication",
                "row_count": row_count,
                "failed_rows": failed_rows,
                "issue_check_ids": issue_check_ids,
                "critical_issue_check_ids": critical_issue_check_ids,
                "quarantine_reason": "; ".join(reasons) if reasons else None,
            }
        return readiness

    def _build_metric_readiness(
        self,
        dataframes: dict[str, pd.DataFrame],
        issues: list[ValidationIssue],
    ) -> dict[str, dict[str, dict[str, Any]]]:
        metric_keys = {
            "team_stats": ["Goals", "xG", "Shots / on target", "Fouls / suffered"],
            "player_stats": ["goals_xg", "shots_on_target"],
            "shots": ["__table__"],
            "shot_totals": ["__table__"],
        }
        readiness: dict[str, dict[str, dict[str, Any]]] = {}
        for table_name, metrics in metric_keys.items():
            table_df = dataframes.get(table_name)
            readiness[table_name] = {}
            for metric in metrics:
                metric_issues = [
                    issue
                    for issue in issues
                    if issue.table == table_name and self._issue_applies_to_metric(issue, metric)
                ]
                failed_rows = self._count_failed_rows(table_df) if metric == "__table__" else 0
                has_error = any(issue.severity == "error" for issue in metric_issues)
                has_critical_warning = any(
                    issue.severity == "warning" and issue.criticality == "critical"
                    for issue in metric_issues
                )
                has_warning = any(issue.severity == "warning" for issue in metric_issues)

                reasons = []
                if has_error:
                    reasons.append("error-level issue(s)")
                if failed_rows:
                    reasons.append(f"{failed_rows} row(s) failed to parse")
                if has_critical_warning:
                    reasons.append("critical match-story warning(s)")
                elif has_warning:
                    reasons.append("non-critical warning(s)")

                if has_error or failed_rows:
                    confidence, level = "none", "raw_only"
                elif has_critical_warning or has_warning:
                    confidence, level = "low", "analysis_only"
                else:
                    confidence, level = "high", "publication"

                readiness[table_name][metric] = {
                    "confidence": confidence,
                    "readiness": level,
                    "fit_for_article_claims": level == "publication",
                    "issue_check_ids": sorted({issue.check_id for issue in metric_issues}),
                    "critical_issue_check_ids": sorted(
                        {issue.check_id for issue in metric_issues if issue.criticality == "critical"}
                    ),
                    "quarantine_reason": "; ".join(reasons) if reasons else None,
                }
        return readiness

    def _critical_team_metric_is_usable(self, row: pd.Series, metric: str) -> bool:
        if metric in {"Goals", "xG"}:
            return (
                self._number(row.get("value")) is not None
                or self._number(row.get("raw_value")) is not None
            )
        if metric == "Shots / on target":
            if (
                self._number(row.get("first")) is not None
                and self._number(row.get("second")) is not None
            ):
                return True
            return self._parse_slash_pair(row.get("raw_value")) is not None
        return self._has_value(row.get("raw_value"))

    def _issue_applies_to_metric(self, issue: ValidationIssue, metric: str) -> bool:
        if metric == "__table__":
            return True
        if issue.check_id == "table_not_empty":
            return metric in {
                "Goals",
                "xG",
                "Shots / on target",
                "goals_xg",
                "shots_on_target",
            }
        issue_metric = issue.details.get("metric")
        if issue_metric == metric:
            return True
        if issue.check_id == "fouls_suffered_are_symmetric" and metric == "Fouls / suffered":
            return True
        if issue.check_id == "possession_sums_to_100" and metric == "Possession %":
            return True
        if issue.check_id in {
            "score_matches_team_goals",
            "player_goals_sum_to_team_goals",
            "shot_page_goals_match_team_goals",
        }:
            return metric in {"Goals", "goals_xg", "__table__"}
        if issue.check_id in {
            "player_xg_sums_to_team_xg",
            "shot_page_xg_matches_team_xg",
            "shot_rows_xg_sum_to_shot_page_xg",
            "shot_rows_psxg_sum_to_shot_page_psxg",
        }:
            return metric in {"xG", "goals_xg", "__table__"}
        if issue.check_id in {
            "player_shots_sum_to_team_shots",
            "shot_page_total_matches_team_shots",
            "shot_page_on_goal_matches_team_on_target",
        }:
            return metric in {"Shots / on target", "shots_on_target", "__table__"}
        return False

    def _count_failed_rows(self, df: pd.DataFrame | None) -> int:
        if not isinstance(df, pd.DataFrame) or df.empty or "parse_status" not in df.columns:
            return 0
        return int(df["parse_status"].isin(HARD_FAILURE_STATUSES).sum())

    def _critical_metrics_ready(
        self,
        table_readiness: dict[str, dict[str, Any]],
        issues: list[ValidationIssue],
    ) -> bool:
        """True only when no credibility-critical finding exists anywhere."""
        return not any(issue.criticality == "critical" for issue in issues)

    def _validate_score_vs_goals(
        self,
        metadata: dict[str, Any],
        team_stats: pd.DataFrame,
        issues: list[ValidationIssue],
    ) -> None:
        if not self._has_columns(team_stats, "team", "metric"):
            return

        for team_key, score_key in [("home_team", "home_score"), ("away_team", "away_score")]:
            team = metadata.get(team_key)
            expected = metadata.get(score_key)
            actual = self._team_metric_number(team_stats, team, "Goals", "value")
            if team and expected is not None and actual is not None and int(actual) != int(expected):
                issues.append(
                    ValidationIssue(
                        "score_matches_team_goals",
                        "error",
                        "Scoreline does not match team Goals stat.",
                        {"team": team, "scoreline_goals": expected, "team_stat_goals": actual},
                    )
                )

    def _validate_player_xg_and_goals(
        self,
        metadata: dict[str, Any],
        team_stats: pd.DataFrame,
        player_stats: pd.DataFrame,
        issues: list[ValidationIssue],
    ) -> None:
        if not self._has_columns(team_stats, "team", "metric"):
            return
        if not self._has_columns(player_stats, "team", "stat_group", "metric", "first", "second"):
            return

        goals_xg = player_stats[
            (player_stats["stat_group"] == "summary") & (player_stats["metric"] == "goals_xg")
        ]
        for team in [metadata.get("home_team"), metadata.get("away_team")]:
            if not team:
                continue
            team_rows = goals_xg[goals_xg["team"] == team]
            player_goals = pd.to_numeric(team_rows["first"], errors="coerce").fillna(0).sum()
            player_xg = pd.to_numeric(team_rows["second"], errors="coerce").fillna(0).sum()
            team_goals = self._team_metric_number(team_stats, team, "Goals", "value")
            team_xg = self._team_metric_number(team_stats, team, "xG", "value")

            if team_goals is not None and int(player_goals) != int(team_goals):
                issues.append(
                    ValidationIssue(
                        "player_goals_sum_to_team_goals",
                        "error",
                        "Player goals do not sum to team Goals stat.",
                        {"team": team, "player_goals": player_goals, "team_goals": team_goals},
                    )
                )

            if team_xg is not None and abs(player_xg - float(team_xg)) > 0.03:
                issues.append(
                    ValidationIssue(
                        "player_xg_sums_to_team_xg",
                        "warning",
                        "Player xG does not reconcile with team xG.",
                        {"team": team, "player_xg": round(player_xg, 3), "team_xg": team_xg},
                    )
                )

    def _validate_player_shots(
        self,
        metadata: dict[str, Any],
        team_stats: pd.DataFrame,
        player_stats: pd.DataFrame,
        issues: list[ValidationIssue],
    ) -> None:
        if not self._has_columns(team_stats, "team", "metric"):
            return
        if not self._has_columns(player_stats, "team", "stat_group", "metric", "first", "second"):
            return

        shot_rows = player_stats[
            (player_stats["stat_group"] == "summary") & (player_stats["metric"] == "shots_on_target")
        ]
        for team in [metadata.get("home_team"), metadata.get("away_team")]:
            if not team:
                continue
            raw_team_shots = self._team_metric_raw(team_stats, team, "Shots / on target")
            expected = self._parse_slash_pair(raw_team_shots)
            if not expected:
                continue

            team_rows = shot_rows[shot_rows["team"] == team]
            player_shots = pd.to_numeric(team_rows["first"], errors="coerce").fillna(0).sum()
            player_on_target = pd.to_numeric(team_rows["second"], errors="coerce").fillna(0).sum()
            if int(player_shots) != int(expected[0]) or int(player_on_target) != int(expected[1]):
                issues.append(
                    ValidationIssue(
                        "player_shots_sum_to_team_shots",
                        "error",
                        "Player shots/on-target do not sum to team Shots / on target.",
                        {
                            "team": team,
                            "player_shots": player_shots,
                            "player_on_target": player_on_target,
                            "team_shots": expected[0],
                            "team_on_target": expected[1],
                        },
                    )
                )

    def _validate_player_parse_status(
        self,
        player_stats: pd.DataFrame,
        issues: list[ValidationIssue],
    ) -> None:
        required_columns = (
            "team",
            "source_page",
            "stat_group",
            "player_number",
            "player_name",
            "parse_status",
            "raw_line",
        )
        if not self._has_columns(player_stats, *required_columns):
            return

        player_rows = player_stats[list(required_columns)].drop_duplicates()
        bad_rows = player_rows[player_rows["parse_status"] != "parsed"]
        if bad_rows.empty:
            return

        details = []
        for _, row in bad_rows.iterrows():
            details.append(
                {
                    "team": row.get("team"),
                    "source_page": row.get("source_page"),
                    "stat_group": row.get("stat_group"),
                    "player_number": row.get("player_number"),
                    "player_name": row.get("player_name"),
                    "parse_status": row.get("parse_status"),
                    "raw_line": row.get("raw_line"),
                }
            )

        issues.append(
            ValidationIssue(
                "player_table_rows_parse_cleanly",
                "warning",
                "One or more player table rows had missing values or trailing unparsed tokens.",
                {"rows": details},
            )
        )

    def _validate_shot_page_totals(
        self,
        team_stats: pd.DataFrame,
        shot_totals: pd.DataFrame,
        shots: pd.DataFrame,
        issues: list[ValidationIssue],
    ) -> None:
        if not self._has_columns(team_stats, "team", "metric"):
            return
        if not self._has_columns(shot_totals, "team", "total"):
            return

        for _, row in shot_totals.iterrows():
            team = row["team"]
            team_raw = self._team_metric_raw(team_stats, team, "Shots / on target")
            expected = self._parse_slash_pair(team_raw)
            if expected and row.get("total") is not None and int(row["total"]) != int(expected[0]):
                issues.append(
                    ValidationIssue(
                        "shot_page_total_matches_team_shots",
                        "warning",
                        "Shots page total does not match team Shots / on target.",
                        {
                            "team": team,
                            "shots_page_total": row.get("total"),
                            "team_stat_shots": expected[0],
                        },
                    )
                )

            if expected and self._has_value(row.get("on_goal")) and int(row["on_goal"]) != int(expected[1]):
                issues.append(
                    ValidationIssue(
                        "shot_page_on_goal_matches_team_on_target",
                        "warning",
                        "Shots page on-goal total does not match team Shots / on target.",
                        {
                            "team": team,
                            "shots_page_on_goal": row.get("on_goal"),
                            "team_stat_on_target": expected[1],
                        },
                    )
                )

            team_goals = self._team_metric_number(team_stats, team, "Goals", "value")
            if self._has_value(row.get("goals")) and team_goals is not None:
                if int(row["goals"]) != int(team_goals):
                    issues.append(
                        ValidationIssue(
                            "shot_page_goals_match_team_goals",
                            "warning",
                            "Shots page goals do not match team Goals stat.",
                            {
                                "team": team,
                                "shots_page_goals": row.get("goals"),
                                "team_goals": team_goals,
                            },
                        )
                    )

            team_xg = self._team_metric_number(team_stats, team, "xG", "value")
            if self._has_value(row.get("xg_total")) and team_xg is not None:
                if abs(float(row["xg_total"]) - float(team_xg)) > 0.03:
                    issues.append(
                        ValidationIssue(
                            "shot_page_xg_matches_team_xg",
                            "warning",
                            "Shots page xG total does not reconcile with team xG.",
                            {
                                "team": team,
                                "shots_page_xg": row.get("xg_total"),
                                "team_xg": team_xg,
                            },
                        )
                    )

            if self._has_columns(shots, "team", "parse_status"):
                parsed_count = len(
                    shots[(shots["team"] == team) & (shots["parse_status"] == "parsed")]
                )
                failed_count = len(
                    shots[(shots["team"] == team) & (shots["parse_status"] == "failed")]
                )
            else:
                parsed_count = 0
                failed_count = 0
            if row.get("total") is not None and parsed_count != int(row["total"]):
                issues.append(
                    ValidationIssue(
                        "shot_rows_match_shot_page_total",
                        "warning",
                        "Parsed shot rows do not match the Shots page total.",
                        {
                            "team": team,
                            "shots_page_total": row.get("total"),
                            "parsed_shot_rows": parsed_count,
                            "failed_shot_rows": failed_count,
                        },
                    )
                )

    def _validate_shot_aggregates(
        self,
        team_stats: pd.DataFrame,
        shot_totals: pd.DataFrame,
        shots: pd.DataFrame,
        issues: list[ValidationIssue],
    ) -> None:
        if not self._has_columns(shot_totals, "team", "total"):
            return
        if not self._has_columns(shots, "team", "parse_status"):
            return

        for _, total_row in shot_totals.iterrows():
            team = total_row.get("team")
            if not self._has_value(team):
                continue

            parsed_rows = shots[(shots["team"] == team) & (shots["parse_status"] == "parsed")]
            if parsed_rows.empty:
                continue

            if self._has_columns(shots, "xg") and self._has_value(total_row.get("xg_total")):
                row_xg = pd.to_numeric(parsed_rows["xg"], errors="coerce").fillna(0).sum()
                if abs(float(row_xg) - float(total_row["xg_total"])) > 0.05:
                    issues.append(
                        ValidationIssue(
                            "shot_rows_xg_sum_to_shot_page_xg",
                            "warning",
                            "Parsed shot-row xG does not reconcile with the Shots page xG total.",
                            {
                                "team": team,
                                "shot_row_xg": round(float(row_xg), 3),
                                "shots_page_xg": total_row.get("xg_total"),
                            },
                        )
                    )

            if self._has_columns(shots, "psxg") and self._has_value(total_row.get("psxg_total")):
                row_psxg = pd.to_numeric(parsed_rows["psxg"], errors="coerce").fillna(0).sum()
                if abs(float(row_psxg) - float(total_row["psxg_total"])) > 0.03:
                    issues.append(
                        ValidationIssue(
                            "shot_rows_psxg_sum_to_shot_page_psxg",
                            "warning",
                            "Parsed shot-row post-shot xG does not reconcile with the Shots page PsxG total.",
                            {
                                "team": team,
                                "shot_row_psxg": round(float(row_psxg), 3),
                                "shots_page_psxg": total_row.get("psxg_total"),
                            },
                        )
                    )

            component_columns = ["on_goal", "blocked", "wide"]
            if all(self._has_value(total_row.get(column)) for column in component_columns):
                component_sum = sum(int(total_row[column]) for column in component_columns)
                if self._has_value(total_row.get("total")) and component_sum != int(total_row["total"]):
                    issues.append(
                        ValidationIssue(
                            "shot_page_result_buckets_sum_to_total",
                            "warning",
                            "Shots page result buckets do not sum to the total shot count.",
                            {
                                "team": team,
                                "total": total_row.get("total"),
                                "component_sum": component_sum,
                                "on_goal": total_row.get("on_goal"),
                                "blocked": total_row.get("blocked"),
                                "wide": total_row.get("wide"),
                                "goals": total_row.get("goals"),
                            },
                        )
                    )

        if not self._has_columns(team_stats, "team", "metric"):
            return

        for team in shot_totals["team"].dropna().unique():
            team_raw = self._team_metric_raw(team_stats, team, "Shots on post / blocked / wide")
            team_buckets = self._parse_slash_parts(team_raw)
            total_rows = shot_totals[shot_totals["team"] == team]
            if len(team_buckets) < 3 or total_rows.empty:
                continue
            total_row = total_rows.iloc[0]
            if self._has_value(total_row.get("blocked")) and int(total_row["blocked"]) != int(team_buckets[1]):
                issues.append(
                    ValidationIssue(
                        "shot_page_blocked_matches_team_blocked",
                        "warning",
                        "Shots page blocked total does not match team Shots on post / blocked / wide.",
                        {
                            "team": team,
                            "shots_page_blocked": total_row.get("blocked"),
                            "team_blocked": team_buckets[1],
                        },
                    )
                )
            if self._has_value(total_row.get("wide")) and int(total_row["wide"]) != int(team_buckets[2]):
                issues.append(
                    ValidationIssue(
                        "shot_page_wide_matches_team_wide",
                        "warning",
                        "Shots page wide total does not match team Shots on post / blocked / wide.",
                        {
                            "team": team,
                            "shots_page_wide": total_row.get("wide"),
                            "team_wide": team_buckets[2],
                        },
                    )
                )

    def _validate_shot_rows(
        self,
        shot_totals: pd.DataFrame,
        shots: pd.DataFrame,
        player_stats: pd.DataFrame,
        issues: list[ValidationIssue],
    ) -> None:
        if not self._has_columns(shots, "team", "parse_status", "shot_number"):
            return

        totals_by_team: dict[str, int] = {}
        if self._has_columns(shot_totals, "team", "total"):
            for _, row in shot_totals.dropna(subset=["team"]).iterrows():
                total = row.get("total")
                if total is not None and not pd.isna(total):
                    totals_by_team[str(row["team"])] = int(total)

        known_players = self._known_players_by_team(player_stats)
        for team, team_rows in shots.groupby("team", dropna=True):
            parsed_rows = team_rows[team_rows["parse_status"] == "parsed"]
            numbers = [
                int(number)
                for number in pd.to_numeric(parsed_rows["shot_number"], errors="coerce").dropna()
            ]
            if not numbers:
                continue

            duplicate_numbers = sorted(
                number for number in set(numbers) if numbers.count(number) > 1
            )
            if duplicate_numbers:
                issues.append(
                    ValidationIssue(
                        "shot_numbers_unique",
                        "warning",
                        "Parsed shot numbers are duplicated for a team.",
                        {"team": team, "duplicate_shot_numbers": duplicate_numbers},
                    )
                )

            if numbers != sorted(numbers):
                issues.append(
                    ValidationIssue(
                        "shot_numbers_monotonic",
                        "warning",
                        "Parsed shot numbers are not monotonic in source order.",
                        {"team": team, "shot_numbers": numbers},
                    )
                )

            expected_total = totals_by_team.get(str(team), max(numbers))
            expected_numbers = set(range(1, expected_total + 1))
            missing_numbers = sorted(expected_numbers - set(numbers))
            unexpected_numbers = sorted(set(numbers) - expected_numbers)
            if missing_numbers or unexpected_numbers:
                issues.append(
                    ValidationIssue(
                        "shot_numbers_complete",
                        "warning",
                        "Parsed shot numbers do not form the expected team sequence.",
                        {
                            "team": team,
                            "missing_shot_numbers": missing_numbers,
                            "unexpected_shot_numbers": unexpected_numbers,
                        },
                    )
                )

            for _, row in parsed_rows.iterrows():
                shot_type = row.get("shot_type")
                if shot_type not in ALLOWED_SHOT_TYPES:
                    issues.append(
                        ValidationIssue(
                            "shot_type_allowed",
                            "warning",
                            "Parsed shot type is not in the allowed Wyscout values.",
                            {
                                "team": team,
                                "shot_number": row.get("shot_number"),
                                "shot_type": shot_type,
                            },
                        )
                    )

                team_players = known_players.get(str(team))
                if team_players is None:
                    continue
                player_key = (row.get("player_number"), row.get("player_name"))
                if player_key not in team_players:
                    issues.append(
                        ValidationIssue(
                            "shot_player_matches_known_players",
                            "warning",
                            "Parsed shot player is not present in known player stats.",
                            {
                                "team": team,
                                "shot_number": row.get("shot_number"),
                                "player_number": row.get("player_number"),
                                "player_name": row.get("player_name"),
                            },
                        )
                    )

    def _validate_team_stat_attribution(
        self,
        metadata: dict[str, Any],
        team_stats: pd.DataFrame,
        issues: list[ValidationIssue],
    ) -> None:
        if not self._has_columns(team_stats, "metric", "team", "opponent"):
            return

        expected_teams = {metadata.get("home_team"), metadata.get("away_team")} - {None}
        if len(expected_teams) != 2:
            return

        for metric, metric_rows in team_stats.groupby("metric", dropna=False):
            if metric in GLOBAL_TEAM_STAT_METRICS or metric not in TEAM_STAT_CATEGORIES:
                continue

            attributed_rows = metric_rows[
                metric_rows["team"].isin(expected_teams) & metric_rows["opponent"].notna()
            ]
            if len(metric_rows) != 2 or set(attributed_rows["team"]) != expected_teams:
                issues.append(
                    ValidationIssue(
                        "team_stat_rows_attributed",
                        "error",
                        "Two-sided team metric was not parsed into home and away attributed rows.",
                        {
                            "metric": metric,
                            "row_count": len(metric_rows),
                            "teams": sorted(
                                str(team) for team in metric_rows["team"].dropna().unique()
                            ),
                        },
                    )
                )

    def _validate_possession_and_symmetry(
        self,
        team_stats: pd.DataFrame,
        issues: list[ValidationIssue],
    ) -> None:
        if not self._has_columns(team_stats, "metric", "raw_value"):
            return

        possession = team_stats[team_stats["metric"] == "Possession %"]
        if len(possession) == 2:
            total = pd.to_numeric(possession["value"], errors="coerce").sum()
            if abs(total - 100) > 0.1:
                issues.append(
                    ValidationIssue(
                        "possession_sums_to_100",
                        "warning",
                        "Team possession percentages do not sum to 100.",
                        {"possession_sum": total},
                    )
                )

        fouls = team_stats[team_stats["metric"] == "Fouls / suffered"]
        if len(fouls) == 2:
            left = self._parse_slash_pair(fouls.iloc[0]["raw_value"])
            right = self._parse_slash_pair(fouls.iloc[1]["raw_value"])
            if left and right and (int(left[0]) != int(right[1]) or int(left[1]) != int(right[0])):
                issues.append(
                    ValidationIssue(
                        "fouls_suffered_are_symmetric",
                        "warning",
                        "Fouls/suffered values are not symmetric across teams.",
                        {
                            "team_a": fouls.iloc[0]["team"],
                            "team_a_value": fouls.iloc[0]["raw_value"],
                            "team_a_fouls": left[0],
                            "team_a_suffered": left[1],
                            "team_b": fouls.iloc[1]["team"],
                            "team_b_value": fouls.iloc[1]["raw_value"],
                            "team_b_fouls": right[0],
                            "team_b_suffered": right[1],
                            "expected_team_a_suffered_from_team_b_fouls": right[0],
                            "expected_team_b_suffered_from_team_a_fouls": left[0],
                        },
                    )
                )

    def _value_row(
        self,
        metadata: dict[str, Any],
        source_page: int,
        table_name: str,
        category: str,
        metric: str,
        team: str | None,
        opponent: str | None,
        raw_value: str,
        parse_status: str = "parsed",
    ) -> dict[str, Any]:
        return {
            "match_id": metadata.get("match_id"),
            "source": metadata.get("source"),
            "source_page": source_page,
            "table_name": table_name,
            "category": category,
            "metric": metric,
            "team": team,
            "opponent": opponent,
            "raw_value": raw_value,
            "parse_status": parse_status,
            **self._parse_value(raw_value),
        }

    def _parse_value(self, raw_value: Any) -> dict[str, Any]:
        raw = "" if raw_value is None else str(raw_value).strip()
        result: dict[str, Any] = {
            "value": None,
            "first": None,
            "second": None,
            "third": None,
            "percentage": None,
            "seconds": None,
            "parts_json": None,
        }
        if raw in {"", "-"}:
            return result

        tokens = raw.split()
        if tokens and tokens[-1].endswith("%"):
            result["percentage"] = self._number(tokens[-1].rstrip("%"))
            raw_without_pct = " ".join(tokens[:-1])
        else:
            raw_without_pct = raw

        if re.match(r"^\d{1,2}:\d{2}$", raw_without_pct):
            minutes, seconds = raw_without_pct.split(":")
            result["seconds"] = int(minutes) * 60 + int(seconds)
            result["value"] = result["seconds"]
            return result

        if "/" in raw_without_pct:
            parts = [self._number(part) for part in raw_without_pct.split("/")]
            result["parts_json"] = json.dumps(parts)
            for key, value in zip(["first", "second", "third"], parts):
                result[key] = value
            result["value"] = parts[0] if parts else None
            return result

        result["value"] = self._number(raw_without_pct)
        return result

    def _split_team_values(self, metric: str, rest: str) -> list[str]:
        if metric in GLOBAL_TEAM_STAT_METRICS:
            return [rest]

        tokens = rest.split()
        for split_at in range(1, len(tokens)):
            left = " ".join(tokens[:split_at])
            right = " ".join(tokens[split_at:])
            if self._is_team_stat_value(left) and self._is_team_stat_value(right):
                return [left, right]
        return []

    def _player_table_lines(self, lines: list[str]) -> list[str]:
        first_header_idx = next((idx for idx, line in enumerate(lines) if line == "Player"), None)
        before_header = lines[:first_header_idx] if first_header_idx is not None else lines
        table_lines = self._player_rows_from_lines(before_header)
        if table_lines or first_header_idx is None:
            return table_lines

        after_header = []
        for line in lines[first_header_idx + 1 :]:
            if line == "Player" or line.startswith("MATCH REPORT"):
                break
            after_header.append(line)
        return self._player_rows_from_lines(after_header)

    def _player_rows_from_lines(self, lines: list[str]) -> list[str]:
        return [
            line
            for line in lines
            if line != "Passing" and re.match(r"^\d+\s+.+?\s+\d{1,3}'\s+", line)
        ]

    def _detect_player_stat_group(self, lines: list[str]) -> str:
        heading_window = lines[:10]
        compact_headings = {self._compact_title(line) for line in heading_window}
        return "passing" if "PASSING" in compact_headings else "summary"

    def _parse_player_table_line(
        self,
        line: str,
        specs: list[tuple[str, bool]],
    ) -> dict[str, Any] | None:
        match = re.match(r"^\s*(\d+)\s+(.+?)\s+(\d{1,3})'\s+(.*)$", line)
        if not match:
            return None

        tokens = match.group(4).split()
        values = {}
        missing_values = False
        for metric, maybe_percent in specs:
            if not tokens:
                values[metric] = ""
                missing_values = True
                continue
            value = tokens.pop(0)
            if maybe_percent and tokens and tokens[0].endswith("%"):
                value = f"{value} {tokens.pop(0)}"
            values[metric] = value

        if missing_values:
            parse_status = "failed_missing_values"
        elif tokens:
            parse_status = "parsed_with_tail"
        else:
            parse_status = "parsed"

        return {
            "player_number": int(match.group(1)),
            "player_name": match.group(2).strip(),
            "minutes_played": int(match.group(3)),
            "values": values,
            "parse_status": parse_status,
            "unparsed_tail": " ".join(tokens),
            "expected_metric_count": len(specs),
            "parsed_metric_count": sum(1 for value in values.values() if value != ""),
        }

    def _shot_table_lines(self, lines: list[str]) -> list[str]:
        rows = []
        in_table = False
        for line in lines:
            if line.startswith("# Player Time Shot type"):
                in_table = True
                continue
            if in_table and line.startswith("Total xG:"):
                break
            if in_table and re.match(r"^\d+", line):
                rows.append(line)
        return rows

    def _parse_shot_line(
        self,
        line: str,
        expected_shot_number: int | None = None,
        known_players: set[tuple[Any, Any]] | None = None,
    ) -> dict[str, Any] | None:
        pattern = re.compile(
            r"^(\d+)\s+(\d+)\s+(.+?)\s+"
            r"(\d{1,2}(?:\+\d+)?')\s+(.+?)\s+"
            r"(<\d+(?:\.\d+)?|\d+(?:\.\d+)?|-)\s+"
            r"(<\d+(?:\.\d+)?|\d+(?:\.\d+)?|-)$"
        )
        match = pattern.match(line)
        if not match:
            return None
        player_name = match.group(3).strip()
        shot_type = match.group(5).strip()
        if shot_type not in ALLOWED_SHOT_TYPES or not self._is_sane_player_name(player_name):
            return None
        shot_number = self._normalize_shot_number(match.group(1), expected_shot_number)
        if shot_number is None:
            return None
        player_number = self._normalize_player_number(match.group(2), player_name, known_players)
        return {
            "shot_number": shot_number,
            "player_number": player_number,
            "player_name": player_name,
            "minute": match.group(4),
            "shot_type": shot_type,
            "xg": self._number(match.group(6).replace("<", "")),
            "psxg": self._number(match.group(7).replace("<", "")),
        }

    def _parse_shot_total(self, lines: list[str]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        labels = {
            "Total": "total",
            "On goal": "on_goal",
            "Wide": "wide",
            "Blocked": "blocked",
            "Goal": "goals",
        }
        for idx, line in enumerate(lines):
            if line in labels and idx + 1 < len(lines):
                next_line = lines[idx + 1]
                parts = next_line.split()
                result[labels[line]] = self._number(parts[0]) if parts else None
                if len(parts) > 1 and parts[1].endswith("%"):
                    result[f"{labels[line]}_percentage"] = self._number(parts[1].rstrip("%"))

            if line.startswith("Total xG:"):
                parts = line.replace("Total xG:", "").strip().split()
                if parts:
                    result["xg_total"] = self._number(parts[0])
                if len(parts) > 1:
                    result["psxg_total"] = self._number(parts[1])
        return result

    def _detect_page_team(self, lines: list[str], metadata: dict[str, Any]) -> str | None:
        teams = [metadata.get("home_team"), metadata.get("away_team")]
        compact_lines = [self._compact_title(line) for line in lines]
        for idx, compact in enumerate(compact_lines):
            if compact in {"PLAYERSTATS", "SHOTS"}:
                for following in lines[idx + 1 : idx + 4]:
                    if following in teams:
                        return following

        for team in teams:
            if team and lines and lines[0] == team:
                return team

        # Shot pages often put the team name just after the report title near the end.
        for team in teams:
            if team and any(line == team for line in lines[-8:]):
                return team

        return None

    def _detect_section(self, default_text: str, layout_text: str, page_number: int) -> str:
        if page_number == 1:
            return "cover"

        for text in [default_text, layout_text]:
            title = self._section_after_match_report(self._lines(text))
            if title:
                return title

        for text in [default_text, layout_text]:
            for line in self._lines(text):
                compact = self._compact_title(line)
                if compact in SECTION_BY_COMPACT_TITLE:
                    return SECTION_BY_COMPACT_TITLE[compact]

        return "unknown"

    def _section_after_match_report(self, lines: list[str]) -> str | None:
        compact_lines = [self._compact_title(line) for line in lines]
        for idx, compact in enumerate(compact_lines):
            if compact != "MATCHREPORT":
                continue
            for candidate in compact_lines[idx + 1 : idx + 5]:
                if candidate in SECTION_BY_COMPACT_TITLE:
                    return SECTION_BY_COMPACT_TITLE[candidate]
        return None

    def _first_page_for_section(
        self,
        pages: list[PageText],
        section: str,
    ) -> PageText | None:
        return next((page for page in pages if page.section == section), None)

    def _team_metric_raw(self, team_stats: pd.DataFrame, team: str | None, metric: str) -> str | None:
        if not self._has_columns(team_stats, "team", "metric", "raw_value") or not team:
            return None
        rows = team_stats[(team_stats["team"] == team) & (team_stats["metric"] == metric)]
        if rows.empty:
            return None
        return str(rows.iloc[0]["raw_value"])

    def _team_metric_number(
        self,
        team_stats: pd.DataFrame,
        team: str | None,
        metric: str,
        column: str,
    ) -> float | None:
        if not self._has_columns(team_stats, "team", "metric", column) or not team:
            return None
        rows = team_stats[(team_stats["team"] == team) & (team_stats["metric"] == metric)]
        if rows.empty:
            return None
        value = rows.iloc[0].get(column)
        return None if pd.isna(value) else float(value)

    def _parse_slash_parts(self, raw_value: str | None) -> tuple[float, ...]:
        if raw_value is None:
            return ()
        first_token = str(raw_value).split()[0]
        if "/" not in first_token:
            return ()
        parts = first_token.split("/")
        values = tuple(self._number(part) for part in parts)
        if any(value is None for value in values):
            return ()
        return values

    def _parse_slash_pair(self, raw_value: str | None) -> tuple[float, float] | None:
        parts = self._parse_slash_parts(raw_value)
        if len(parts) < 2:
            return None
        return parts[0], parts[1]

    def _opponent(self, team: str | None, metadata: dict[str, Any]) -> str | None:
        if not team:
            return None
        if team == metadata.get("home_team"):
            return metadata.get("away_team")
        if team == metadata.get("away_team"):
            return metadata.get("home_team")
        return None

    def _make_match_id(self, metadata: dict[str, Any], pdf_path: Path) -> str:
        date = metadata.get("match_date") or "unknown_date"
        home = metadata.get("home_team") or pdf_path.stem
        away = metadata.get("away_team") or ""
        return self._slugify(f"{date}_{home}_{away}")

    def _slugify(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
        return slug or "wyscout_match"

    def _sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file_obj:
            for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _iso_date(self, wyscout_date: str) -> str:
        return datetime.strptime(wyscout_date, "%d/%m/%Y").date().isoformat()

    def _compact_title(self, text: str) -> str:
        return re.sub(r"[^A-Z]", "", text.upper())

    def _lines(self, text: str) -> list[str]:
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _number(self, value: Any) -> float | int | None:
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass
        text = str(value).strip()
        if text in {"", "-"}:
            return None
        try:
            number = float(text)
        except ValueError:
            return None
        return int(number) if number.is_integer() else number

    def _has_columns(self, df: pd.DataFrame, *columns: str) -> bool:
        return not df.empty and all(column in df.columns for column in columns)

    def _has_value(self, value: Any) -> bool:
        if value is None:
            return False
        try:
            return not bool(pd.isna(value))
        except (TypeError, ValueError):
            return True

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._json_safe(item) for item in value]
        if isinstance(value, tuple):
            return [self._json_safe(item) for item in value]
        if isinstance(value, float) and pd.isna(value):
            return None
        if hasattr(value, "item"):
            return value.item()
        return value

    def _clean_repeated_fragments(self, line: str) -> str:
        line = re.sub(r"\b(Left foot|Right foot|Head|Other)\1\b", r"\1", line)
        line = re.sub(
            r"\b([A-ZÀ-ÖØ-Þ][\w.\-]*(?:\s+[A-ZÀ-ÖØ-Þ][\w.\-]*)+)\1\b",
            r"\1",
            line,
        )
        return " ".join(self._dedupe_token(token) for token in line.split())

    def _dedupe_token(self, token: str) -> str:
        if token.isdigit():
            return token
        previous = None
        current = token
        while previous != current:
            previous = current
            midpoint = len(current) // 2
            if len(current) % 2 == 0 and current[:midpoint] == current[midpoint:]:
                current = current[:midpoint]
        return current

    def _normalize_shot_number(
        self,
        token: str,
        expected_shot_number: int | None,
    ) -> int | None:
        candidates = self._numeric_overlay_candidates(token)
        if expected_shot_number is None:
            return candidates[0] if candidates else None
        for candidate in candidates:
            if candidate == expected_shot_number:
                return candidate
        return None

    def _normalize_player_number(
        self,
        token: str,
        player_name: str,
        known_players: set[tuple[Any, Any]] | None,
    ) -> int | None:
        candidates = self._numeric_overlay_candidates(token)
        if known_players:
            for candidate in candidates:
                if (candidate, player_name) in known_players:
                    return candidate
        return candidates[0] if candidates else None

    def _numeric_overlay_candidates(self, token: str) -> list[int]:
        if not token.isdigit():
            return []
        candidates = [int(token)]
        midpoint = len(token) // 2
        if len(token) % 2 == 0 and token[:midpoint] == token[midpoint:]:
            deduped = int(token[:midpoint])
            if deduped not in candidates:
                candidates.append(deduped)
        return candidates

    def _is_team_stat_value(self, value: str) -> bool:
        value = value.strip()
        if value == "-":
            return True
        number = r"\d+(?:\.\d+)?"
        slash_value = rf"{number}(?:/{number})+"
        time_value = r"\d{1,2}:\d{2}"
        base_value = rf"(?:{number}|{slash_value}|{time_value})"
        return re.match(rf"^{base_value}(?:\s+{number}%)?$", value) is not None

    def _is_sane_player_name(self, player_name: str) -> bool:
        if not re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", player_name):
            return False
        for token in player_name.split():
            if token.endswith(".") and len(token) > 2:
                return False
        compact = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ]", "", player_name)
        return re.search(r"([A-Za-zÀ-ÖØ-öø-ÿ]{2,})\1", compact) is None

    def _known_players_by_team(
        self,
        player_stats: pd.DataFrame,
    ) -> dict[str, set[tuple[Any, Any]]]:
        if not self._has_columns(player_stats, "team", "player_number", "player_name"):
            return {}

        known_players: dict[str, set[tuple[Any, Any]]] = {}
        player_rows = player_stats[["team", "player_number", "player_name"]].drop_duplicates()
        for _, row in player_rows.iterrows():
            team = row.get("team")
            if pd.isna(team):
                continue
            known_players.setdefault(str(team), set()).add(
                (row.get("player_number"), row.get("player_name"))
            )
        return known_players
