import urllib.request
import json

url = "https://raw.githubusercontent.com/g0v/twgeojson/master/json/twCounty2010.geo.json"
print("Downloading GeoJSON...")
response = urllib.request.urlopen(url)
data = json.loads(response.read())

# Simplify or rename some fields if needed
# g0v's geojson uses properties.COUNTYNAME
with open("twCounty.geojson", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)
print("Saved as twCounty.geojson")
