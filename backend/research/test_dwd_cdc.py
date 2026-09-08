import requests
import re
import zipfile
import io
import pandas as pd

print("Testing DWD Open Data Portal (opendata.dwd.de)...")

# Check station list
stations_url = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/precipitation/historical/stundenwerte_RR_Beschreibung_Stationen.txt"
resp = requests.get(stations_url, timeout=15)
print(f"Station list status: {resp.status_code}")

lines = resp.text.splitlines()
print(f"Total stations listed: {len(lines)}")

# Search for stations in/near Bad Münstereifel (e.g. Kall, Euskirchen, Weilerswist, Mechernich, Bad Münstereifel)
matches = []
for line in lines[2:]:
    if any(city in line for city in ["Kall", "Euskirchen", "Weilerswist", "Mechernich", "Münstereifel", "Muenstereifel", "Schleiden"]):
        matches.append(line)

print("\nRelevant nearby DWD Gauges:")
for m in matches[:10]:
    print(" ", m)

# Let's inspect station 02480 (Kall-Sistig, Eifel, near Bad Münstereifel)
# Check file existence in recent/historical
kall_url = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/precipitation/historical/stundenwerte_RR_02480_19930701_20201231_hist.zip"
# Also check recent
recent_index_url = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/precipitation/recent/"
recent_resp = requests.get(recent_index_url, timeout=15)
kall_recent = re.findall(r'stundenwerte_RR_02480_akt\.zip', recent_resp.text)
euskirchen_recent = re.findall(r'stundenwerte_RR_01300_akt\.zip', recent_resp.text)
weilerswist_recent = re.findall(r'stundenwerte_RR_06140_akt\.zip', recent_resp.text)

print(f"\nDWD Recent Files Available:")
print(f"  Station 02480 (Kall-Sistig): {kall_recent}")
print(f"  Station 01300 (Euskirchen): {euskirchen_recent}")
print(f"  Station 06140 (Weilerswist): {weilerswist_recent}")
