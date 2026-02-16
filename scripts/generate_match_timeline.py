import json
import os

def generate_timeline(input_path, output_path):
    """
    Reads match event data from a JSON file and writes a formatted timeline to a text file.
    """
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {input_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {input_path}")
        return

    events = data.get('events', [])
    
    if not events:
        print("No events found in the data.")
        return

    # Sort events: primary by minute, secondary by extra_minute (treat None as 0), tertiary by sort_order
    def event_sort_key(e):
        minute = e.get('minute') or 0
        extra = e.get('extra_minute') or 0
        sort_order = e.get('sort_order') or 0
        return (minute, extra, sort_order)

    sorted_events = sorted(events, key=event_sort_key)

    lines = []
    lines.append(f"Match Timeline: {data.get('name', 'Unknown Match')}")
    lines.append(f"Date: {data.get('starting_at', 'Unknown Date')}")
    lines.append("-" * 50)

    for event in sorted_events:
        minute = event.get('minute')
        extra_minute = event.get('extra_minute')
        
        time_str = f"{minute}'"
        if extra_minute:
            time_str += f"+{extra_minute}"
            
        player_name = event.get('player_name')
        
        # Construct description from info and addition
        info = event.get('info')
        addition = event.get('addition')
        
        description_parts = []
        if info:
            description_parts.append(info)
        if addition:
            description_parts.append(addition)
            
        description = " - ".join(description_parts)
        
        # Fallback if no description
        if not description:
            description = event.get('type_id', 'Unknown Event') # fall back to type_id if nothing else? strictly maybe just say 'Event'

        line = f"{time_str:<8} | {player_name:<25} | {description}"
        lines.append(line)

    try:
        with open(output_path, 'w') as f:
            f.write("\n".join(lines))
        print(f"Timeline successfully written to {output_path}")
    except OSError as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    input_file = '/Users/gauravahlawat/git_projects/football-analytics/data/raw/ball_coordinates/fixture_19134454_complete.json'
    output_file = '/Users/gauravahlawat/git_projects/football-analytics/data/raw/ball_coordinates/fixture_19134454_timeline.txt'
    
    generate_timeline(input_file, output_file)
