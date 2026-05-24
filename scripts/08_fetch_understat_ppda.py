import argparse
import logging
from pathlib import Path

import pandas as pd
from understatapi import UnderstatClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
OUT_DIR = PROCESSED_DIR / "understat"

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Understat PPDA data")
    parser.add_argument("--league", type=str, required=True, help="e.g. 'EPL', 'Bundesliga'")
    parser.add_argument("--seasons", type=int, nargs="+", required=True, help="Start years, e.g. 2023 2024")
    parser.add_argument("--team-slug", type=str, required=True, help="'Liverpool' or 'Bayer Leverkusen'")
    args = parser.parse_args()

    safe_team_name = args.team_slug.lower().replace(" ", "_")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{safe_team_name}_ppda.csv"

    client = UnderstatClient()
    
    rows = []
    for season in args.seasons:
        log.info(f"Fetching PPDA for {args.league} season {season}")
        team_data = client.league(args.league).get_team_data(season=str(season))
        
        # find the team
        for team_id, team_info in team_data.items():
            if team_info["title"] == args.team_slug:
                for match in team_info["history"]:
                    rows.append({
                        "season": season,
                        "date": match["date"],
                        "h_a": match["h_a"],
                        "ppda_att": match["ppda"]["att"],
                        "ppda_def": match["ppda"]["def"],
                        "ppda": match["ppda"]["att"] / match["ppda"]["def"] if match["ppda"]["def"] > 0 else 0,
                        "ppda_allowed_att": match["ppda_allowed"]["att"],
                        "ppda_allowed_def": match["ppda_allowed"]["def"],
                        "ppda_allowed": match["ppda_allowed"]["att"] / match["ppda_allowed"]["def"] if match["ppda_allowed"]["def"] > 0 else 0,
                        "deep": match["deep"],
                        "deep_allowed": match["deep_allowed"]
                    })

    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    log.info(f"Saved {len(df)} PPDA rows to {out_path}")
    log.info(f"PPDA summary:\n{df.groupby('season')['ppda'].mean().round(2)}")

if __name__ == "__main__":
    main()
