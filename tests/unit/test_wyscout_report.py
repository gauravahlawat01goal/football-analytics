"""Unit tests for Wyscout report processing."""

from football_analytics.processors.wyscout_report import PageText, WyscoutReportProcessor


def test_clean_repeated_fragments_handles_pdf_overlay_tokens():
    processor = WyscoutReportProcessor()

    cleaned = processor._clean_repeated_fragments(
        "1010 77 Son Heung-MinSon Heung-Min 45+2'45+2' Left footLeft foot 0.330.33 --"
    )

    assert cleaned == "1010 77 Son Heung-Min 45+2' Left foot 0.33 -"


def test_clean_repeated_fragments_preserves_valid_two_digit_shot_numbers():
    processor = WyscoutReportProcessor()

    cleaned = processor._clean_repeated_fragments("11 7 Son Heung-Min 56' Left foot 0.05 -")

    assert cleaned.startswith("11 7 ")


def test_parse_player_summary_line_preserves_values_and_tail():
    processor = WyscoutReportProcessor()
    line = (
        "7 Son Heung-Min 72' 0/0.85 0/0.00 40/21 53% 6/1 17% "
        "20/18 90% - - 10/2 20% 9/2 1/0 4 1 -"
    )

    parsed = processor._parse_player_table_line(line, processor_module_specs("summary"))

    assert parsed["player_number"] == 7
    assert parsed["player_name"] == "Son Heung-Min"
    assert parsed["minutes_played"] == 72
    assert parsed["values"]["goals_xg"] == "0/0.85"
    assert parsed["values"]["shots_on_target"] == "6/1 17%"
    assert parsed["values"]["yellow_red_cards"] == "-"
    assert parsed["parse_status"] == "parsed"


def test_parse_player_line_with_missing_values_is_not_clean():
    processor = WyscoutReportProcessor()
    line = "7 Son Heung-Min 72' 0/0.85 0/0.00"

    parsed = processor._parse_player_table_line(line, processor_module_specs("summary"))

    assert parsed["parse_status"] == "failed_missing_values"
    assert parsed["expected_metric_count"] == len(processor_module_specs("summary"))
    assert parsed["parsed_metric_count"] == 2


def test_player_table_lines_survive_player_header_before_rows():
    processor = WyscoutReportProcessor()
    lines = [
        "Passing",
        "Player",
        "7 Son Heung-Min 72' 1/1 100% 2/2 100% 3/3 100% 4/4 100% 5/5 100% 6/6 100% 7/7 100% 0/0 - - - 1 21.4",
    ]

    assert processor._detect_player_stat_group(lines) == "passing"
    assert processor._player_table_lines(lines) == [lines[2]]


def test_team_stats_parse_keeps_raw_and_derived_fields():
    processor = WyscoutReportProcessor()
    pages = [
        PageText(
            page_number=5,
            section="team_stats",
            default_text="\n".join(
                [
                    "Goals 2 1",
                    "xG 2.41 0.87",
                    "Shots / on target 15/7 6/4",
                    "Possession % 60 40",
                    "Through passes / accurate 1/1 100% 0",
                    "Fouls / suffered 9/16 16/9",
                    "Dead time 53:53",
                ]
            ),
            layout_text="",
        )
    ]
    metadata = {
        "match_id": "sample",
        "source": "wyscout_report_pdf",
        "home_team": "Korea Republic",
        "away_team": "Czechia",
    }

    df = processor._parse_team_stats(pages, metadata)

    shots = df[(df["team"] == "Korea Republic") & (df["metric"] == "Shots / on target")]
    through_passes = df[df["metric"] == "Through passes / accurate"]
    dead_time = df[df["metric"] == "Dead time"]

    assert shots.iloc[0]["raw_value"] == "15/7"
    assert shots.iloc[0]["first"] == 15
    assert shots.iloc[0]["second"] == 7
    assert list(through_passes["team"]) == ["Korea Republic", "Czechia"]
    assert list(through_passes["raw_value"]) == ["1/1 100%", "0"]
    assert dead_time.iloc[0]["seconds"] == 3233


def test_parse_shot_line_preserves_11_and_rejects_corrupted_player_artifacts():
    processor = WyscoutReportProcessor()

    parsed = processor._parse_shot_line(
        processor._clean_repeated_fragments("11 7 Son Heung-Min 56' Left foot 0.05 -"),
        expected_shot_number=11,
    )
    failed = processor._parse_shot_line(
        processor._clean_repeated_fragments(
            "12 9 A. HloA. Hložžekek 82' Left footLeft foot 0.31 0.65"
        ),
        expected_shot_number=12,
    )

    assert parsed["shot_number"] == 11
    assert parsed["shot_type"] == "Left foot"
    assert failed is None


def test_parse_shot_line_repairs_numeric_overlays_with_context():
    processor = WyscoutReportProcessor()
    known_players = {
        (7, "Son Heung-Min"),
        (10, "Lee Jae-Sung"),
        (18, "M. Sadílek"),
    }

    son = processor._parse_shot_line(
        processor._clean_repeated_fragments(
            "77 77 Son Heung-MinSon Heung-Min 39'39' Left footLeft foot 0.210.21 --"
        ),
        expected_shot_number=7,
        known_players=known_players,
    )
    lee = processor._parse_shot_line(
        processor._clean_repeated_fragments(
            "1010 1010 Lee Jae-SungLee Jae-Sung 49'49' Left footLeft foot 0.630.63 0.700.70"
        ),
        expected_shot_number=10,
        known_players=known_players,
    )
    sadilek = processor._parse_shot_line(
        processor._clean_repeated_fragments(
            "44 1818 M. SadílekM. Sadílek 90+3'90+3' Right footRight foot 0.160.16 0.620.62"
        ),
        expected_shot_number=4,
        known_players=known_players,
    )

    assert son["shot_number"] == 7
    assert son["player_number"] == 7
    assert lee["shot_number"] == 10
    assert lee["player_number"] == 10
    assert sadilek["shot_number"] == 4
    assert sadilek["player_number"] == 18


def test_validate_flags_duplicate_missing_and_non_monotonic_shot_numbers():
    import pandas as pd

    processor = WyscoutReportProcessor()
    shots = pd.DataFrame(
        [
            {"team": "Korea Republic", "parse_status": "parsed", "shot_number": 1},
            {"team": "Korea Republic", "parse_status": "parsed", "shot_number": 3},
            {"team": "Korea Republic", "parse_status": "parsed", "shot_number": 1},
            {"team": "Korea Republic", "parse_status": "parsed", "shot_number": 2},
        ]
    )
    shot_totals = pd.DataFrame([{"team": "Korea Republic", "total": 4}])
    issues = []

    processor._validate_shot_rows(shot_totals, shots, empty_player_stats(), issues)

    check_ids = {issue.check_id for issue in issues}
    assert "shot_numbers_unique" in check_ids
    assert "shot_numbers_monotonic" in check_ids
    assert "shot_numbers_complete" in check_ids


def test_validate_flags_shot_page_mismatches_against_team_stats():
    import pandas as pd

    processor = WyscoutReportProcessor()
    team_stats = pd.DataFrame(
        [
            {"team": "Mexico", "metric": "Goals", "value": 2, "raw_value": "2"},
            {"team": "Mexico", "metric": "xG", "value": 1.32, "raw_value": "1.32"},
            {"team": "Mexico", "metric": "Shots / on target", "raw_value": "14/4"},
        ]
    )
    shot_totals = pd.DataFrame(
        [
            {
                "team": "Mexico",
                "total": 14,
                "on_goal": 3,
                "goals": 1,
                "xg_total": 1.40,
            }
        ]
    )
    issues = []

    processor._validate_shot_page_totals(team_stats, shot_totals, empty_shots(), issues)

    check_ids = {issue.check_id for issue in issues}
    assert "shot_page_on_goal_matches_team_on_target" in check_ids
    assert "shot_page_goals_match_team_goals" in check_ids
    assert "shot_page_xg_matches_team_xg" in check_ids


def test_validate_flags_shot_row_aggregate_mismatches():
    import pandas as pd

    processor = WyscoutReportProcessor()
    team_stats = pd.DataFrame(
        [
            {
                "team": "Mexico",
                "metric": "Shots on post / blocked / wide",
                "raw_value": "0/5/3",
            }
        ]
    )
    shot_totals = pd.DataFrame(
        [
            {
                "team": "Mexico",
                "total": 4,
                "xg_total": 0.20,
                "psxg_total": 0.70,
                "on_goal": 1,
                "blocked": 4,
                "wide": 1,
                "goals": 1,
            }
        ]
    )
    shots = pd.DataFrame(
        [
            {"team": "Mexico", "parse_status": "parsed", "xg": 0.10, "psxg": 0.10},
            {"team": "Mexico", "parse_status": "parsed", "xg": 0.10, "psxg": 0.10},
            {"team": "Mexico", "parse_status": "parsed", "xg": 0.10, "psxg": 0.10},
        ]
    )
    issues = []

    processor._validate_shot_aggregates(team_stats, shot_totals, shots, issues)

    check_ids = {issue.check_id for issue in issues}
    assert "shot_rows_xg_sum_to_shot_page_xg" in check_ids
    assert "shot_rows_psxg_sum_to_shot_page_psxg" in check_ids
    assert "shot_page_result_buckets_sum_to_total" in check_ids
    assert "shot_page_blocked_matches_team_blocked" in check_ids
    assert "shot_page_wide_matches_team_wide" in check_ids


def test_validate_flags_team_metric_without_two_attributed_rows():
    import pandas as pd

    processor = WyscoutReportProcessor()
    metadata = {
        "home_team": "Korea Republic",
        "away_team": "Czechia",
    }
    team_stats = pd.DataFrame(
        [
            {
                "metric": "Through passes / accurate",
                "team": None,
                "opponent": None,
                "raw_value": "1/1 100%",
                "parse_status": "failed",
            }
        ]
    )
    issues = []

    processor._validate_team_stat_attribution(metadata, team_stats, issues)

    assert [issue.check_id for issue in issues] == ["team_stat_rows_attributed"]


def test_validation_flags_unclean_player_table_rows():
    import pandas as pd

    processor = WyscoutReportProcessor()
    player_stats = pd.DataFrame(
        [
            {
                "team": "Korea Republic",
                "source_page": 6,
                "stat_group": "summary",
                "player_number": 7,
                "player_name": "Son Heung-Min",
                "parse_status": "failed_missing_values",
                "raw_line": "7 Son Heung-Min 72' 0/0.85",
            }
        ]
    )
    issues = []

    processor._validate_player_parse_status(player_stats, issues)

    assert [issue.check_id for issue in issues] == ["player_table_rows_parse_cleanly"]
    assert issues[0].details["rows"][0]["parse_status"] == "failed_missing_values"


def test_validation_flags_failed_shot_rows_as_critical_findings():
    import pandas as pd

    processor = WyscoutReportProcessor()
    shots = pd.DataFrame(
        [
            {
                "team": "Czechia",
                "source_page": 13,
                "raw_line": "33 99 A. HloA. Hložžekek 82'82' Left footLeft foot 0.310.31 0.650.65",
                "cleaned_line": "33 99 A. HloA. Hložžekek 82' Left foot 0.31 0.65",
                "parse_status": "failed",
            }
        ]
    )
    issues = []

    processor._validate_shot_parse_status(shots, issues)

    assert issues[0].check_id == "shot_rows_parse_cleanly"
    assert issues[0].table == "shots"
    assert issues[0].criticality == "critical"
    assert issues[0].details["failed_count"] == 1


def test_missing_critical_team_metric_is_critical():
    import pandas as pd

    processor = WyscoutReportProcessor()
    metadata = {"home_team": "Mexico", "away_team": "South Africa"}
    team_stats = pd.DataFrame(
        [
            {"team": "Mexico", "metric": "Goals", "raw_value": "2"},
            {"team": "South Africa", "metric": "Goals", "raw_value": "0"},
            {"team": "Mexico", "metric": "Shots / on target", "raw_value": "14/4"},
            {"team": "South Africa", "metric": "Shots / on target", "raw_value": "3/2"},
        ]
    )
    issues = []

    processor._validate_critical_metric_presence(
        metadata,
        [],
        team_stats,
        empty_player_stats(),
        pd.DataFrame(),
        issues,
    )
    processor._classify_issues(issues)

    missing_xg = [issue for issue in issues if issue.check_id == "critical_team_metric_present"]
    assert missing_xg
    assert all(issue.criticality == "critical" for issue in missing_xg)
    assert processor._critical_metrics_ready({}, issues) is False


def test_unusable_critical_team_metric_is_critical():
    import pandas as pd

    processor = WyscoutReportProcessor()
    metadata = {"home_team": "Mexico", "away_team": "South Africa"}
    team_stats = pd.DataFrame(
        [
            {"team": "Mexico", "metric": "Goals", "raw_value": "-", "value": None},
            {"team": "South Africa", "metric": "Goals", "raw_value": "-", "value": None},
            {"team": "Mexico", "metric": "xG", "raw_value": "-", "value": None},
            {"team": "South Africa", "metric": "xG", "raw_value": "-", "value": None},
            {
                "team": "Mexico",
                "metric": "Shots / on target",
                "raw_value": "-",
                "first": None,
                "second": None,
            },
            {
                "team": "South Africa",
                "metric": "Shots / on target",
                "raw_value": "-",
                "first": None,
                "second": None,
            },
        ]
    )
    issues = []

    processor._validate_critical_metric_presence(
        metadata,
        [],
        team_stats,
        empty_player_stats(),
        pd.DataFrame(),
        issues,
    )
    processor._classify_issues(issues)

    assert {issue.details["metric"] for issue in issues} == {
        "Goals",
        "xG",
        "Shots / on target",
    }
    assert all(issue.details["reason"] == "missing_or_unusable_value" for issue in issues)
    assert all(issue.criticality == "critical" for issue in issues)
    assert processor._critical_metrics_ready({}, issues) is False


def test_missing_shot_total_goals_is_critical():
    import pandas as pd

    processor = WyscoutReportProcessor()
    metadata = {"home_team": "Mexico", "away_team": "South Africa"}
    pages = [PageText(12, "shots", "", "")]
    shot_totals = pd.DataFrame(
        [
            {
                "team": "Mexico",
                "total": 14,
                "on_goal": 4,
                "xg_total": 1.32,
                "psxg_total": 1.04,
            },
            {
                "team": "South Africa",
                "total": 3,
                "on_goal": 2,
                "goals": 0,
                "xg_total": 0.46,
                "psxg_total": 0.20,
            },
        ]
    )
    issues = []

    processor._validate_critical_metric_presence(
        metadata,
        pages,
        pd.DataFrame(),
        empty_player_stats(),
        shot_totals,
        issues,
    )
    processor._classify_issues(issues)

    goal_issues = [
        issue
        for issue in issues
        if issue.check_id == "critical_shot_total_field_present"
        and issue.details["field"] == "goals"
    ]
    assert len(goal_issues) == 1
    assert goal_issues[0].details["team"] == "Mexico"
    assert goal_issues[0].criticality == "critical"
    assert processor._critical_metrics_ready({}, issues) is False


def test_metric_readiness_inherits_empty_critical_table_failure():
    import pandas as pd
    from football_analytics.processors.wyscout_report import ValidationIssue

    processor = WyscoutReportProcessor()
    issues = [
        ValidationIssue(
            "table_not_empty",
            "error",
            "Expected normalized table was empty.",
            {"table": "team_stats"},
        )
    ]

    processor._classify_issues(issues)
    metric_readiness = processor._build_metric_readiness({"team_stats": pd.DataFrame()}, issues)

    assert metric_readiness["team_stats"]["Goals"]["fit_for_article_claims"] is False
    assert metric_readiness["team_stats"]["xG"]["fit_for_article_claims"] is False
    assert metric_readiness["team_stats"]["Shots / on target"]["fit_for_article_claims"] is False
    assert metric_readiness["team_stats"]["Fouls / suffered"]["fit_for_article_claims"] is True


def test_fouls_warning_does_not_block_critical_metric_readiness():
    import pandas as pd

    processor = WyscoutReportProcessor()
    team_stats = pd.DataFrame(
        [
            {"team": "Mexico", "metric": "Goals", "raw_value": "2", "parse_status": "parsed"},
            {"team": "Mexico", "metric": "xG", "raw_value": "1.32", "parse_status": "parsed"},
            {
                "team": "Mexico",
                "metric": "Shots / on target",
                "raw_value": "14/4",
                "parse_status": "parsed",
            },
            {
                "team": "Mexico",
                "metric": "Fouls / suffered",
                "raw_value": "12/11",
                "parse_status": "parsed",
            },
            {
                "team": "South Africa",
                "metric": "Fouls / suffered",
                "raw_value": "11/11",
                "parse_status": "parsed",
            },
        ]
    )
    issues = []

    processor._validate_possession_and_symmetry(team_stats, issues)
    processor._classify_issues(issues)
    metric_readiness = processor._build_metric_readiness({"team_stats": team_stats}, issues)

    assert issues[0].check_id == "fouls_suffered_are_symmetric"
    assert issues[0].criticality == "standard"
    assert processor._critical_metrics_ready({}, issues) is True
    assert metric_readiness["team_stats"]["Goals"]["fit_for_article_claims"] is True
    assert metric_readiness["team_stats"]["xG"]["fit_for_article_claims"] is True
    assert metric_readiness["team_stats"]["Shots / on target"]["fit_for_article_claims"] is True
    assert metric_readiness["team_stats"]["Fouls / suffered"]["fit_for_article_claims"] is False


def test_validation_flags_shots_page_mismatch_as_warning():
    import pandas as pd

    processor = WyscoutReportProcessor()
    pages = [
        PageText(1, "cover", "", ""),
        PageText(3, "positions", "", ""),
        PageText(5, "team_stats", "", ""),
        PageText(6, "player_stats", "", ""),
        PageText(12, "shots", "", ""),
    ]
    metadata = {
        "match_id": "sample",
        "home_team": "Korea Republic",
        "away_team": "Czechia",
        "home_score": 2,
        "away_score": 1,
    }
    team_stats = processor._parse_team_stats(
        [
            PageText(
                page_number=5,
                section="team_stats",
                default_text="\n".join(
                    [
                        "Goals 2 1",
                        "xG 2.41 0.87",
                        "Shots / on target 15/7 6/4",
                        "Possession % 60 40",
                    ]
                ),
                layout_text="",
            )
        ],
        {**metadata, "source": "wyscout_report_pdf"},
    )
    shot_totals = processor._parse_shots(
        [
            PageText(
                page_number=12,
                section="shots",
                default_text="\n".join(
                    [
                        "Total",
                        "14",
                        "# Player Time Shot type xG* PsxG*",
                        "1 7 Son Heung-Min 12' Left foot 0.07 -",
                        "Total xG: 2.14 1.41",
                        "MATCH REPORT",
                        "SHO T S",
                        "Korea Republic",
                    ]
                ),
                layout_text="",
            )
        ],
        metadata,
    )[1]
    player_stats = pd.DataFrame(
        [
            {
                "team": "Korea Republic",
                "stat_group": "summary",
                "metric": "goals_xg",
                "first": 2,
                "second": 2.41,
                "parse_status": "parsed",
            },
            {
                "team": "Korea Republic",
                "stat_group": "summary",
                "metric": "shots_on_target",
                "first": 15,
                "second": 7,
                "parse_status": "parsed",
            },
            {
                "team": "Czechia",
                "stat_group": "summary",
                "metric": "goals_xg",
                "first": 1,
                "second": 0.87,
                "parse_status": "parsed",
            },
            {
                "team": "Czechia",
                "stat_group": "summary",
                "metric": "shots_on_target",
                "first": 6,
                "second": 4,
                "parse_status": "parsed",
            },
        ]
    )

    report = processor._validate(
        metadata,
        pages,
        {
            "team_stats": team_stats,
            "player_stats": player_stats,
            "shots": empty_shots(),
            "shot_totals": shot_totals,
        },
    )

    shot_issue = next(
        issue
        for issue in report["issues"]
        if issue["check_id"] == "shot_page_total_matches_team_shots"
    )
    assert shot_issue["severity"] == "warning"
    assert report["analysis_ready"] is True
    assert report["publication_ready"] is False
    assert report["critical_metrics_ready"] is False
    assert "shot_page_total_matches_team_shots" in [
        issue["check_id"] for issue in report["critical_findings"]
    ]
    assert report["table_readiness"]["shots"]["fit_for_article_claims"] is False
    assert "team_stats" in report["normalized_tables"]
    assert "positions" in report["detected_but_not_normalized_sections"]


def processor_module_specs(group):
    from football_analytics.processors.wyscout_report import (
        PLAYER_PASSING_SPECS,
        PLAYER_SUMMARY_SPECS,
    )

    return PLAYER_PASSING_SPECS if group == "passing" else PLAYER_SUMMARY_SPECS


def empty_player_stats():
    import pandas as pd

    return pd.DataFrame(
        columns=["team", "stat_group", "metric", "first", "second", "raw_value"]
    )


def empty_shots():
    import pandas as pd

    return pd.DataFrame(columns=["team", "parse_status"])
