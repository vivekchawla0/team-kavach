import requests
import json
import pandas as pd
from datetime import datetime

print("Testing Open-Meteo Historical Archive API for Bad Münstereifel (50.5539°N, 6.7633°E)...")

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 50.5539,
    "longitude": 6.7633,
    "start_date": "2021-05-01",
    "end_date": "2021-08-31",
    "hourly": [
        "precipitation",
        "rain",
        "soil_moisture_0_to_7cm",
        "soil_moisture_7_to_28cm",
        "soil_moisture_28_to_100cm",
        "temperature_2m",
        "relative_humidity_2m",
        "surface_pressure",
        "wind_speed_10m"
    ],
    "timezone": "UTC"
}

resp = requests.get(url, params=params, timeout=20)
print(f"Status Code: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    hourly = data.get("hourly", {})
    df = pd.DataFrame(hourly)
    print(f"Successfully retrieved {len(df)} hourly records from {params['start_date']} to {params['end_date']}")
    print(f"Columns: {list(df.columns)}")
    print("\nSample records around July 13-16, 2021 (Catastrophic Ahr/Erft Flood Event):")
    df['time'] = pd.to_datetime(df['time'])
    july_flood = df[(df['time'] >= '2021-07-12') & (df['time'] <= '2021-07-16')]
    print(july_flood[['time', 'precipitation', 'rain', 'soil_moisture_0_to_7cm', 'temperature_2m']].head(20))
    print(f"\nMax precipitation rate during event: {july_flood['precipitation'].max()} mm/h")
    print(f"Total precipitation July 13-15: {july_flood['precipitation'].sum():.2f} mm")
    print(f"Soil moisture progression: min={july_flood['soil_moisture_0_to_7cm'].min():.3f}, max={july_flood['soil_moisture_0_to_7cm'].max():.3f}")
else:
    print(f"Error: {resp.text}")
