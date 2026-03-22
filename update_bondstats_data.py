import json
import os
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen

API_KEY = os.environ.get("FRED_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing FRED_API_KEY environment variable.")

OUTPUT_FILE = "data.json"

SERIES = [
    {
        "country": "United States",
        "series_id": "DGS10",
        "label": "US 10Y",
        "source_note": "Daily"
    },
    {
        "country": "Germany",
        "series_id": "IRLTLT01DEM156N",
        "label": "Germany 10Y",
        "source_note": "Monthly"
    },
    {
        "country": "United Kingdom",
        "series_id": "IRLTLT01GBM156N",
        "label": "UK 10Y",
        "source_note": "Monthly"
    },
    {
        "country": "Japan",
        "series_id": "IRLTLT01JPM156N",
        "label": "Japan 10Y",
        "source_note": "Monthly"
    }
]

def fetch_latest_observation(series_id: str):
    params = urlencode({
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 12
    })
    url = f"https://api.stlouisfed.org/fred/series/observations?{params}"

    with urlopen(url) as response:
        raw = response.read().decode("utf-8")

    data = json.loads(raw)
    observations = data.get("observations", [])

    valid = [o for o in observations if o.get("value") not in (None, ".", "")]
    if not valid:
        raise RuntimeError(f"No valid observations for {series_id}")

    latest = valid[0]
    previous = valid[1] if len(valid) > 1 else None

    latest_value = float(latest["value"])
    previous_value = float(previous["value"]) if previous else None
    change = latest_value - previous_value if previous_value is not None else None

    return {
        "date": latest["date"],
        "value": latest_value,
        "previousDate": previous["date"] if previous else None,
        "previousValue": previous_value,
        "change": change
    }

def main():
    rows = []

    for item in SERIES:
        obs = fetch_latest_observation(item["series_id"])
        rows.append({
            "country": item["country"],
            "label": item["label"],
            "seriesId": item["series_id"],
            "sourceFrequency": item["source_note"],
            "date": obs["date"],
            "value": obs["value"],
            "previousDate": obs["previousDate"],
            "previousValue": obs["previousValue"],
            "change": obs["change"]
        })

    output = {
        "meta": {
            "title": "BondStats Daily Yields",
            "source": "FRED",
            "frequency": "Daily run",
            "lastUpdated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "note": "Some international series update monthly depending on source frequency."
        },
        "countries": rows
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("Updated data.json successfully.")
    for row in rows:
        print(f"{row['country']}: {row['value']} ({row['date']})")

if __name__ == "__main__":
    main()
